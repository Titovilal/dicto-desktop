"""
Keyboard automation service for simulating key presses.
Centralizes all keyboard simulation (paste, enter, copy) in one place.
"""

from pynput import keyboard
from src.utils.logger import get_logger

logger = get_logger(__name__)


class KeyboardService:
    """Simulates keyboard actions like paste, enter, and copy."""

    def __init__(self):
        self._controller = keyboard.Controller()

    def paste(self):
        """Simulate Ctrl+V."""
        try:
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
            self._controller.press(keyboard.Key.enter)
            self._controller.release(keyboard.Key.enter)
        except Exception as e:
            logger.error(f"Error simulating enter: {e}")
            raise

    def copy(self):
        """Simulate Ctrl+C."""
        try:
            self._controller.press(keyboard.Key.ctrl)
            self._controller.press("c")
            self._controller.release("c")
            self._controller.release(keyboard.Key.ctrl)
        except Exception as e:
            logger.error(f"Error simulating copy: {e}")
            raise
