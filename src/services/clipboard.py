"""
Clipboard manager service.

Uses win32clipboard for direct access (supports more formats, no extra
dependency beyond pywin32 which PySide6 already pulls in).
"""

import logging
import time

import win32clipboard  # pywin32  # ty: ignore[unresolved-import]

logger = logging.getLogger(__name__)


class _ClipboardBackend:
    @staticmethod
    def read() -> str:
        try:
            win32clipboard.OpenClipboard()
            try:
                data = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
                return data or ""
            except TypeError:
                return ""
            finally:
                win32clipboard.CloseClipboard()
        except Exception as e:
            logger.error(f"Error reading clipboard: {e}")
            return ""

    @staticmethod
    def write(text: str):
        win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(text, win32clipboard.CF_UNICODETEXT)
        finally:
            win32clipboard.CloseClipboard()


class ClipboardManager:
    """Manages clipboard operations."""

    @staticmethod
    def copy(text: str) -> bool:
        """Copy text to clipboard.

        Returns True if successful, False otherwise.
        """
        if not text:
            logger.warning("Attempted to copy empty text to clipboard")
            return False

        try:
            _ClipboardBackend.write(text)
            logger.info(
                f"Copied to clipboard: {text[:50]}{'...' if len(text) > 50 else ''}"
            )
            return True

        except Exception as e:
            logger.error(f"Error copying to clipboard: {e}")
            return False

    @staticmethod
    def paste() -> str:
        """Get text from clipboard.

        Returns text from clipboard, or empty string if error.
        """
        try:
            return _ClipboardBackend.read()
        except Exception as e:
            logger.error(f"Error reading from clipboard: {e}")
            return ""

    @staticmethod
    def clear():
        """Clear clipboard contents."""
        try:
            _ClipboardBackend.write("")
            logger.debug("Clipboard cleared")

        except Exception as e:
            logger.error(f"Error clearing clipboard: {e}")

    @staticmethod
    def wait_for_change(
        old_content: str, timeout_ms: int = 500, poll_ms: int = 20
    ) -> str:
        """Poll clipboard until content changes or timeout.

        Args:
            old_content: The clipboard content before the expected change.
            timeout_ms: Maximum time to wait in milliseconds.
            poll_ms: Polling interval in milliseconds.

        Returns:
            The new clipboard content (may equal old_content if timeout).
        """
        deadline = time.monotonic() + timeout_ms / 1000
        while time.monotonic() < deadline:
            current = ClipboardManager.paste()
            if current != old_content:
                return current
            time.sleep(poll_ms / 1000)
        # Timeout — return whatever is there now
        return ClipboardManager.paste()
