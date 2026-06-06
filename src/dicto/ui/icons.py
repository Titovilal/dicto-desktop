"""Icon loading from the bundled assets directory.

Centralises asset lookup so widgets never build paths by hand. Status-coloured
tray icons follow the naming ``icon[_<status>].ico`` under ``assets/icons``.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QIcon

from dicto.utils.platform import get_assets_dir

# Map AppState-ish status names to the coloured icon variant.
_STATUS_ICON = {
    "idle": "icon.ico",
    "recording": "icon_red.ico",
    "processing": "icon_amber.ico",
    "success": "icon_green.ico",
    "error": "icon_red.ico",
}


def _icons_dir() -> Path:
    return get_assets_dir() / "icons"


def app_icon() -> QIcon:
    """The default application icon."""
    return QIcon(str(_icons_dir() / "icon.ico"))


def status_icon(status: str) -> QIcon:
    """Tray icon coloured for the given app status."""
    name = _STATUS_ICON.get(status, "icon.ico")
    path = _icons_dir() / name
    if not path.exists():
        path = _icons_dir() / "icon.ico"
    return QIcon(str(path))
