"""Global hotkey listener — hold and toggle modes (effects: pynput).

``HotkeyMatcher`` is the pure press/release state machine (testable without
pynput): it swallows OS auto-repeat and normalises L/R modifiers.
``HotkeyListener`` wraps it with a lazily-imported pynput backend. Callbacks fire
on pynput's daemon thread, so the app layer marshals back to the Qt thread.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable

logger = logging.getLogger(__name__)

RecordingMode = str  # "hold" | "toggle"

# Modifier name -> the set of canonical names it satisfies. A requirement of
# "ctrl" is met by ctrl / ctrl_l / ctrl_r; pressing a side key adds the generic.
_MODIFIER_ALIASES: dict[str, str] = {
    "ctrl": "ctrl",
    "ctrl_l": "ctrl",
    "ctrl_r": "ctrl",
    "control": "ctrl",
    "shift": "shift",
    "shift_l": "shift",
    "shift_r": "shift",
    "alt": "alt",
    "alt_l": "alt",
    "alt_r": "alt",
    "alt_gr": "alt",
    "cmd": "cmd",
    "cmd_l": "cmd",
    "cmd_r": "cmd",
    "win": "cmd",
}


def canonical_modifier(name: str) -> str | None:
    """Map any modifier spelling to its canonical name (or None if not one)."""
    return _MODIFIER_ALIASES.get(name.lower())


class HotkeyMatcher:
    """Pure press/release state machine — no pynput, fully unit-testable.

    Feed it canonical key names via :meth:`on_press` / :meth:`on_release`
    (modifiers as ``"ctrl"``/``"shift"``/…, the main key as e.g. ``"space"``).
    It calls ``on_start`` once when the full combo is first held and, in hold
    mode, ``on_stop`` when the main key is released. Toggle mode flips between
    start and stop on each fresh full press.
    """

    def __init__(
        self,
        modifiers: Iterable[str],
        key: str,
        *,
        mode: RecordingMode = "hold",
        on_start: Callable[[], None] | None = None,
        on_stop: Callable[[], None] | None = None,
    ) -> None:
        self.required: set[str] = {
            c for c in (canonical_modifier(m) for m in modifiers) if c is not None
        }
        self.key = key.lower()
        self.mode = mode
        self.on_start = on_start
        self.on_stop = on_stop

        self._held_modifiers: set[str] = set()
        self._key_down = False
        # True between a successful combo press and its release: blocks the OS
        # key auto-repeat from re-firing the start callback.
        self._armed = False
        # Toggle mode only: are we currently recording?
        self._recording = False

    # ── feed ────────────────────────────────────────────────────────────

    def on_press(self, name: str) -> None:
        canon = canonical_modifier(name)
        if canon is not None:
            self._held_modifiers.add(canon)
            return
        if name.lower() != self.key:
            return
        self._key_down = True
        if self._armed:
            return  # auto-repeat while held — ignore
        if not self.required.issubset(self._held_modifiers):
            return
        self._armed = True
        self._fire_start()

    def on_release(self, name: str) -> None:
        canon = canonical_modifier(name)
        if canon is not None:
            self._held_modifiers.discard(canon)
            return
        if name.lower() != self.key:
            return
        self._key_down = False
        if not self._armed:
            return
        self._armed = False
        if self.mode == "hold":
            self._fire_stop()

    def reset(self) -> None:
        """Clear all held state (e.g. after the listener restarts)."""
        self._held_modifiers.clear()
        self._key_down = False
        self._armed = False
        self._recording = False

    # ── dispatch ────────────────────────────────────────────────────────

    def _fire_start(self) -> None:
        if self.mode == "toggle":
            # In toggle mode a fresh press flips state.
            if self._recording:
                self._recording = False
                self._call(self.on_stop)
            else:
                self._recording = True
                self._call(self.on_start)
        else:  # hold
            self._call(self.on_start)

    def _fire_stop(self) -> None:
        self._call(self.on_stop)

    @staticmethod
    def _call(cb: Callable[[], None] | None) -> None:
        if cb is None:
            return
        try:
            cb()
        except Exception:  # noqa: BLE001 — a bad callback must not kill the listener
            logger.exception("hotkey callback failed")


class HotkeyListener:
    """Drives a :class:`HotkeyMatcher` from a real pynput keyboard listener.

    Effects are isolated here: the matcher above stays pure. ``start`` lazily
    imports pynput and translates its key objects into canonical names the
    matcher understands.
    """

    def __init__(
        self,
        modifiers: Iterable[str],
        key: str,
        *,
        mode: RecordingMode = "hold",
        on_start: Callable[[], None] | None = None,
        on_stop: Callable[[], None] | None = None,
    ) -> None:
        self.matcher = HotkeyMatcher(
            modifiers, key, mode=mode, on_start=on_start, on_stop=on_stop
        )
        self._listener = None
        self._kb = None

    # ── lifecycle ───────────────────────────────────────────────────────

    def start(self) -> bool:
        """Begin listening on pynput's daemon thread. False if unavailable."""
        if self._listener is not None:
            return True
        try:
            from pynput import keyboard as kb  # noqa: PLC0415 — lazy, headless-safe
        except Exception:  # noqa: BLE001
            logger.warning("pynput unavailable; global hotkey disabled", exc_info=True)
            return False
        self._kb = kb
        self.matcher.reset()
        self._listener = kb.Listener(on_press=self._on_press, on_release=self._on_release)
        self._listener.start()
        logger.info(
            "hotkey listener started: %s+%s (%s)",
            "+".join(sorted(self.matcher.required)),
            self.matcher.key,
            self.matcher.mode,
        )
        return True

    def stop(self) -> None:
        if self._listener is not None:
            try:
                self._listener.stop()
            except Exception:  # noqa: BLE001
                logger.debug("error stopping hotkey listener", exc_info=True)
            self._listener = None

    @property
    def is_running(self) -> bool:
        return self._listener is not None

    # ── pynput → canonical name translation ─────────────────────────────

    def _name_for(self, key) -> str | None:  # noqa: ANN001 — pynput key
        kb = self._kb
        # Modifier enum members carry a stable ``.name`` like "ctrl_l".
        name = getattr(key, "name", None)
        if name:
            return name
        # Character keys: KeyCode with a .char.
        char = getattr(key, "char", None)
        if char:
            return char.lower()
        # Named special keys (space, enter, …) compare against Key enum.
        try:
            for special in ("space", "enter", "tab", "esc", "backspace", "delete"):
                if key == getattr(kb.Key, special):
                    return special
        except Exception:  # noqa: BLE001
            pass
        return None

    def _on_press(self, key) -> None:  # noqa: ANN001
        name = self._name_for(key)
        if name is not None:
            self.matcher.on_press(name)

    def _on_release(self, key) -> None:  # noqa: ANN001
        name = self._name_for(key)
        if name is not None:
            self.matcher.on_release(name)
