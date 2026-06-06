"""The ephemeral recording overlay — a small, draggable, always-on-top card.

Live feedback while dictating (status dot, label, waveform, pause/stop). Visual
only: it reflects ``AppState`` and audio levels and emits intent signals; it
never records. Styled from theme tokens; drag persists its position in Settings.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QPoint, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from dicto.config.settings import Settings
from dicto.core.state import AppState
from dicto.i18n import on_language_changed, t
from dicto.ui import icons
from dicto.ui.overlay.controls import OverlayControls
from dicto.ui.overlay.waveform import WaveformWidget
from dicto.ui.theme.manager import ThemeManager
from dicto.ui.theme.tokens import Token

logger = logging.getLogger(__name__)

_MARGIN = 16
_TOP_OFFSET = 50
_SUCCESS_HIDE_MS = 1400
_ERROR_HIDE_MS = 3500


class Overlay(QWidget):
    """Frameless draggable status card shown while recording/processing."""

    recordRequested = Signal()
    stopRequested = Signal()
    pauseRequested = Signal()
    resumeRequested = Signal()
    openAppRequested = Signal()

    def __init__(
        self,
        theme: ThemeManager,
        settings: Settings,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._theme = theme
        self._settings = settings
        self._state = AppState.IDLE

        self._drag_active = False
        self._drag_offset = QPoint()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(190, 64)

        self._build_ui()
        self._apply_card_style()
        self._restore_position()
        self.hide()

        self._theme.themeChanged.connect(lambda _e: self._on_theme_changed())
        self._unsub_lang = on_language_changed(lambda _l: self.retranslate())

    # ── construction ────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self._card = QWidget()
        self._card.setObjectName("overlayCard")
        card_layout = QVBoxLayout(self._card)
        card_layout.setContentsMargins(0, 6, 0, 6)
        card_layout.setSpacing(4)

        # Status row: dot + label + open-app button.
        status_row = QHBoxLayout()
        status_row.setContentsMargins(8, 0, 6, 0)
        status_row.setSpacing(5)

        self._dot = QWidget()
        self._dot.setFixedSize(6, 6)
        status_row.addWidget(self._dot, 0, Qt.AlignmentFlag.AlignVCenter)

        self._label = QLabel()
        self._label.setObjectName("overlayLabel")
        status_row.addWidget(self._label, 1)

        self._open_btn = QPushButton()
        self._open_btn.setObjectName("overlayOpenBtn")
        self._open_btn.setFixedSize(22, 22)
        self._open_btn.setProperty("overlayIcon", True)
        self._open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._open_btn.clicked.connect(self.openAppRequested)
        status_row.addWidget(self._open_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        card_layout.addLayout(status_row)

        # Waveform.
        self._waveform = WaveformWidget(
            self._theme, token=Token.STATUS_RECORDING, height=16, mode="live"
        )
        card_layout.addWidget(self._waveform)

        # Controls (timer + pause/stop), hidden until recording.
        self._controls = OverlayControls(self._theme)
        self._controls.pauseRequested.connect(self.pauseRequested)
        self._controls.resumeRequested.connect(self.resumeRequested)
        self._controls.stopRequested.connect(self.stopRequested)
        card_layout.addWidget(self._controls)
        self._controls.hide()

        outer.addWidget(self._card)
        self.retranslate()
        self._refresh_icons()

    # ── theme / i18n ────────────────────────────────────────────────────

    def _apply_card_style(self, accent_token: Token = Token.BORDER) -> None:
        bg = self._theme.color(Token.BG_ELEVATED)
        border = self._theme.color(accent_token)
        text = self._theme.color(Token.TEXT)
        self._card.setStyleSheet(
            f"QWidget#overlayCard {{ background-color: {bg};"
            f" border: 1px solid {border}; border-radius: 10px; }}"
            f" QLabel#overlayLabel {{ color: {text}; font-size: 12px; font-weight: 600;"
            " background: transparent; }"
            " QPushButton[overlayIcon=\"true\"] { background: transparent; border: none;"
            " border-radius: 6px; padding: 2px; }"
            f" QPushButton[overlayIcon=\"true\"]:hover {{ background-color:"
            f" {self._theme.color(Token.BG_HOVER)}; }}"
        )

    def _dot_color(self) -> str:
        return {
            AppState.RECORDING: self._theme.color(Token.STATUS_RECORDING),
            AppState.PAUSED: self._theme.color(Token.STATUS_PROCESSING),
            AppState.PROCESSING: self._theme.color(Token.STATUS_PROCESSING),
            AppState.SUCCESS: self._theme.color(Token.STATUS_SUCCESS),
            AppState.ERROR: self._theme.color(Token.STATUS_ERROR),
        }.get(self._state, self._theme.color(Token.TEXT_MUTED))

    def _refresh_dot(self) -> None:
        self._dot.setStyleSheet(f"background-color: {self._dot_color()}; border-radius: 3px;")

    def _refresh_icons(self) -> None:
        self._open_btn.setIcon(icons.svg_icon("external", self._theme.color(Token.TEXT_MUTED), 14))

    def _on_theme_changed(self) -> None:
        self._apply_card_style()
        self._refresh_dot()
        self._refresh_icons()

    def retranslate(self) -> None:
        self._open_btn.setToolTip(t("overlay.open_app"))
        self._apply_state_label()

    # ── state ───────────────────────────────────────────────────────────

    def set_state(self, state: AppState) -> None:
        """Reflect the app state: label, dot, waveform mode and visibility."""
        self._state = state
        if state is AppState.RECORDING:
            self._show_recording()
        elif state is AppState.PAUSED:
            self._show_paused()
        elif state is AppState.PROCESSING:
            self._show_processing()
        elif state is AppState.SUCCESS:
            self._show_success()
        elif state is AppState.ERROR:
            self._show_error()
        else:
            self._show_idle()

    def _apply_state_label(self) -> None:
        self._label.setText(t(f"status.{self._state.value}"))

    def _show_recording(self) -> None:
        self._controls.show()
        self._controls.start()
        self._waveform.set_token(Token.STATUS_RECORDING)
        self._waveform.mode = "live"
        self._waveform.start()
        self._apply_state_label()
        self._refresh_dot()
        self._apply_card_style(Token.STATUS_RECORDING)
        self.show_at_saved()

    def _show_paused(self) -> None:
        self._controls.set_paused(True)
        self._waveform.stop()
        self._apply_state_label()
        self._refresh_dot()

    def _show_processing(self) -> None:
        self._controls.set_paused(False)
        self._controls.stop()
        self._waveform.set_token(Token.STATUS_PROCESSING)
        self._waveform.mode = "pulse"
        self._waveform.start()
        self._apply_state_label()
        self._refresh_dot()
        self._apply_card_style(Token.STATUS_PROCESSING)

    def _show_success(self) -> None:
        self._controls.stop()
        self._controls.hide()
        self._waveform.set_token(Token.STATUS_SUCCESS)
        self._waveform.mode = "settle"
        self._waveform.start()
        self._apply_state_label()
        self._refresh_dot()
        self._apply_card_style(Token.STATUS_SUCCESS)
        QTimer.singleShot(_SUCCESS_HIDE_MS, self._hide_if_idle_like)

    def _show_error(self) -> None:
        self._controls.stop()
        self._controls.hide()
        self._waveform.stop()
        self._apply_state_label()
        self._refresh_dot()
        self._apply_card_style(Token.STATUS_ERROR)
        QTimer.singleShot(_ERROR_HIDE_MS, self._hide_if_idle_like)

    def _show_idle(self) -> None:
        self._controls.stop()
        self._controls.hide()
        self._waveform.clear()
        self._apply_state_label()
        self._refresh_dot()
        self._apply_card_style()
        self.hide()

    def _hide_if_idle_like(self) -> None:
        # Only auto-hide if we're not back in an active recording cycle.
        if self._state in (AppState.SUCCESS, AppState.ERROR):
            self.hide()

    # ── live level ──────────────────────────────────────────────────────

    def set_level(self, level: float) -> None:
        """Feed a live RMS level (0..1) to the waveform while recording."""
        if self._state is AppState.RECORDING:
            self._waveform.set_level(level)

    # ── position persistence ────────────────────────────────────────────

    def show_at_saved(self) -> None:
        self._restore_position()
        self.show()
        self.raise_()

    def _restore_position(self) -> None:
        ov = self._settings.overlay
        if ov.x is not None and ov.y is not None and self._on_screen(ov.x, ov.y):
            self.move(ov.x, ov.y)
        else:
            self._move_to_anchor(ov.position)

    def _move_to_anchor(self, anchor: str) -> None:
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        geo = screen.geometry()
        w, h = self.width(), self.height()
        positions = {
            "top-left": (_MARGIN, _TOP_OFFSET),
            "top-right": (geo.width() - w - _MARGIN, _TOP_OFFSET),
            "bottom-left": (_MARGIN, geo.height() - h - _MARGIN),
            "bottom-right": (geo.width() - w - _MARGIN, geo.height() - h - _MARGIN),
            "center": ((geo.width() - w) // 2, (geo.height() - h) // 2),
        }
        x, y = positions.get(anchor, positions["top-right"])
        self.move(x, y)

    def _on_screen(self, x: int, y: int) -> bool:
        screen = QApplication.primaryScreen()
        if screen is None:
            return False
        geo = screen.availableGeometry()
        # Require the top-left to land inside the available area.
        return geo.contains(QPoint(x, y))

    def reset_position(self) -> None:
        """Forget the dragged position and snap back to the configured anchor."""
        self._settings.overlay.x = None
        self._settings.overlay.y = None
        self._settings.save()
        self._move_to_anchor(self._settings.overlay.position)

    def _persist_position(self) -> None:
        pos = self.pos()
        self._settings.overlay.x = pos.x()
        self._settings.overlay.y = pos.y()
        self._settings.save()

    # ── dragging ────────────────────────────────────────────────────────

    def mousePressEvent(self, event) -> None:  # noqa: N802, ANN001 — Qt override
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_active = True
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802, ANN001 — Qt override
        if self._drag_active and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802, ANN001 — Qt override
        if self._drag_active:
            self._drag_active = False
            self._persist_position()
        event.accept()

    # ── teardown ────────────────────────────────────────────────────────

    def dispose(self) -> None:
        self._controls.dispose()
        self._unsub_lang()
        self.close()
