"""
Keyboard automation service for simulating key presses.
Centralizes all keyboard simulation (paste, enter, copy) in one place.

pynput is imported lazily so the app can start on headless/containerized
environments (e.g. Wayland dev containers) where pynput cannot acquire an
X connection. Importing it only on first key simulation keeps startup working;
the actual simulation still requires a supported display (used on Windows).
"""

from src.utils.logger import get_logger

logger = get_logger(__name__)


class KeyboardService:
    """Simulates keyboard actions like paste, enter, and copy."""

    _keyboard = None  # lazy-loaded pynput.keyboard module

    def __init__(self):
        self._controller = None  # created lazily on first use

    def _ensure_controller(self):
        """Import pynput and build the Controller on first use.

        Fails on Wayland/headless if called, which is fine: it is only reached
        when an actual key simulation is requested.
        """
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
