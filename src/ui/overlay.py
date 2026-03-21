"""
Overlay window for visual feedback during recording and processing.
Purely informational — no interactive elements.
"""

import math

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor

from src.i18n import t
from src.ui.main_window_styles import (
    MUTED, BORDER, SECONDARY, TEXT, TEXT_DIM, PRIMARY, PRIMARY_FG,
    RED, RED_HOVER, AMBER, GREEN,
    SVG_AUDIO_LINES,
)


class OverlayWaveformWidget(QWidget):
    def __init__(self, color: str = RED, parent=None):
        super().__init__(parent)
        self.bar_count = 20
        self.bar_heights = [0.3] * self.bar_count
        self.color = color
        self.setFixedSize(80, 12)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_bars)
        self._tick = 0

    def start(self):
        self._tick = 0
        self._timer.start(50)

    def stop(self):
        self._timer.stop()

    def _update_bars(self):
        self._tick += 1
        for i in range(self.bar_count):
            phase = i * 0.7 + self._tick * 0.15
            self.bar_heights[i] = 0.2 + 0.8 * abs(math.sin(phase))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        total_width = self.bar_count * 3 - 1
        start_x = (self.width() - total_width) // 2
        max_h = self.height()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(self.color))
        for i in range(self.bar_count):
            h = max(1, int(self.bar_heights[i] * max_h))
            x = start_x + i * 3
            y = (max_h - h) // 2
            painter.drawRoundedRect(x, y, 2, h, 1, 1)
        painter.end()


FONT = '"JetBrains Mono", "Cascadia Code", "Consolas", monospace'
LABEL_BASE = f"font-family: {FONT}; background: transparent; letter-spacing: -0.5px;"


