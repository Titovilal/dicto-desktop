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

# Minimal hand-written introspection XML for the portal interfaces we use.
#
# We deliberately do NOT call bus.introspect() on the portal object: the live
# portal advertises every interface it implements, and some compositors expose
# properties whose names contain a hyphen (e.g. PowerProfileMonitor's
# "power-saver-enabled"). Hyphens are illegal in D-Bus member names, so
# dbus-next raises "invalid member name: power-saver-enabled" while parsing the
# full document and the whole listener dies before the shortcut is ever bound.
# Feeding it only the interfaces we care about sidesteps that entirely.
_SHORTCUTS_XML = """<!DOCTYPE node PUBLIC "-//freedesktop//DTD D-BUS Object Introspection 1.0//EN" "http://www.freedesktop.org/standards/dbus/1.0/introspect.dtd">
<node>
  <interface name="org.freedesktop.portal.GlobalShortcuts">
    <method name="CreateSession">
      <arg type="a{sv}" name="options" direction="in"/>
      <arg type="o" name="request_handle" direction="out"/>
    </method>
    <method name="BindShortcuts">
      <arg type="o" name="session_handle" direction="in"/>
      <arg type="a(sa{sv})" name="shortcuts" direction="in"/>
      <arg type="s" name="parent_window" direction="in"/>
      <arg type="a{sv}" name="options" direction="in"/>
      <arg type="o" name="request_handle" direction="out"/>
    </method>
    <method name="ListShortcuts">
      <arg type="o" name="session_handle" direction="in"/>
      <arg type="a{sv}" name="options" direction="in"/>
      <arg type="o" name="request_handle" direction="out"/>
    </method>
    <signal name="Activated">
      <arg type="o" name="session_handle"/>
      <arg type="s" name="shortcut_id"/>
      <arg type="t" name="timestamp"/>
      <arg type="a{sv}" name="options"/>
    </signal>
    <signal name="Deactivated">
      <arg type="o" name="session_handle"/>
      <arg type="s" name="shortcut_id"/>
      <arg type="t" name="timestamp"/>
      <arg type="a{sv}" name="options"/>
    </signal>
  </interface>
</node>"""

_REQUEST_XML = """<!DOCTYPE node PUBLIC "-//freedesktop//DTD D-BUS Object Introspection 1.0//EN" "http://www.freedesktop.org/standards/dbus/1.0/introspect.dtd">
<node>
  <interface name="org.freedesktop.portal.Request">
    <method name="Close"/>
    <signal name="Response">
      <arg type="u" name="response"/>
      <arg type="a{sv}" name="results"/>
    </signal>
  </interface>
</node>"""


class WaylandHotkeyListener:
    """Listens for global hotkey events on Wayland via the XDG GlobalShortcuts portal."""

    def __init__(
        self,
        shortcut_id: str,
        description: str,
        preferred_trigger: str,
        on_toggle: Callable | None = None,
        mode: str = "hold",
    ):
        """
        Args:
            shortcut_id: Unique ID for this shortcut (e.g. 'dicto-record').
            description: Human-readable description shown in the compositor dialog.
            preferred_trigger: Suggested trigger (e.g. 'CTRL+SHIFT+space'). The
                compositor may change it.
            on_toggle: Callback fired once per portal activation (tap). The
                caller decides whether that means start or stop.
            mode: kept for API compatibility; the portal only supports toggle.
        """
        self.shortcut_id = shortcut_id
        self.description = description
        self.preferred_trigger = preferred_trigger
        self.on_toggle_callback = on_toggle
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
            f"(preferred: {self.preferred_trigger}) — toggle mode "
            "(press to start, press again to stop; hold-to-record is not "
            "supported by the Wayland portal)"
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

        # Use our trimmed introspection XML instead of bus.introspect() — see
        # the comment on _SHORTCUTS_XML for why introspecting the live portal
        # object blows up on some compositors.
        proxy = bus.get_proxy_object(PORTAL_BUS, PORTAL_PATH, _SHORTCUTS_XML)
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

        # 2. Bind shortcuts. The signature is a(sa{sv}); dbus-next represents a
        # D-Bus STRUCT as a Python list (NOT a tuple), so each shortcut entry
        # must be [id, {options}], not (id, {options}).
        shortcut_spec = [
            [
                self.shortcut_id,
                {
                    "description": Variant("s", self.description),
                    "preferred-trigger": Variant("s", self.preferred_trigger),
                },
            ]
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

        # The request path is returned by the portal call. Use our trimmed XML
        # rather than introspecting it live (same reason as _SHORTCUTS_XML).
        request_proxy = bus.get_proxy_object(PORTAL_BUS, request_path, _REQUEST_XML)
        request = request_proxy.get_interface(REQUEST_IFACE)

        def on_response(response_code, results):
            if not future.done():
                if response_code == 0:
                    # Success — extract session_handle if present
                    handle = results.get("session_handle")
                    if handle:
                        future.set_result(
                            handle.value if isinstance(handle, Variant) else handle
                        )
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
    #
    # Wayland note: the XDG GlobalShortcuts portal fires Activated on key press
    # but Mutter (GNOME) does NOT reliably fire Deactivated on key release, so
    # true press-and-hold ("push to talk") is impossible here — see
    # https://docs.murmure.app/configure-shortcuts-on-linux/ for the same
    # limitation in another dictation app. We therefore expose a TOGGLE: each
    # Activated flips between start and stop.
    #
    # Crucially, we do NOT keep a local toggle flag here. GNOME emits BOTH
    # Activated and Deactivated for a single tap, while KDE behaves differently,
    # so any flag kept in the listener inevitably desyncs from the controller's
    # actual recording state (symptom: "Recording already in progress" after a
    # couple of taps). Instead we fire ONE neutral callback per Activated and
    # let the controller — the single source of truth — decide start vs stop
    # from its own state. Deactivated is ignored for the toggle: it's
    # unreliable across compositors and would double-fire on GNOME.
    #
    # X11 / Windows / macOS keep real hold behaviour via the pynput
    # HotkeyListener.

    def _on_activated(self, session_handle, shortcut_id, timestamp, options):
        if shortcut_id != self.shortcut_id:
            return
        logger.debug(f"Shortcut activated (toggle): {shortcut_id}")
        # on_toggle is the controller's toggle entry point, which starts or
        # stops recording based on the controller's current state.
        if self.on_toggle_callback:
            self.on_toggle_callback()

    def _on_deactivated(self, session_handle, shortcut_id, timestamp, options):
        # Deliberately a no-op: see the note above. Some compositors fire this
        # on every tap; acting on it would double-toggle and desync state.
        if shortcut_id != self.shortcut_id:
            return
        logger.debug(f"Shortcut deactivated (ignored): {shortcut_id}")


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
