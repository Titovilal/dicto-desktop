"""Unit tests for ClipboardManager."""

from __future__ import annotations

from unittest.mock import patch

from src.services.clipboard import ClipboardManager


class TestCopy:
    @patch("src.services.clipboard._ClipboardBackend.write")
    def test_copy_text(self, mock_write):
        assert ClipboardManager.copy("hello") is True
        mock_write.assert_called_once_with("hello")

    def test_copy_empty_returns_false(self):
        assert ClipboardManager.copy("") is False

    @patch(
        "src.services.clipboard._ClipboardBackend.write", side_effect=Exception("fail")
    )
    def test_copy_exception_returns_false(self, mock_write):
        assert ClipboardManager.copy("hello") is False


class TestPaste:
    @patch("src.services.clipboard._ClipboardBackend.read", return_value="world")
    def test_paste_text(self, mock_read):
        assert ClipboardManager.paste() == "world"

    @patch("src.services.clipboard._ClipboardBackend.read", return_value="")
    def test_paste_empty_returns_empty(self, mock_read):
        assert ClipboardManager.paste() == ""

    @patch(
        "src.services.clipboard._ClipboardBackend.read", side_effect=Exception("fail")
    )
    def test_paste_exception_returns_empty(self, mock_read):
        assert ClipboardManager.paste() == ""


class TestClear:
    @patch("src.services.clipboard._ClipboardBackend.write")
    def test_clear(self, mock_write):
        ClipboardManager.clear()
        mock_write.assert_called_once_with("")


class TestWaitForChange:
    @patch("src.services.clipboard._ClipboardBackend.read")
    def test_returns_new_content(self, mock_read):
        mock_read.side_effect = ["old", "old", "new"]
        result = ClipboardManager.wait_for_change("old", timeout_ms=200, poll_ms=10)
        assert result == "new"

    @patch("src.services.clipboard._ClipboardBackend.read", return_value="same")
    def test_returns_on_timeout(self, mock_read):
        result = ClipboardManager.wait_for_change("same", timeout_ms=50, poll_ms=10)
        assert result == "same"
