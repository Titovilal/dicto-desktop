"""Injector — drop a transcript at the cursor of the focused app.

This is the default delivery path: the user dictates into whatever window has
focus and the text appears there, optionally followed by Enter (handy for chat
boxes and search bars). It works the portable way — copy to the clipboard, then
synthesise **Ctrl+V** — rather than typing character by character, which is slow
and mangles non-ASCII.

``pynput`` is imported lazily so importing this module never requires a display
or an input backend; ``available()`` reports whether real injection is possible
here, which ``core/result_router`` uses to decide between cursor and clipboard.
If injection is requested but unavailable, the caller falls back to the
clipboard — the text is already there, so nothing is lost.
"""

from __future__ import annotations

import logging
import time

from dicto.services.clipboard import Clipboard

logger = logging.getLogger(__name__)


class Injector:
    """Pastes text at the cursor via the clipboard + Ctrl+V, with auto-enter.

    The keyboard controller (pynput) is created lazily on first use. A
    ``Clipboard`` is injected (defaults to a fresh one) so the paste and the
    fallback share one backend.
    """

    def __init__(self, clipboard: Clipboard | None = None) -> None:
        self._clipboard = clipboard or Clipboard()
        self._controller = None  # pynput.keyboard.Controller, lazy
        self._keyboard = None  # pynput.keyboard module, lazy
        self._unavailable = False  # latched once pynput import fails

    # ── capability ──────────────────────────────────────────────────────

    def available(self) -> bool:
        """True if keyboard injection is usable here (pynput importable)."""
        if self._unavailable:
            return False
        if self._controller is not None:
            return True
        return self._ensure_controller()

    def _ensure_controller(self) -> bool:
        if self._controller is not None:
            return True
        if self._unavailable:
            return False
        try:
            from pynput import keyboard as kb

            self._keyboard = kb
            self._controller = kb.Controller()
            return True
        except Exception:  # noqa: BLE001 — no input backend (headless / unsupported)
            logger.warning("keyboard injection unavailable", exc_info=True)
            self._unavailable = True
            return False

    # ── actions ─────────────────────────────────────────────────────────

    def inject(self, text: str, *, auto_enter: bool = False) -> bool:
        """Place ``text`` at the cursor. Returns True if the paste was sent.

        Copies to the clipboard first (so the text survives even if the paste
        keystroke is dropped), then sends Ctrl+V and, if asked, Enter. Returns
        False without raising when injection isn't available — the caller treats
        that as "fall back to clipboard".
        """
        if not text:
            return False
        # Always stage on the clipboard; this is also the fallback content.
        self._clipboard.copy(text)
        if not self._ensure_controller():
            return False
        try:
            self._paste()
            if auto_enter:
                # A beat so the target app processes the paste before Enter.
                time.sleep(0.05)
                self._enter()
            return True
        except Exception:  # noqa: BLE001 — surfaced as a clipboard fallback by caller
            logger.error("injection failed; text remains on clipboard", exc_info=True)
            return False

    def _paste(self) -> None:
        kb = self._keyboard
        ctrl = self._controller
        assert kb is not None and ctrl is not None
        ctrl.press(kb.Key.ctrl)
        ctrl.press("v")
        ctrl.release("v")
        ctrl.release(kb.Key.ctrl)

    def _enter(self) -> None:
        kb = self._keyboard
        ctrl = self._controller
        assert kb is not None and ctrl is not None
        ctrl.press(kb.Key.enter)
        ctrl.release(kb.Key.enter)
