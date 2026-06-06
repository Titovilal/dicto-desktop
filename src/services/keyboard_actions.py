"""
Keyboard automation (paste, enter, copy).

pynput is imported lazily so startup works in headless environments.
"""

from __future__ import annotations

from src.utils.logger import get_logger

logger = get_logger(__name__)


class KeyboardService:
    """Simulates keyboard actions like paste, enter, and copy."""

    _keyboard = None  # lazy-loaded pynput.keyboard module

    def __init__(self):
        self._controller = None  # created lazily on first use

    def _ensure_controller(self):
        if self._controller is not None:
            return
        from pynput import keyboard as _kb

        KeyboardService._keyboard = _kb
        self._controller = _kb.Controller()

    def paste(self):
        """Simulate Ctrl+V."""
        try:
            self._ensure_controller()
            keyboard = self._keyboard
            self._controller.press(keyboard.Key.ctrl)
            self._controller.press("v")
            self._controller.release("v")
            self._controller.release(keyboard.Key.ctrl)
        except Exception as e:
            logger.error(f"Error simulating paste: {e}")
            raise

    def enter(self):
        """Simulate Enter key press."""
        try:
            self._ensure_controller()
            keyboard = self._keyboard
            self._controller.press(keyboard.Key.enter)
            self._controller.release(keyboard.Key.enter)
        except Exception as e:
            logger.error(f"Error simulating enter: {e}")
            raise

    def copy(self):
        """Simulate Ctrl+C."""
        try:
            self._ensure_controller()
            keyboard = self._keyboard
            self._controller.press(keyboard.Key.ctrl)
            self._controller.press("c")
            self._controller.release("c")
            self._controller.release(keyboard.Key.ctrl)
        except Exception as e:
            logger.error(f"Error simulating copy: {e}")
            raise
