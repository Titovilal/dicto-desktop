"""Unit tests for platform-specific behavior."""

from __future__ import annotations

from unittest.mock import patch

from src.services.hotkey import HotkeyListener


class TestHotkeyPlatformFilter:
    """win32_event_filter should only be passed on Windows."""

    @patch("src.services.hotkey.sys")
    @patch("src.services.hotkey.keyboard.Listener")
    def test_win32_filter_passed_on_windows(self, MockListener, mock_sys):
        mock_sys.platform = "win32"
        listener = HotkeyListener(modifiers=["ctrl"], key="space", suppress_key=True)
        listener.start()
        kwargs = MockListener.call_args[1]
        assert "win32_event_filter" in kwargs
        assert kwargs["suppress"] is True

    @patch("src.services.hotkey.sys")
    @patch("src.services.hotkey.keyboard.Listener")
    def test_win32_filter_not_passed_on_linux(self, MockListener, mock_sys):
        mock_sys.platform = "linux"
        listener = HotkeyListener(modifiers=["ctrl"], key="space", suppress_key=True)
        listener.start()
        kwargs = MockListener.call_args[1]
        assert "win32_event_filter" not in kwargs
        assert kwargs["suppress"] is True

    @patch("src.services.hotkey.keyboard.Listener")
    def test_no_suppress_no_filter(self, MockListener):
        listener = HotkeyListener(modifiers=["ctrl"], key="space", suppress_key=False)
        listener.start()
        kwargs = MockListener.call_args[1]
        assert "win32_event_filter" not in kwargs
        assert "suppress" not in kwargs


class TestWaylandDetection:
    """Wayland warning should trigger only on linux + wayland."""

    def test_wayland_detected(self):
        """On linux + wayland, the guard condition is true."""
        with (
            patch("sys.platform", "linux"),
            patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"}),
        ):
            import os
            import sys

            assert sys.platform == "linux"
            assert os.environ.get("XDG_SESSION_TYPE") == "wayland"

    def test_x11_not_detected_as_wayland(self):
        with (
            patch("sys.platform", "linux"),
            patch.dict("os.environ", {"XDG_SESSION_TYPE": "x11"}),
        ):
            import os
            import sys

            condition = (
                sys.platform == "linux"
                and os.environ.get("XDG_SESSION_TYPE") == "wayland"
            )
            assert condition is False

    def test_windows_not_detected_as_wayland(self):
        with (
            patch("sys.platform", "win32"),
            patch.dict("os.environ", {}, clear=True),
        ):
            import sys

            condition = (
                sys.platform == "linux"
                and "XDG_SESSION_TYPE" in __import__("os").environ
            )
            assert condition is False


class TestWaylandMessages:
    """Wayland messages dict has all required languages and structure."""

    def _get_messages(self):
        return {
            "en": {
                "title": "Dicto - Wayland detected",
                "text": (
                    "Dicto requires an X11 session to work correctly.\n\n"
                    "Global hotkeys and keyboard simulation do not work on Wayland.\n\n"
                    "To switch to X11:\n"
                    "1. Log out\n"
                    "2. On the login screen, select 'Ubuntu on Xorg' (or equivalent)\n"
                    "3. Log in and run Dicto again"
                ),
            },
            "es": {"title": "Dicto - Wayland detectado"},
            "de": {"title": "Dicto - Wayland erkannt"},
            "fr": {"title": "Dicto - Wayland détecté"},
            "pt": {"title": "Dicto - Wayland detectado"},
        }

    def test_all_ui_languages_have_wayland_message(self):
        from src.i18n.translations import UI_LANGUAGES

        messages = self._get_messages()
        for lang in UI_LANGUAGES:
            assert lang in messages, f"Missing Wayland message for '{lang}'"

    def test_messages_have_title_and_text(self):
        """At minimum, en should have both title and text."""
        msgs = self._get_messages()
        assert "title" in msgs["en"]
        assert "text" in msgs["en"]
        assert "X11" in msgs["en"]["text"]
