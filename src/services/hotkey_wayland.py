"""
Global hotkey listener for Wayland using org.freedesktop.portal.GlobalShortcuts via D-Bus.

Requires the 'dbus-next' package: pip install dbus-next
"""

from __future__ import annotations

import asyncio
import logging
import threading
from typing import Callable, List

logger = logging.getLogger(__name__)

PORTAL_BUS = "org.freedesktop.portal.Desktop"
PORTAL_PATH = "/org/freedesktop/portal/desktop"
SHORTCUTS_IFACE = "org.freedesktop.portal.GlobalShortcuts"
REQUEST_IFACE = "org.freedesktop.portal.Request"


class WaylandHotkeyListener:
    """Listens for global hotkey events on Wayland via the XDG GlobalShortcuts portal."""

    def __init__(
        self,
        shortcut_id: str,
        description: str,
        preferred_trigger: str,
        on_press: Callable | None = None,
        on_release: Callable | None = None,
        mode: str = "hold",
    ):
        """
        Args:
            shortcut_id: Unique ID for this shortcut (e.g. 'dicto-record').
            description: Human-readable description shown in the compositor dialog.
            preferred_trigger: Suggested trigger (e.g. 'CTRL+SHIFT+space'). The
                compositor may change it.
            on_press: Callback fired when the shortcut is activated.
            on_release: Callback fired when the shortcut is deactivated (hold mode).
            mode: 'hold' for press+release, 'press' for single activation.
        """
        self.shortcut_id = shortcut_id
        self.description = description
        self.preferred_trigger = preferred_trigger
        self.on_press_callback = on_press
        self.on_release_callback = on_release
        self.mode = mode

        self._thread: threading.Thread | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._running = False
        self._session_handle: str | None = None

    # ── Public API (matches HotkeyListener interface) ────────

    def start(self):
        """Start the D-Bus listener in a background thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info(
            f"Wayland hotkey listener started: {self.shortcut_id} "
            f"(preferred: {self.preferred_trigger})"
        )

    def stop(self):
        """Stop the D-Bus listener."""
        self._running = False
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None
        self._session_handle = None
        logger.info(f"Wayland hotkey listener stopped: {self.shortcut_id}")

    def is_running(self) -> bool:
        return self._running

    # ── Event loop ───────────────────────────────────────────

    def _run_loop(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._setup_and_listen())
        except Exception as e:
            logger.error(f"Wayland hotkey listener error: {e}")
        finally:
            self._loop.close()
            self._loop = None
            self._running = False

    async def _setup_and_listen(self):
        from dbus_next.aio import MessageBus
        from dbus_next import Variant

        bus = await MessageBus().connect()

        introspection = await bus.introspect(PORTAL_BUS, PORTAL_PATH)
        proxy = bus.get_proxy_object(PORTAL_BUS, PORTAL_PATH, introspection)
        shortcuts = proxy.get_interface(SHORTCUTS_IFACE)

        # 1. Create a session
        token = f"dicto_{self.shortcut_id.replace('-', '_')}"
        session_result = await shortcuts.call_create_session(
            {
                "handle_token": Variant("s", token),
                "session_handle_token": Variant("s", token),
            }
        )
        # The portal returns (response_code, {session_handle: ...})
        # But with dbus-next we get the Request path and need to wait for Response
        session_handle = await self._wait_for_response(bus, session_result)
        if session_handle is None:
            logger.error("Failed to create GlobalShortcuts session")
            return
        self._session_handle = session_handle

        # 2. Bind shortcuts
        shortcut_spec = [
            (
                self.shortcut_id,
                {
                    "description": Variant("s", self.description),
                    "preferred-trigger": Variant("s", self.preferred_trigger),
                },
            )
        ]
        bind_result = await shortcuts.call_bind_shortcuts(
            session_handle,
            shortcut_spec,
            "",  # parent_window
            {"handle_token": Variant("s", f"{token}_bind")},
        )
        bind_response = await self._wait_for_response(bus, bind_result)
        if bind_response is None:
            logger.warning("User denied shortcut binding or portal error")
            return

        logger.info(f"Shortcut bound: {self.shortcut_id}")

        # 3. Listen for Activated / Deactivated signals
        shortcuts.on_activated(self._on_activated)
        shortcuts.on_deactivated(self._on_deactivated)

        # Keep running until stopped
        while self._running:
            await asyncio.sleep(0.5)

        await bus.disconnect()

    async def _wait_for_response(self, bus, request_path: str) -> str | None:
        """Wait for a portal Request.Response signal and return the session handle."""
        from dbus_next import Variant

        future: asyncio.Future = self._loop.create_future()

        # The request path is returned by the portal call
        introspection = await bus.introspect(PORTAL_BUS, request_path)
        request_proxy = bus.get_proxy_object(
            PORTAL_BUS, request_path, introspection
        )
        request = request_proxy.get_interface(REQUEST_IFACE)

        def on_response(response_code, results):
            if not future.done():
                if response_code == 0:
                    # Success — extract session_handle if present
                    handle = results.get("session_handle")
                    if handle:
                        future.set_result(handle.value if isinstance(handle, Variant) else handle)
                    else:
                        future.set_result("ok")
                else:
                    future.set_result(None)

        request.on_response(on_response)

        try:
            return await asyncio.wait_for(future, timeout=30)
        except asyncio.TimeoutError:
            logger.error("Portal response timed out")
            return None

    # ── Signal handlers ──────────────────────────────────────

    def _on_activated(self, session_handle, shortcut_id, timestamp, options):
        if shortcut_id != self.shortcut_id:
            return
        logger.debug(f"Shortcut activated: {shortcut_id}")
        if self.on_press_callback:
            self.on_press_callback()

    def _on_deactivated(self, session_handle, shortcut_id, timestamp, options):
        if shortcut_id != self.shortcut_id:
            return
        logger.debug(f"Shortcut deactivated: {shortcut_id}")
        if self.mode == "hold" and self.on_release_callback:
            self.on_release_callback()


def format_portal_trigger(modifiers: List[str], key: str) -> str:
    """Convert our config format (modifiers list + key) to portal trigger string.

    Example: ['ctrl', 'shift'], 'space' -> 'CTRL+SHIFT+space'
    """
    parts = [m.upper() for m in modifiers]
    parts.append(key.lower())
    return "+".join(parts)


def is_wayland() -> bool:
    """Check if running under a Wayland session."""
    import os

    return os.environ.get("XDG_SESSION_TYPE") == "wayland"
