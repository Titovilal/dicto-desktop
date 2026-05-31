"""Shared icon helpers for the main window UI.

Builds QIcons from inline SVG data (with a bounded cache) and maps model keys
to their provider logos.
"""

from __future__ import annotations

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon, QPainter, QColor, QPixmap
from PySide6.QtWidgets import QApplication

from src.ui.icons import (
    SVG_OPENAI,
    SVG_GOOGLEGEMINI,
    SVG_QWEN,
)


_icon_cache: dict[tuple[str, int, str], QIcon] = {}  # (svg_data, size, color) -> QIcon
_ICON_CACHE_MAX = 64  # bound icon cache to avoid unbounded pixmap memory


def make_icon(svg_data: str, size: int, color: str) -> QIcon:
    """Create a QIcon from inline SVG data with a given color (cached, max 64 entries)."""
    key = (svg_data, size, color)
    cached = _icon_cache.get(key)
    if cached is not None:
        return cached

    from PySide6.QtSvg import QSvgRenderer

    scale = 2
    app = QApplication.instance()
    if app and isinstance(app, QApplication):
        screen = app.primaryScreen()
        if screen:
            scale = max(2, int(screen.devicePixelRatio()))

    colored = svg_data.replace("currentColor", color)
    renderer = QSvgRenderer(colored.encode())
    px = QPixmap(QSize(size * scale, size * scale))
    px.fill(QColor(0, 0, 0, 0))
    painter = QPainter(px)
    renderer.render(painter)
    painter.end()
    px.setDevicePixelRatio(scale)
    icon = QIcon()
    icon.addPixmap(px)

    # Evict oldest entry if cache is full (simple FIFO — icons are small & stable)
    if len(_icon_cache) >= _ICON_CACHE_MAX:
        _icon_cache.pop(next(iter(_icon_cache)))
    _icon_cache[key] = icon
    return icon


# Maps model key prefixes/substrings to their provider SVG icon
_MODEL_PROVIDER_SVG: list[tuple[str, str]] = []


def get_provider_svg_for_model(model_key: str) -> str | None:
    """Return the provider SVG string for a given model key, or None."""
    # Lazy-build the list on first call so SVG constants are already resolved
    global _MODEL_PROVIDER_SVG
    if not _MODEL_PROVIDER_SVG:
        _MODEL_PROVIDER_SVG = [
            ("gemini", SVG_GOOGLEGEMINI),
            ("qwen", SVG_QWEN),
            # OpenAI / Whisper models
            ("openai", SVG_OPENAI),
            ("v3-turbo", SVG_OPENAI),
            ("v3", SVG_OPENAI),
            ("gpt", SVG_OPENAI),
        ]
    key_lower = model_key.lower()
    for prefix, svg in _MODEL_PROVIDER_SVG:
        if prefix in key_lower:
            return svg
    return None
