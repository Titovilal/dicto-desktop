"""Icon loading from the bundled assets directory.

Tray icons: ``icon[_<status>].ico`` under ``assets/icons``. Action glyphs:
single-path SVGs under ``assets/icons/svg`` using ``currentColor``; ``svg_icon``
recolours them to a theme token and caches the result.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import QSize
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

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


# ── action glyphs (SVG, recoloured to a theme token) ──────────────────────


def _svg_dir() -> Path:
    return _icons_dir() / "svg"


@lru_cache(maxsize=None)
def _load_svg_text(name: str) -> str:
    """Read an action SVG's markup (cached). Missing file -> empty string."""
    path = _svg_dir() / f"{name}.svg"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


@lru_cache(maxsize=None)
def svg_icon(name: str, color: str, size: int = 16) -> QIcon:
    """A theme-coloured QIcon for the action glyph ``name``.

    ``color`` is a hex string (typically ``ThemeManager.color(token)``);
    ``currentColor`` in the SVG is replaced with it. Rendered at 2× for crisp
    HiDPI. Returns an empty icon if the glyph is missing so a typo never crashes
    the UI. Cached by ``(name, color, size)`` since these are stable per theme.
    """
    markup = _load_svg_text(name)
    if not markup:
        return QIcon()
    renderer = QSvgRenderer(markup.replace("currentColor", color).encode("utf-8"))
    pixmap = QPixmap(QSize(size * 2, size * 2))
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    pixmap.setDevicePixelRatio(2.0)
    icon = QIcon()
    icon.addPixmap(pixmap)
    return icon
