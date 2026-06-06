"""
Keyboard automation (paste, enter, copy).

pynput is imported lazily so startup works on headless/Wayland environments.
On Wayland pynput can't inject events into other windows, so we fall back to
ydotool (needs ydotoold running) or xdotool.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys

from src.utils.logger import get_logger

logger = get_logger(__name__)


def _is_wayland() -> bool:
    """True under a Wayland session. Checked lazily, not at import time."""
    if sys.platform != "linux":
        return False
    return bool(os.environ.get("WAYLAND_DISPLAY")) or (
        os.environ.get("XDG_SESSION_TYPE") == "wayland"
    )


# xdotool takes keysym names; ydotool takes Linux keycodes with press/release
# state (29=Ctrl, 46=C, 47=V, 28=Enter). Each needs its own encoding.
_XDOTOOL_KEYS = {"paste": "ctrl+v", "copy": "ctrl+c", "enter": "Return"}
_YDOTOOL_KEYS = {
    "paste": ["29:1", "47:1", "47:0", "29:0"],
    "copy": ["29:1", "46:1", "46:0", "29:0"],
    "enter": ["28:1", "28:0"],
}


def _wayland_key(action: str) -> bool:
    """Run a paste/copy/enter via ydotool or xdotool. False if none worked."""
    ydotool = shutil.which("ydotool")
    if ydotool:
        result = subprocess.run(
            [ydotool, "key", *_YDOTOOL_KEYS[action]], capture_output=True
        )
        if result.returncode == 0:
            return True
        logger.warning(f"ydotool failed for {action}: {result.stderr.decode().strip()}")

    xdotool = shutil.which("xdotool")
    if xdotool:
        result = subprocess.run(
            [xdotool, "key", _XDOTOOL_KEYS[action]], capture_output=True
        )
        if result.returncode == 0:
            return True
        logger.warning(f"xdotool failed for {action}: {result.stderr.decode().strip()}")

    return False


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
        if _is_wayland() and _wayland_key("paste"):
            return
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
        if _is_wayland() and _wayland_key("enter"):
            return
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
        if _is_wayland() and _wayland_key("copy"):
            return
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
