"""
Global hotkey listener service using pynput.
"""

from pynput import keyboard
from typing import Callable, List, Set


class HotkeyListener:
    """Listens for global hotkey press and release events."""

    # Map config modifier names to pynput Key objects
    MODIFIER_MAP = {
        "ctrl": keyboard.Key.ctrl,
        "ctrl_l": keyboard.Key.ctrl_l,
        "ctrl_r": keyboard.Key.ctrl_r,
        "shift": keyboard.Key.shift,
        "shift_l": keyboard.Key.shift_l,
        "shift_r": keyboard.Key.shift_r,
        "alt": keyboard.Key.alt,
        "alt_l": keyboard.Key.alt_l,
        "alt_r": keyboard.Key.alt_r,
        "cmd": keyboard.Key.cmd,
        "cmd_l": keyboard.Key.cmd_l,
        "cmd_r": keyboard.Key.cmd_r,
    }

    def __init__(
        self,
        modifiers: List[str],
        key: str,
        on_press: Callable | None = None,
        on_release: Callable | None = None,
    ):
        """
        Initialize hotkey listener.

        Args:
            modifiers: List of modifier keys (e.g., ['ctrl', 'shift'])
            key: The main key (e.g., 'space')
            on_press: Callback function when hotkey is pressed
            on_release: Callback function when hotkey is released
        """
        self.modifiers = self._parse_modifiers(modifiers)
        self.key = self._parse_key(key)
        self.on_press_callback = on_press
        self.on_release_callback = on_release

        self.current_modifiers: Set = set()
        self.hotkey_pressed = False
        self.listener = None

    def _parse_modifiers(self, modifiers: List[str]) -> Set:
        """Convert modifier strings to pynput Key objects."""
        parsed = set()
        for mod in modifiers:
            mod_lower = mod.lower()
            if mod_lower in self.MODIFIER_MAP:
                parsed.add(self.MODIFIER_MAP[mod_lower])
            # Also add the generic version if specific L/R is given
            if mod_lower in ["ctrl_l", "ctrl_r"]:
                parsed.add(keyboard.Key.ctrl)
            elif mod_lower in ["shift_l", "shift_r"]:
                parsed.add(keyboard.Key.shift)
            elif mod_lower in ["alt_l", "alt_r"]:
                parsed.add(keyboard.Key.alt)
        return parsed

    def _parse_key(self, key: str):
        """Convert key string to pynput Key object or character."""
        key_lower = key.lower()

        # Check if it's a special key
        special_keys = {
            "space": keyboard.Key.space,
            "enter": keyboard.Key.enter,
            "tab": keyboard.Key.tab,
            "esc": keyboard.Key.esc,
            "backspace": keyboard.Key.backspace,
            "delete": keyboard.Key.delete,
            "up": keyboard.Key.up,
            "down": keyboard.Key.down,
            "left": keyboard.Key.left,
            "right": keyboard.Key.right,
        }

        if key_lower in special_keys:
            return special_keys[key_lower]

        # It's a regular character key
        return keyboard.KeyCode.from_char(key_lower)

    def _on_press(self, key):
        """Internal callback for key press events."""
        # Track modifiers
        if key in [
            keyboard.Key.ctrl,
            keyboard.Key.ctrl_l,
            keyboard.Key.ctrl_r,
            keyboard.Key.shift,
            keyboard.Key.shift_l,
            keyboard.Key.shift_r,
            keyboard.Key.alt,
            keyboard.Key.alt_l,
            keyboard.Key.alt_r,
            keyboard.Key.cmd,
            keyboard.Key.cmd_l,
            keyboard.Key.cmd_r,
        ]:
            # Normalize L/R modifiers to generic
            if key in [keyboard.Key.ctrl_l, keyboard.Key.ctrl_r]:
                self.current_modifiers.add(keyboard.Key.ctrl)
            elif key in [keyboard.Key.shift_l, keyboard.Key.shift_r]:
                self.current_modifiers.add(keyboard.Key.shift)
            elif key in [keyboard.Key.alt_l, keyboard.Key.alt_r]:
                self.current_modifiers.add(keyboard.Key.alt)
            elif key in [keyboard.Key.cmd_l, keyboard.Key.cmd_r]:
                self.current_modifiers.add(keyboard.Key.cmd)
            else:
                self.current_modifiers.add(key)

        # Check if hotkey is pressed
        if not self.hotkey_pressed:
            if self._is_hotkey_combination(key):
                self.hotkey_pressed = True
                if self.on_press_callback:
                    self.on_press_callback()

    def _on_release(self, key):
        """Internal callback for key release events."""
        # Track modifier release
        if key in [keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r]:
            self.current_modifiers.discard(keyboard.Key.ctrl)
        elif key in [keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r]:
            self.current_modifiers.discard(keyboard.Key.shift)
        elif key in [keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r]:
            self.current_modifiers.discard(keyboard.Key.alt)
        elif key in [keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r]:
            self.current_modifiers.discard(keyboard.Key.cmd)

        # Check if hotkey is released
        if self.hotkey_pressed and key == self.key:
            self.hotkey_pressed = False
            if self.on_release_callback:
                self.on_release_callback()

    def _is_hotkey_combination(self, key) -> bool:
        """Check if current key combination matches the configured hotkey."""
        # Check if the main key matches
        if key != self.key:
            return False

        # Check if all required modifiers are pressed
        return self.modifiers.issubset(self.current_modifiers)

    def start(self):
        """Start listening for hotkeys in a separate thread."""
        if self.listener is not None:
            return  # Already running

        self.listener = keyboard.Listener(
            on_press=self._on_press, on_release=self._on_release
        )

        # keyboard.Listener is already a threading.Thread subclass
        # Just call start() directly - it runs in its own daemon thread
        self.listener.start()
        print(
            f"Hotkey listener started: {'+'.join([str(m) for m in self.modifiers])}+{self.key}"
        )

    def stop(self):
        """Stop listening for hotkeys."""
        if self.listener is not None:
            self.listener.stop()
            self.listener = None
            print("Hotkey listener stopped")

    def is_running(self) -> bool:
        """Check if listener is currently running."""
        return self.listener is not None
