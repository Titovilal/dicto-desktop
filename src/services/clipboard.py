"""
Clipboard manager service using pyperclip.
"""

import logging
import pyperclip

logger = logging.getLogger(__name__)


class ClipboardManager:
    """Manages clipboard operations."""

    @staticmethod
    def copy(text: str) -> bool:
        """
        Copy text to clipboard.

        Args:
            text: Text to copy

        Returns:
            True if successful, False otherwise
        """
        if not text:
            logger.warning("Attempted to copy empty text to clipboard")
            return False

        try:
            pyperclip.copy(text)
            logger.info(f"Copied to clipboard: {text[:50]}{'...' if len(text) > 50 else ''}")
            return True

        except Exception as e:
            logger.error(f"Error copying to clipboard: {e}")
            return False

    @staticmethod
    def paste() -> str:
        """
        Get text from clipboard.

        Returns:
            Text from clipboard, or empty string if error
        """
        try:
            text = pyperclip.paste()
            return text or ""

        except Exception as e:
            logger.error(f"Error reading from clipboard: {e}")
            return ""

    @staticmethod
    def clear():
        """Clear clipboard contents."""
        try:
            pyperclip.copy("")
            logger.debug("Clipboard cleared")

        except Exception as e:
            logger.error(f"Error clearing clipboard: {e}")
