"""
Clipboard manager service using pyperclip.
"""
import pyperclip


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
            print("Warning: Attempted to copy empty text to clipboard")
            return False

        try:
            pyperclip.copy(text)
            print(f"Copied to clipboard: {text[:50]}{'...' if len(text) > 50 else ''}")
            return True

        except Exception as e:
            print(f"Error copying to clipboard: {e}")
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
            print(f"Error reading from clipboard: {e}")
            return ""

    @staticmethod
    def clear():
        """Clear clipboard contents."""
        try:
            pyperclip.copy("")
            print("Clipboard cleared")

        except Exception as e:
            print(f"Error clearing clipboard: {e}")
