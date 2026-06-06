"""Unit tests for platform-specific behavior."""

from __future__ import annotations

from unittest.mock import patch

from src.services.hotkey import HotkeyListener

from tests.conftest import requires_pynput


@requires_pynput
class TestHotkeyPlatformFilter:
    """win32_event_filter should be passed when suppression is enabled."""

    def test_win32_filter_passed_when_suppressing(self):
        from pynput import keyboard

        with patch.object(keyboard, "Listener") as MockListener:
            listener = HotkeyListener(
                modifiers=["ctrl"], key="space", suppress_key=True
            )
            listener.start()
            kwargs = MockListener.call_args[1]
            assert "win32_event_filter" in kwargs
            assert kwargs["suppress"] is True

    def test_no_suppress_no_filter(self):
        from pynput import keyboard

        with patch.object(keyboard, "Listener") as MockListener:
            listener = HotkeyListener(
                modifiers=["ctrl"], key="space", suppress_key=False
            )
            listener.start()
            kwargs = MockListener.call_args[1]
            assert "win32_event_filter" not in kwargs
            assert "suppress" not in kwargs