class OverlayWindow(QWidget):
    """Fixed top-right overlay showing status. Purely informational, no interactive elements."""

    def __init__(self, position: str = "top-right", size: int = 100, opacity: float = 0.85):
        super().__init__()
        self.position_name = "top-right"  # Always top-right
        self.window_opacity = opacity
        self._persistent = False

        self._dots_count = 0
        self._dots_timer = QTimer(self)
        self._dots_timer.timeout.connect(self._animate_dots)

        self._dot_visible = True
        self._dot_pulse_timer = QTimer(self)
        self._dot_pulse_timer.timeout.connect(self._pulse_dot)

        self._setup_ui()
        self._setup_window()

    # ── Window setup ─────────────────────────────────────────

    def _setup_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        self.setFixedSize(180, 52)
        self._position_window()
        self.hide()

    def _position_window(self):
        from PySide6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        margin = 16
        top_offset = 50
        w, h = self.width(), self.height()
        positions = {
            "top-left": (margin, top_offset),
            "top-right": (screen.width() - w - margin, top_offset),
            "bottom-left": (margin, screen.height() - h - margin),
            "bottom-right": (screen.width() - w - margin, screen.height() - h - margin),
            "center": ((screen.width() - w) // 2, (screen.height() - h) // 2),
        }
        x, y = positions.get(self.position_name, positions["top-right"])
        self.move(x, y)

    # ── UI ───────────────────────────────────────────────────

    def _setup_ui(self):
        self.current_state = "idle"

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.card = QWidget()
        self.card.setObjectName("overlayCard")
        self._set_card_style()

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(8, 6, 8, 6)
        card_layout.setSpacing(4)

        # Waveform (top)
        self.waveform = OverlayWaveformWidget(RED)
        self.waveform.hide()
        card_layout.addWidget(self.waveform, 0, Qt.AlignmentFlag.AlignCenter)

        # Status row (dot + label)
        status_row = QHBoxLayout()
        status_row.setContentsMargins(0, 0, 0, 0)
        status_row.setSpacing(5)

        self.status_dot = QWidget()
        self.status_dot.setFixedSize(6, 6)
        self.status_dot.setStyleSheet(f"background-color: {TEXT_DIM}; border-radius: 3px;")
        status_row.addWidget(self.status_dot, 0, Qt.AlignmentFlag.AlignVCenter)

        self.status_label = QLabel(t("ready"))
        self.status_label.setStyleSheet(f"color: {TEXT}; font-size: 10px; font-weight: 600; {LABEL_BASE}")
        status_row.addWidget(self.status_label, 1)

        card_layout.addLayout(status_row)

        # Hidden sub_label kept for error messages only
        self.sub_label = QLabel("")
        self.sub_label.hide()

        main_layout.addWidget(self.card)

    def _set_card_style(self, border_accent: str = BORDER):
        self.card.setStyleSheet(
            f"QWidget#overlayCard {{ "
            f"background-color: rgba(0, 0, 0, 0.95); "
            f"border: 1px solid {border_accent}; "
            f"border-radius: 8px; "
            f"}}"
        )

    # ── Persistent mode ──────────────────────────────────────

    def set_persistent(self, enabled: bool):
        self._persistent = enabled
        if enabled:
            self.show_idle()
            self.show()
        elif self.current_state == "idle":
            super().hide()

    # ── Animations ───────────────────────────────────────────

    def _pulse_dot(self):
        self._dot_visible = not self._dot_visible
        if self._dot_visible:
            color = RED if self.current_state == "recording" else AMBER
            self.status_dot.setStyleSheet(f"background-color: {color}; border-radius: 3px;")
        else:
            self.status_dot.setStyleSheet(f"background-color: transparent; border-radius: 3px;")

    def _animate_dots(self):
        self._dots_count = (self._dots_count + 1) % 4
        dots = "." * self._dots_count + "\u00A0" * (3 - self._dots_count)
        if self.current_state == "recording":
            self.status_label.setText(f"{t('recording')}{dots}")
        elif self.current_state == "processing":
            self.status_label.setText(f"{t('transcribing')}{dots}")

    def _stop_animations(self):
        self._dot_pulse_timer.stop()
        self._dots_timer.stop()
        self.waveform.stop()

    # ── State methods ────────────────────────────────────────

    def show_idle(self):
        self.current_state = "idle"
        self._stop_animations()
        self.status_label.setText(t("ready"))
        self.status_label.setStyleSheet(f"color: {TEXT}; font-size: 10px; font-weight: 600; {LABEL_BASE}")
        self.sub_label.hide()
        self.status_dot.setStyleSheet(f"background-color: {TEXT_DIM}; border-radius: 3px;")
        self._set_card_style()
        self.waveform.hide()

    def show_recording(self):
        self.current_state = "recording"
        self.status_label.setText(t("recording"))
        self.status_label.setStyleSheet(f"color: {TEXT}; font-size: 10px; font-weight: 600; {LABEL_BASE}")
        self.sub_label.hide()
        self.status_dot.setStyleSheet(f"background-color: {RED}; border-radius: 3px;")
        self._set_card_style()
        self.waveform.show()
        self.waveform.start()
        self._dot_pulse_timer.start(500)
        self._dots_timer.start(400)
        self.show()

    def show_processing(self):
        self.current_state = "processing"
        self.status_label.setText(t("transcribing"))
        self.status_label.setStyleSheet(f"color: {TEXT}; font-size: 10px; font-weight: 600; {LABEL_BASE}")
        self.sub_label.hide()
        self.status_dot.setStyleSheet(f"background-color: {AMBER}; border-radius: 3px;")
        self._set_card_style()
        self.waveform.stop()
        self.waveform.hide()
        self._dot_pulse_timer.start(500)
        self._dots_timer.start(400)

    def show_success(self, auto_hide_delay: int = 1500):
        self.current_state = "success"
        self._stop_animations()
        self.status_label.setText(t("copied_to_clipboard"))
        self.status_label.setStyleSheet(f"color: {GREEN}; font-size: 10px; font-weight: 600; {LABEL_BASE}")
        self.sub_label.hide()
        self.status_dot.setStyleSheet(f"background-color: {GREEN}; border-radius: 3px;")
        self._set_card_style()
        self.waveform.stop()
        self.waveform.hide()

        if not self._persistent:
            QTimer.singleShot(auto_hide_delay, self._auto_hide)
        else:
            QTimer.singleShot(auto_hide_delay, self.show_idle)

    def show_error(self, message: str = "Error", auto_hide_delay: int = 3000):
        self.current_state = "error"
        self._stop_animations()
        self.status_label.setText(f"{t('error')}: {message}")
        self.status_label.setStyleSheet(f"color: {RED}; font-size: 10px; font-weight: 600; {LABEL_BASE}")
        self.sub_label.hide()
        self.status_dot.setStyleSheet(f"background-color: {RED}; border-radius: 3px;")
        self._set_card_style()
        self.waveform.stop()
        self.waveform.hide()

        if not self._persistent:
            QTimer.singleShot(auto_hide_delay, self._auto_hide)
        else:
            QTimer.singleShot(auto_hide_delay, self.show_idle)

    # ── Hide logic ───────────────────────────────────────────

    def _auto_hide(self):
        if not self._persistent:
            self.hide()

    def hide(self):
        self._stop_animations()
        if self._persistent:
            self.show_idle()
        else:
            super().hide()
