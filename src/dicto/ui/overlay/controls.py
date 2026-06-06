"""Overlay controls — elapsed timer plus pause/resume and stop buttons.

Owns the wall-clock timer (``format_elapsed``) and icon buttons. Emits intent
only (pause/resume/stop); the app layer acts on it. Icons recolour on theme
change, tooltips re-localise on language change.
"""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

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


class OverlayControls(QWidget):
    """Timer + pause/resume + stop, emitted as intent signals."""

    pauseRequested = Signal()
    resumeRequested = Signal()
    stopRequested = Signal()

    def __init__(self, theme: ThemeManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._theme = theme
        self._paused = False
        self._elapsed = 0.0

        self._timer = QTimer(self)
        self._timer.setInterval(250)
        self._timer.timeout.connect(self._tick)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 6, 0)
        layout.setSpacing(5)

        self._time_label = QLabel(format_elapsed(0))
        self._time_label.setProperty("muted", True)
        layout.addWidget(self._time_label, 1, Qt.AlignmentFlag.AlignVCenter)

        self._pause_btn = self._make_button(self._on_pause_clicked)
        self._stop_btn = self._make_button(self.stopRequested.emit)
        layout.addWidget(self._pause_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._stop_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        self._refresh_icons()
        self.retranslate()

        self._theme.themeChanged.connect(lambda _e: self._refresh_icons())
        self._unsub_lang = on_language_changed(lambda _l: self.retranslate())

    # ── construction helpers ────────────────────────────────────────────

    def _make_button(self, on_click) -> QPushButton:  # noqa: ANN001
        btn = QPushButton()
        btn.setFixedSize(22, 22)
        btn.setIconSize(QSize(14, 14))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setProperty("overlayIcon", True)
        btn.clicked.connect(on_click)
        return btn

    def _refresh_icons(self) -> None:
        muted = self._theme.color(Token.TEXT_MUTED)
        rec = self._theme.color(Token.STATUS_RECORDING)
        glyph = "record" if self._paused else "pause"
        self._pause_btn.setIcon(icons.svg_icon(glyph, rec if self._paused else muted, 14))
        self._stop_btn.setIcon(icons.svg_icon("stop", rec, 14))

    def retranslate(self) -> None:
        self._pause_btn.setToolTip(t("overlay.resume") if self._paused else t("overlay.pause"))
        self._stop_btn.setToolTip(t("overlay.stop"))

    # ── timer ───────────────────────────────────────────────────────────

    def start(self) -> None:
        """Reset and start counting from zero."""
        self._elapsed = 0.0
        self._paused = False
        self._time_label.setText(format_elapsed(0))
        self._refresh_icons()
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
            self._time_label.setText(format_elapsed(self._elapsed))

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
        self._refresh_icons()
        self.retranslate()

    def dispose(self) -> None:
        self._timer.stop()
        self._unsub_lang()
