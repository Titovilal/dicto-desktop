"""ThemeManager — resolves tokens to QSS, follows the OS, switches live.

The pure functions (``detect_system_theme``, ``resolve_palette``, ``build_qss``)
have no Qt dependency so they are unit-testable. ``ThemeManager`` is a thin
``QObject`` wrapper that applies the QSS to the running ``QApplication`` and
emits ``themeChanged`` when the effective palette changes.

A widget never reads a colour directly; it inherits it from the application
stylesheet built here. Components that need a token value at runtime (e.g. to
paint a custom waveform) call ``manager.color(Token.ACCENT)``.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QObject, Signal

from dicto.ui.theme.palettes import PALETTES, Palette
from dicto.ui.theme.tokens import Token

logger = logging.getLogger(__name__)

# A theme setting is one of these; "system" resolves to light/dark at runtime.
ThemeName = str  # "light" | "dark" | "system"


def detect_system_theme() -> str:
    """Read the Windows app theme. Returns "light" or "dark" (default light).

    Uses ``AppsUseLightTheme`` under
    ``HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize``.
    Falls back to "light" anywhere this key is unavailable (non-Windows, error).
    """
    try:
        import winreg  # noqa: PLC0415 — Windows-only, imported lazily

        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        )
        try:
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        finally:
            winreg.CloseKey(key)
        return "light" if value else "dark"
    except Exception:  # noqa: BLE001 — any failure -> light
        return "light"


def resolve_theme(name: ThemeName) -> str:
    """Map a setting ("light"/"dark"/"system") to a concrete "light"/"dark"."""
    if name == "system":
        return detect_system_theme()
    return name if name in PALETTES else "light"


def resolve_palette(name: ThemeName) -> Palette:
    """Concrete palette for a theme setting."""
    return PALETTES[resolve_theme(name)]


def build_qss(palette: Palette) -> str:
    """Build the application-wide Qt stylesheet from a palette.

    Intentionally small for Phase 0 — just enough that the empty window and
    common widgets pick up the theme. Components add their own rules later,
    always referencing tokens via this palette, never literal colours.
    """

    def c(token: Token) -> str:
        return palette[token]

    return f"""
    QWidget {{
        background-color: {c(Token.BG)};
        color: {c(Token.TEXT)};
        font-size: 13px;
    }}
    QFrame#elevated, QMenu, QToolTip {{
        background-color: {c(Token.BG_ELEVATED)};
        border: 1px solid {c(Token.BORDER)};
    }}
    QLabel[muted="true"] {{
        color: {c(Token.TEXT_MUTED)};
    }}
    QPushButton {{
        background-color: {c(Token.BG_ELEVATED)};
        border: 1px solid {c(Token.BORDER)};
        border-radius: 6px;
        padding: 6px 12px;
    }}
    QPushButton:hover {{
        background-color: {c(Token.BG_HOVER)};
    }}
    QPushButton[accent="true"] {{
        background-color: {c(Token.ACCENT)};
        color: {c(Token.TEXT_ON_ACCENT)};
        border: none;
    }}
    QPushButton[accent="true"]:hover {{
        background-color: {c(Token.ACCENT_HOVER)};
    }}
    QMenu::item:selected {{
        background-color: {c(Token.BG_SELECTED)};
    }}
    """


class ThemeManager(QObject):
    """Owns the active theme, applies QSS, emits ``themeChanged``."""

    # Emitted with the effective theme ("light"/"dark") after every apply.
    themeChanged = Signal(str)

    def __init__(self, app, theme: ThemeName = "system", parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._app = app
        self._setting: ThemeName = theme
        self._effective: str = resolve_theme(theme)

    @property
    def setting(self) -> ThemeName:
        """The configured theme ("light"/"dark"/"system")."""
        return self._setting

    @property
    def effective(self) -> str:
        """The concrete theme currently applied ("light"/"dark")."""
        return self._effective

    def color(self, token: Token) -> str:
        """Current hex value for a token (for custom-painted widgets)."""
        return resolve_palette(self._setting)[token]

    def apply(self) -> None:
        """(Re)build and apply the stylesheet for the current setting."""
        self._effective = resolve_theme(self._setting)
        qss = build_qss(PALETTES[self._effective])
        if self._app is not None:
            self._app.setStyleSheet(qss)
        logger.info("theme applied: %s (setting=%s)", self._effective, self._setting)
        self.themeChanged.emit(self._effective)

    def set_theme(self, theme: ThemeName) -> None:
        """Switch theme and re-apply live."""
        if theme == self._setting:
            return
        self._setting = theme
        self.apply()

    def refresh_system(self) -> None:
        """Re-resolve when following the OS and the OS theme may have changed."""
        if self._setting == "system" and resolve_theme("system") != self._effective:
            self.apply()
