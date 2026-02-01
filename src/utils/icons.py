"""
Icon utilities for Dicto application.
"""

import sys
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def get_icon_path(icon_name: str = "icon") -> Path | None:
    """
    Get the path to an icon file.

    Works both in development and when packaged with PyInstaller.
    Prefers .ico on Windows, .png on other platforms.

    Args:
        icon_name: Base name of the icon (without extension)

    Returns:
        Path to the icon file, or None if not found
    """
    # Determine base path (PyInstaller sets _MEIPASS when bundled)
    if getattr(sys, "frozen", False):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).parent.parent.parent

    icons_dir = base_path / "assets" / "icons"

    # Prefer .ico on Windows, .png elsewhere
    if sys.platform == "win32":
        extensions = [".ico", ".png"]
    else:
        extensions = [".png", ".ico"]

    for ext in extensions:
        icon_path = icons_dir / f"{icon_name}{ext}"
        if icon_path.exists():
            logger.debug(f"Icon found: {icon_path}")
            return icon_path

    logger.warning(f"Icon not found: {icon_name} in {icons_dir}")
    return None
