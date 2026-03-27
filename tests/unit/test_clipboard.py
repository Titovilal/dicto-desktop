"""Unit tests for ClipboardManager."""
from __future__ import annotations

from unittest.mock import patch

from src.services.clipboard import ClipboardManager


class TestCopy:

    @patch("src.services.clipboard.pyperclip.copy")
    def test_copy_text(self, mock_copy):
        assert ClipboardManager.copy("hello") is True
        mock_copy.assert_called_once_with("hello")

    def test_copy_empty_returns_false(self):
        assert ClipboardManager.copy("") is False

    @patch("src.services.clipboard.pyperclip.copy", side_effect=Exception("fail"))
    def test_copy_exception_returns_false(self, mock_copy):
        assert ClipboardManager.copy("hello") is False


class TestPaste:

    @patch("src.services.clipboard.pyperclip.paste", return_value="world")
    def test_paste_text(self, mock_paste):
        assert ClipboardManager.paste() == "world"

    @patch("src.services.clipboard.pyperclip.paste", return_value=None)
    def test_paste_none_returns_empty(self, mock_paste):
        assert ClipboardManager.paste() == ""

    @patch("src.services.clipboard.pyperclip.paste", side_effect=Exception("fail"))
    def test_paste_exception_returns_empty(self, mock_paste):
        assert ClipboardManager.paste() == ""


class TestClear:

    @patch("src.services.clipboard.pyperclip.copy")
    def test_clear(self, mock_copy):
        ClipboardManager.clear()
        mock_copy.assert_called_once_with("")
