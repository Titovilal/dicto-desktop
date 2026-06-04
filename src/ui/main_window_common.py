"""
Shared module-level helpers for the MainWindow mixins.

Holds the icon cache, provider-SVG lookup, and the HotkeyButton widget so that
BuildMixin/SettingsMixin/StateMixin and MainWindow can all import them without
circular imports.
"""

from __future__ import annotations

import logging

from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtGui import QIcon, QPainter, QColor, QPixmap

from src.i18n import t
from src.ui.icons import (
    SVG_GOOGLEGEMINI,
    SVG_QWEN,
    SVG_OPENAI,
)

logger = logging.getLogger(__name__)


_icon_cache: dict[tuple[str, int, str], QIcon] = {}  # (svg_data, size, color) -> QIcon
_ICON_CACHE_MAX = 64  # bound icon cache to avoid unbounded pixmap memory


def _make_icon(svg_data: str, size: int, color: str) -> QIcon:
    """Create a QIcon from inline SVG data with a given color (cached, max 64 entries)."""
    key = (svg_data, size, color)
    cached = _icon_cache.get(key)
    if cached is not None:
        return cached

    from PySide6.QtSvg import QSvgRenderer
    from PySide6.QtWidgets import QApplication

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


def _get_provider_svg_for_model(model_key: str) -> str | None:
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


class HotkeyButton(QPushButton):
    """A button that captures key combinations when clicked."""

    hotkey_changed = Signal(list, str)  # (modifiers, key)

    # Map Qt modifiers to config-style names
    _MOD_MAP = {
        Qt.KeyboardModifier.ControlModifier: "ctrl",
        Qt.KeyboardModifier.ShiftModifier: "shift",
        Qt.KeyboardModifier.AltModifier: "alt",
        Qt.KeyboardModifier.MetaModifier: "cmd",
    }

    # Map Qt keys to config-style names
    _KEY_MAP = {
        Qt.Key.Key_Space: "space",
        Qt.Key.Key_Return: "enter",
        Qt.Key.Key_Enter: "enter",
        Qt.Key.Key_Tab: "tab",
        Qt.Key.Key_Escape: "esc",
        Qt.Key.Key_Backspace: "backspace",
        Qt.Key.Key_Delete: "delete",
        Qt.Key.Key_Up: "up",
        Qt.Key.Key_Down: "down",
        Qt.Key.Key_Left: "left",
        Qt.Key.Key_Right: "right",
    }

    _MODIFIER_KEYS = {
        Qt.Key.Key_Control,
        Qt.Key.Key_Shift,
        Qt.Key.Key_Alt,
        Qt.Key.Key_Meta,
    }

    def __init__(self, modifiers: list[str], key: str, parent=None):
        super().__init__(parent)
        self._modifiers = modifiers
        self._key = key
        self._listening = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._update_display()
        self.clicked.connect(self._start_listening)

    @staticmethod
    def format_hotkey(modifiers: list[str], key: str) -> str:
        parts = [m.capitalize() for m in modifiers] + [key.capitalize()]
        return "+".join(parts)

    def _update_display(self):
        self.setText(self.format_hotkey(self._modifiers, self._key))

    def _start_listening(self):
        self._listening = True
        self.setText(t("press_combination"))
        self.setFocus()

    def keyPressEvent(self, event):
        if not self._listening:
            super().keyPressEvent(event)
            return

        qt_key = event.key()

        # Ignore lone modifier presses
        if qt_key in self._MODIFIER_KEYS:
            return

        # Escape cancels
        if qt_key == Qt.Key.Key_Escape:
            self._listening = False
            self._update_display()
            return

        # Build modifier list
        mods = event.modifiers()
        modifiers: list[str] = []
        for qt_mod, name in self._MOD_MAP.items():
            if mods & qt_mod:
                modifiers.append(name)

        # Determine key name
        if qt_key in self._KEY_MAP:
            key_name = self._KEY_MAP[qt_key]
        elif Qt.Key.Key_A <= qt_key <= Qt.Key.Key_Z:
            key_name = chr(qt_key).lower()
        elif Qt.Key.Key_0 <= qt_key <= Qt.Key.Key_9:
            key_name = chr(qt_key)
        else:
            key_name = event.text().lower().strip()
            if not key_name:
                return

        self._modifiers = modifiers
        self._key = key_name
        self._listening = False
        self._update_display()
        self.hotkey_changed.emit(modifiers, key_name)

    def focusOutEvent(self, event):
        if self._listening:
            self._listening = False
            self._update_display()
        super().focusOutEvent(event)
