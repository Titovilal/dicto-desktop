"""Unit tests for HotkeyListener key parsing and combination matching."""
from __future__ import annotations

from unittest.mock import patch

from src.services.hotkey import HotkeyListener


class TestKeyParsing:

    def test_parse_special_key_space(self):
        listener = HotkeyListener(modifiers=["ctrl"], key="space")
        from pynput import keyboard
        assert listener.key == keyboard.Key.space

    def test_parse_special_key_enter(self):
        listener = HotkeyListener(modifiers=["ctrl"], key="enter")
        from pynput import keyboard
        assert listener.key == keyboard.Key.enter

    def test_parse_regular_char(self):
        listener = HotkeyListener(modifiers=["ctrl"], key="a")
        from pynput import keyboard
        assert listener.key == keyboard.KeyCode.from_char("a")


class TestModifierParsing:

    def test_parse_generic_modifiers(self):
        from pynput import keyboard
        listener = HotkeyListener(modifiers=["ctrl", "shift"], key="space")
        assert keyboard.Key.ctrl in listener.modifiers
        assert keyboard.Key.shift in listener.modifiers

    def test_parse_specific_lr_adds_generic(self):
        from pynput import keyboard
        listener = HotkeyListener(modifiers=["ctrl_l"], key="space")
        assert keyboard.Key.ctrl in listener.modifiers

    def test_parse_alt(self):
        from pynput import keyboard
        listener = HotkeyListener(modifiers=["alt"], key="space")
        assert keyboard.Key.alt in listener.modifiers


class TestModes:

    def test_hold_mode_default(self):
        listener = HotkeyListener(modifiers=["ctrl"], key="space")
        assert listener.mode == "hold"

    def test_press_mode(self):
        listener = HotkeyListener(modifiers=["ctrl"], key="space", mode="press")
        assert listener.mode == "press"


class TestStartStop:

    @patch("src.services.hotkey.keyboard.Listener")
    def test_start_creates_listener(self, MockListener):
        listener = HotkeyListener(modifiers=["ctrl"], key="space")
        listener.start()
        assert listener.listener is not None
        MockListener.return_value.start.assert_called_once()

    @patch("src.services.hotkey.keyboard.Listener")
    def test_start_twice_is_noop(self, MockListener):
        listener = HotkeyListener(modifiers=["ctrl"], key="space")
        listener.start()
        listener.start()
        assert MockListener.return_value.start.call_count == 1

    @patch("src.services.hotkey.keyboard.Listener")
    def test_stop(self, MockListener):
        listener = HotkeyListener(modifiers=["ctrl"], key="space")
        listener.start()
        listener.stop()
        MockListener.return_value.stop.assert_called_once()
        assert listener.listener is None

    def test_is_running(self):
        listener = HotkeyListener(modifiers=["ctrl"], key="space")
        assert listener.is_running() is False
