"""Overlay controls — elapsed timer plus stop and pause/resume buttons.

Owns the wall-clock timer (``format_elapsed``) and the control widgets the
overlay lays out per the design: a big round stop button (red while recording,
green/play while paused), a bordered pause/resume button and a monospace timer
label. Emits intent only (pause/resume/stop); the app layer acts on it. Icons
recolour on theme change, tooltips re-localise on language change.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, QSize, Qt, QTimer, Signal
from PySide6.QtWidgets import QLabel, QPushButton

from dicto.i18n import on_language_changed, t
from dicto.ui import icons
from dicto.ui.theme.manager import ThemeManager
from dicto.ui.theme.tokens import Token


def format_elapsed(seconds: float) -> str:
    """Format elapsed seconds as ``M:SS`` (or ``H:MM:SS`` past an hour)."""
    total = int(seconds)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


class OverlayControls(QObject):
    """Timer + stop + pause/resume; the overlay positions the widgets."""

    pauseRequested = Signal()
    resumeRequested = Signal()
    stopRequested = Signal()

    def __init__(self, theme: ThemeManager, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._theme = theme
        self._paused = False
        self._elapsed = 0.0

        self._timer = QTimer(self)
        self._timer.setInterval(250)
        self._timer.timeout.connect(self._tick)

        # Big round stop button (left side of the card).
        self.stop_btn = QPushButton()
        self.stop_btn.setObjectName("overlayStop")
        self.stop_btn.setFixedSize(44, 44)
        self.stop_btn.setIconSize(QSize(16, 16))
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_btn.clicked.connect(self.stopRequested)

        # Bordered pause/resume button (right side).
        self.pause_btn = QPushButton()
        self.pause_btn.setObjectName("overlayPause")
        self.pause_btn.setFixedSize(34, 34)
        self.pause_btn.setIconSize(QSize(16, 16))
        self.pause_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pause_btn.clicked.connect(self._on_pause_clicked)

        # Monospace tabular timer.
        self.time_label = QLabel(format_elapsed(0))
        self.time_label.setObjectName("overlayTimer")

        self._refresh_style()
        self.retranslate()

        self._theme.themeChanged.connect(lambda _e: self._refresh_style())
        self._unsub_lang = on_language_changed(lambda _l: self.retranslate())

    # ── theming ─────────────────────────────────────────────────────────

    def _refresh_style(self) -> None:
        red = self._theme.color(Token.STATUS_RECORDING)
        red_hover = self._theme.color(Token.STATUS_RECORDING_HOVER)
        green = self._theme.color(Token.STATUS_SUCCESS)
        bg = red if not self._paused else green
        hover = red_hover if not self._paused else green
        self.stop_btn.setStyleSheet(
            f"QPushButton#overlayStop {{ background-color: {bg}; border: none;"
            " border-radius: 22px; }"
            f" QPushButton#overlayStop:hover {{ background-color: {hover}; }}"
        )
        self.stop_btn.setIcon(
            icons.svg_icon("play" if self._paused else "stop", "#ffffff", 16)
        )
        self.pause_btn.setStyleSheet(
            f"QPushButton#overlayPause {{ background-color: {self._theme.color(Token.BG_ELEVATED)};"
            f" border: 1px solid {self._theme.color(Token.BORDER)}; border-radius: 9px; }}"
            f" QPushButton#overlayPause:hover {{ background-color:"
            f" {self._theme.color(Token.BG_HOVER)}; }}"
        )
        self.pause_btn.setIcon(
            icons.svg_icon(
                "play" if self._paused else "pause",
                self._theme.color(Token.TEXT_MUTED),
                16,
            )
        )
        self.time_label.setStyleSheet(
            f"QLabel#overlayTimer {{ color: {self._theme.color(Token.TEXT)};"
            ' font-family: "Consolas"; font-size: 14px; font-weight: 500;'
            " background: transparent; border: none; }"
        )

    def retranslate(self) -> None:
        self.pause_btn.setToolTip(t("overlay.resume") if self._paused else t("overlay.pause"))
        self.stop_btn.setToolTip(t("overlay.resume") if self._paused else t("overlay.stop"))

    # ── visibility (the overlay shows/hides the trio together) ─────────

    def set_visible(self, visible: bool) -> None:
        for w in (self.stop_btn, self.pause_btn, self.time_label):
            w.setVisible(visible)

    # ── timer ───────────────────────────────────────────────────────────

    def start(self) -> None:
        """Reset and start counting from zero."""
        self._elapsed = 0.0
        self._paused = False
        self.time_label.setText(format_elapsed(0))
        self._refresh_style()
        self.retranslate()
        self._timer.start()

    def stop(self) -> None:
        self._timer.stop()

    @property
    def elapsed(self) -> float:
        return self._elapsed

    def _tick(self) -> None:
        if not self._paused:
            self._elapsed += self._timer.interval() / 1000.0
            self.time_label.setText(format_elapsed(self._elapsed))

    # ── pause / resume ──────────────────────────────────────────────────

    @property
    def is_paused(self) -> bool:
        return self._paused

    def _on_pause_clicked(self) -> None:
        if self._paused:
            self.set_paused(False)
            self.resumeRequested.emit()
        else:
            self.set_paused(True)
            self.pauseRequested.emit()

    def set_paused(self, paused: bool) -> None:
        """Reflect paused state in the UI (does not emit)."""
        self._paused = paused
        self._refresh_style()
        self.retranslate()

    def dispose(self) -> None:
        self._timer.stop()
        self._unsub_lang()
