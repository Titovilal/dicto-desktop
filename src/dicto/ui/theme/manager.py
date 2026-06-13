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

    Mirrors the design-system rules in the hand-off's ``theme.css``: zinc
    surfaces, soft 9-11px radii, pill chips, a neutral "primary" button and a
    quiet text scale. Widgets opt into a style with ``objectName`` or dynamic
    properties (``chip``, ``ghost``, ``accent``…), never literal colours.
    """

    def c(token: Token) -> str:
        return palette[token]

    return f"""
    QWidget {{
        background-color: {c(Token.BG)};
        color: {c(Token.TEXT)};
        font-family: "Segoe UI Variable Text", "Segoe UI", sans-serif;
        font-size: 13px;
    }}
    QLabel, QCheckBox {{ background: transparent; }}
    QLabel[muted="true"] {{ color: {c(Token.TEXT_MUTED)}; }}
    QLabel[dim="true"] {{ color: {c(Token.TEXT_DIM)}; }}
    QLabel[heading="true"] {{ font-size: 17px; font-weight: 600; }}

    QFrame#elevated, QToolTip {{
        background-color: {c(Token.BG_ELEVATED)};
        border: 1px solid {c(Token.BORDER)};
    }}

    /* panels that sit next to the body (rail, titlebar, footers) */
    QFrame[panel="true"] {{ background-color: {c(Token.BG_PANEL)}; border: none; }}
    QFrame#rail {{
        background-color: {c(Token.BG_PANEL)};
        border: none;
        border-right: 1px solid {c(Token.BORDER)};
    }}
    QFrame#libraryPane {{
        background: transparent;
        border: none;
        border-right: 1px solid {c(Token.BORDER)};
    }}
    QFrame#detailFooter {{
        background-color: {c(Token.BG_PANEL)};
        border: none;
        border-top: 1px solid {c(Token.BORDER)};
    }}
    QFrame#tabsRule {{ background-color: {c(Token.BORDER)}; border: none; }}
    QLabel#avatar {{
        background-color: {c(Token.BG_HOVER)};
        border: 1px solid {c(Token.BORDER)};
        border-radius: 15px;
        font-size: 12px;
        font-weight: 600;
        color: {c(Token.TEXT_MUTED)};
    }}

    /* ── buttons ─────────────────────────────────────────────── */
    QPushButton {{
        background-color: {c(Token.BG_ELEVATED)};
        border: 1px solid {c(Token.BORDER)};
        border-radius: 9px;
        padding: 6px 13px;
        font-weight: 500;
    }}
    QPushButton:hover {{ background-color: {c(Token.BG_HOVER)}; }}
    QPushButton:disabled {{ color: {c(Token.TEXT_DIM)}; }}
    QPushButton[accent="true"] {{
        background-color: {c(Token.ACCENT)};
        color: {c(Token.TEXT_ON_ACCENT)};
        border: 1px solid {c(Token.ACCENT)};
    }}
    QPushButton[accent="true"]:hover {{ background-color: {c(Token.ACCENT_HOVER)}; }}
    QPushButton[ghost="true"] {{
        background: transparent;
        border: 1px solid transparent;
        color: {c(Token.TEXT_MUTED)};
    }}
    QPushButton[ghost="true"]:hover {{
        background-color: {c(Token.BG_ELEVATED)};
        color: {c(Token.TEXT)};
    }}
    QPushButton[iconBtn="true"] {{
        background: transparent;
        border: 1px solid transparent;
        border-radius: 9px;
        padding: 0px;
        color: {c(Token.TEXT_DIM)};
    }}
    QPushButton[iconBtn="true"]:hover {{
        background-color: {c(Token.BG_ELEVATED)};
        color: {c(Token.TEXT)};
    }}
    QPushButton[iconBtn="bordered"] {{
        background-color: {c(Token.BG_ELEVATED)};
        border: 1px solid {c(Token.BORDER)};
        border-radius: 9px;
        padding: 0px;
    }}
    QPushButton[iconBtn="bordered"]:hover {{ background-color: {c(Token.BG_HOVER)}; }}

    /* tag-filter chips (checkable pills) */
    QPushButton[chip="true"] {{
        background: transparent;
        border: 1px solid {c(Token.BORDER)};
        border-radius: 13px;
        padding: 3px 11px;
        font-size: 12px;
        color: {c(Token.TEXT_MUTED)};
    }}
    QPushButton[chip="true"]:hover {{ background-color: {c(Token.BG_ELEVATED)}; }}
    QPushButton[chip="true"]:checked {{
        background-color: {c(Token.ACCENT)};
        color: {c(Token.TEXT_ON_ACCENT)};
        border-color: {c(Token.ACCENT)};
    }}

    /* left rail */
    QPushButton[rail="true"] {{
        background: transparent;
        border: none;
        border-radius: 11px;
        color: {c(Token.TEXT_DIM)};
    }}
    QPushButton[rail="true"]:hover {{ background-color: {c(Token.BG_ELEVATED)}; }}
    QPushButton[rail="true"]:checked {{
        background-color: {c(Token.BG_ELEVATED)};
        color: {c(Token.TEXT)};
    }}
    QPushButton#railRecord {{
        background-color: {c(Token.STATUS_RECORDING)};
        border: none;
        border-radius: 20px;
    }}
    QPushButton#railRecord:hover {{ background-color: {c(Token.STATUS_RECORDING_HOVER)}; }}

    /* ── inputs ──────────────────────────────────────────────── */
    QLineEdit, QTextEdit, QPlainTextEdit {{
        background-color: {c(Token.BG_ELEVATED)};
        border: 1px solid {c(Token.BORDER)};
        border-radius: 9px;
        padding: 6px 10px;
        selection-background-color: {c(Token.BLUE)};
        selection-color: {c(Token.BG)};
    }}
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border-color: {c(Token.TEXT_DIM)};
    }}
    QLineEdit[bare="true"], QTextEdit[bare="true"] {{
        background: transparent;
        border: 1px solid transparent;
        border-radius: 6px;
    }}
    QLineEdit#detailTitle {{
        font-size: 20px;
        font-weight: 600;
        padding: 2px 4px;
    }}

    QComboBox {{
        background-color: {c(Token.BG_ELEVATED)};
        border: 1px solid {c(Token.BORDER)};
        border-radius: 9px;
        padding: 5px 10px;
    }}
    QComboBox:hover {{ background-color: {c(Token.BG_HOVER)}; }}
    QComboBox::drop-down {{ border: none; width: 22px; }}
    QComboBox QAbstractItemView {{
        background-color: {c(Token.BG_PANEL)};
        border: 1px solid {c(Token.BORDER)};
        border-radius: 9px;
        selection-background-color: {c(Token.BG_ELEVATED)};
        selection-color: {c(Token.TEXT)};
        outline: none;
    }}

    /* ── lists ───────────────────────────────────────────────── */
    QListWidget {{
        background: transparent;
        border: none;
        outline: none;
    }}
    QListWidget::item {{
        border: 1px solid transparent;
        border-radius: 10px;
        margin: 1px 0px;
    }}
    QListWidget::item:hover {{ background-color: {c(Token.BG_ELEVATED)}; }}
    QListWidget::item:selected {{
        background-color: {c(Token.BG_SELECTED)};
        border-color: {c(Token.BORDER)};
    }}

    /* ── tabs (detail view) ──────────────────────────────────── */
    /* The selected tab's 2px underline sits flush on the #tabsRule baseline
       directly below the bar (no padding-bottom gap), so the indicator and
       the divider read as one continuous line. */
    QTabBar {{ background: transparent; }}
    QTabBar::tab {{
        background: transparent;
        border: none;
        border-bottom: 2px solid transparent;
        margin-right: 4px;
        padding: 8px 4px 8px;
        font-weight: 500;
        color: {c(Token.TEXT_DIM)};
    }}
    QTabBar::tab:hover:!selected:!disabled {{ color: {c(Token.TEXT_MUTED)}; }}
    QTabBar::tab:selected {{
        color: {c(Token.TEXT)};
        border-bottom-color: {c(Token.ACCENT)};
    }}
    QTabBar::tab:disabled {{ color: {c(Token.BORDER)}; }}

    /* ── transform result (detail tabs) ──────────────────────── */
    /* Result header: "✦ Resumen" left, "↺ Cacheado" chip right. */
    QLabel#xformHead {{ font-size: 13px; font-weight: 600; color: {c(Token.TEXT_MUTED)}; }}
    QLabel#cacheChip {{ font-size: 11px; color: {c(Token.TEXT_DIM)}; }}
    QPushButton#xformGen {{
        background-color: {c(Token.BG_ELEVATED)};
        border: 1px solid {c(Token.BORDER)};
        border-radius: 8px;
        padding: 4px 11px;
        font-size: 12px;
        font-weight: 500;
        color: {c(Token.TEXT_MUTED)};
    }}
    QPushButton#xformGen:hover {{ background-color: {c(Token.BG_HOVER)}; color: {c(Token.TEXT)}; }}
    QPushButton#xformGen:disabled {{ color: {c(Token.TEXT_DIM)}; }}
    QLabel#xformEmpty {{ color: {c(Token.TEXT_DIM)}; font-size: 14px; }}
    QScrollArea#xformScroll, QScrollArea#chatScroll {{ background: transparent; border: none; }}
    QScrollArea#xformScroll > QWidget > QWidget,
    QScrollArea#chatScroll > QWidget > QWidget {{ background: transparent; }}

    /* prose (summary / rewrite) */
    QLabel#prose {{ font-size: 14px; line-height: 1.7; color: {c(Token.TEXT)}; }}

    /* key points: numbered chip + text */
    QLabel#kpNum {{
        background-color: {c(Token.BG_ELEVATED)};
        border: 1px solid {c(Token.BORDER)};
        border-radius: 7px;
        color: {c(Token.TEXT_MUTED)};
        font-weight: 600;
        font-size: 12px;
    }}
    QLabel#kpText {{ font-size: 14px; color: {c(Token.TEXT)}; }}

    /* flashcards: grid of cards */
    QFrame#xformCard {{
        background-color: {c(Token.BG_ELEVATED)};
        border: 1px solid {c(Token.BORDER)};
        border-radius: 12px;
    }}
    QLabel#cardTag {{
        font-size: 10px; font-weight: 600; color: {c(Token.TEXT_DIM)};
    }}
    QLabel#cardQ {{ font-size: 13px; font-weight: 600; color: {c(Token.TEXT)}; }}
    QLabel#cardA {{ font-size: 13px; color: {c(Token.TEXT_MUTED)}; }}

    /* ── chat ("ask your notes") ─────────────────────────────── */
    QLabel#chatHead {{ font-size: 17px; font-weight: 600; color: {c(Token.TEXT)}; }}
    QLabel#chatEmpty {{ color: {c(Token.TEXT_DIM)}; font-size: 14px; }}
    QLabel#bubbleUser {{
        background-color: {c(Token.ACCENT)};
        color: {c(Token.TEXT_ON_ACCENT)};
        border-radius: 14px;
        padding: 10px 14px;
        font-size: 14px;
    }}
    QLabel#bubbleAi {{
        background-color: {c(Token.BG_ELEVATED)};
        border: 1px solid {c(Token.BORDER)};
        color: {c(Token.TEXT)};
        border-radius: 14px;
        padding: 10px 14px;
        font-size: 14px;
    }}

    /* ── menus (tray / context) ──────────────────────────────── */
    QMenu {{
        background-color: {c(Token.BG_PANEL)};
        border: 1px solid {c(Token.BORDER)};
        border-radius: 12px;
        padding: 7px;
    }}
    QMenu::item {{
        border-radius: 8px;
        padding: 8px 12px;
    }}
    QMenu::item:selected {{ background-color: {c(Token.BG_ELEVATED)}; }}
    QMenu::separator {{
        height: 1px;
        background-color: {c(Token.BORDER)};
        margin: 5px 4px;
    }}

    /* ── settings modal ──────────────────────────────────────── */
    /* The dialog itself is translucent (WA_TranslucentBackground) so the
       card's rounded corners read as real transparency on all four sides;
       the fill + border + radius live on the inner #modalCard frame. */
    QDialog#settingsModal, QDialog#dictionaryModal {{
        background: transparent;
    }}
    QFrame#modalCard {{
        background-color: {c(Token.BG)};
        border: 1px solid {c(Token.BORDER)};
        border-radius: 16px;
    }}
    QFrame#modalNav {{
        background-color: {c(Token.BG_PANEL)};
        border: none;
        border-right: 1px solid {c(Token.BORDER)};
    }}
    QFrame#modalHead {{
        background: transparent;
        border: none;
        border-bottom: 1px solid {c(Token.BORDER)};
    }}
    QPushButton[mnav="true"] {{
        background: transparent;
        border: none;
        border-radius: 9px;
        padding: 8px 11px;
        font-weight: 500;
        color: {c(Token.TEXT_MUTED)};
        text-align: left;
    }}
    QPushButton[mnav="true"]:hover {{
        background-color: {c(Token.BG_ELEVATED)};
        color: {c(Token.TEXT)};
    }}
    QPushButton[mnav="true"]:checked {{
        background-color: {c(Token.BG_ELEVATED)};
        color: {c(Token.TEXT)};
    }}
    QLabel[settingsTitle="true"] {{ font-size: 14px; font-weight: 600; }}
    QLabel[fieldLabel="true"] {{ font-size: 13px; font-weight: 500; }}
    QFrame[fieldRule="true"] {{
        background-color: {c(Token.BORDER_SOFT)};
        border: none;
        max-height: 1px;
    }}
    /* ── dictionary modal table ──────────────────────────────── */
    QLabel[tableHead="true"] {{
        font-size: 10.5px;
        font-weight: 600;
        letter-spacing: 1px;
        color: {c(Token.TEXT_DIM)};
    }}
    QFrame[dictRow="true"] {{
        background: transparent;
        border: none;
        border-bottom: 1px solid {c(Token.BORDER_SOFT)};
    }}
    QFrame[dictRow="true"]:hover {{ background-color: {c(Token.BG_HOVER)}; }}
    QLabel[dictTerm="true"] {{
        font-family: "Consolas";
        font-size: 13px;
        font-weight: 600;
    }}

    QLabel#kbdPill {{
        font-family: "Consolas";
        font-size: 11px;
        padding: 2px 7px;
        border-radius: 6px;
        background-color: {c(Token.KBD_BG)};
        border: 1px solid {c(Token.BORDER)};
        color: {c(Token.TEXT_MUTED)};
    }}

    /* ── scrollbars ──────────────────────────────────────────── */
    QScrollBar:vertical {{
        background: transparent; width: 10px; margin: 2px;
    }}
    QScrollBar::handle:vertical {{
        background-color: {c(Token.BORDER)};
        border-radius: 4px; min-height: 28px;
    }}
    QScrollBar::handle:vertical:hover {{ background-color: {c(Token.TEXT_DIM)}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar:horizontal {{
        background: transparent; height: 10px; margin: 2px;
    }}
    QScrollBar::handle:horizontal {{
        background-color: {c(Token.BORDER)};
        border-radius: 4px; min-width: 28px;
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

    /* splitter / status bar */
    QSplitter::handle {{ background-color: {c(Token.BORDER)}; }}
    QStatusBar {{
        background-color: {c(Token.BG_PANEL)};
        color: {c(Token.TEXT_DIM)};
        border-top: 1px solid {c(Token.BORDER)};
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
