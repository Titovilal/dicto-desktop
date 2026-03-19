"""
Overlay window for visual feedback during recording and processing.
Draggable, optionally persistent, with record/stop button.
"""

import math

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPainter, QColor, QMouseEvent

from src.ui.main_window_styles import (
    MUTED, BORDER, SECONDARY, TEXT, TEXT_DIM, PRIMARY, PRIMARY_FG,
    RED, RED_HOVER, AMBER, GREEN,
    SVG_AUDIO_LINES,
)


class OverlayWaveformWidget(QWidget):
    def __init__(self, color: str = RED, parent=None):
        super().__init__(parent)
        self.bar_count = 12
        self.bar_heights = [0.3] * self.bar_count
        self.color = color
        self.setFixedSize(48, 16)
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
        total_width = self.bar_count * 4 - 2
        start_x = (self.width() - total_width) // 2
        max_h = self.height()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(self.color))
        for i in range(self.bar_count):
            h = max(2, int(self.bar_heights[i] * max_h))
            x = start_x + i * 4
            y = (max_h - h) // 2
            painter.drawRoundedRect(x, y, 2, h, 1, 1)
        painter.end()


FONT = '"JetBrains Mono", "Cascadia Code", "Consolas", monospace'
LABEL_BASE = f"font-family: {FONT}; background: transparent; letter-spacing: -0.5px;"

OVERLAY_BTN = f"""
    QPushButton {{
        background-color: {PRIMARY};
        border: none;
        border-radius: 4px;
        color: {PRIMARY_FG};
        font-family: {FONT};
        font-size: 11px;
        font-weight: 600;
        padding: 4px 10px;
    }}
    QPushButton:hover {{
        background-color: rgba(244, 244, 245, 0.8);
    }}
"""

OVERLAY_BTN_RECORDING = f"""
    QPushButton {{
        background-color: {RED};
        border: none;
        border-radius: 4px;
        color: white;
        font-family: {FONT};
        font-size: 11px;
        font-weight: 600;
        padding: 4px 10px;
    }}
    QPushButton:hover {{
        background-color: {RED_HOVER};
    }}
"""


class OverlayWindow(QWidget):
    """Draggable overlay with record/stop button. Can stay visible permanently."""

    record_clicked = Signal()
    stop_clicked = Signal()

    def __init__(self, position: str = "top-right", size: int = 100, opacity: float = 0.9):
        super().__init__()
        self.position_name = position
        self.window_opacity = opacity
        self._persistent = False
        self._drag_pos = None

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
        self.setFixedSize(240, 64)
        self._position_window()
        self.hide()

    def _position_window(self):
        from PySide6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        margin = 20
        w, h = self.width(), self.height()
        positions = {
            "top-left": (margin, margin),
            "top-right": (screen.width() - w - margin, margin),
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

        card_layout = QHBoxLayout(self.card)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(8)

        # Status dot
        self.status_dot = QWidget()
        self.status_dot.setFixedSize(8, 8)
        self.status_dot.setStyleSheet(f"background-color: {TEXT_DIM}; border-radius: 4px;")
        card_layout.addWidget(self.status_dot, 0, Qt.AlignmentFlag.AlignVCenter)

        # Text column
        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(1)

        self.status_label = QLabel("Listo")
        self.status_label.setStyleSheet(f"color: {TEXT}; font-size: 13px; font-weight: 600; {LABEL_BASE}")
        text_col.addWidget(self.status_label)

        self.sub_label = QLabel("")
        self.sub_label.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; {LABEL_BASE}")
        self.sub_label.hide()
        text_col.addWidget(self.sub_label)

        card_layout.addLayout(text_col, 1)

        # Waveform
        self.waveform = OverlayWaveformWidget(RED)
        self.waveform.hide()
        card_layout.addWidget(self.waveform, 0, Qt.AlignmentFlag.AlignVCenter)

        # Record/stop button
        self.action_button = QPushButton("Grabar")
        self.action_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.action_button.setFixedHeight(26)
        self.action_button.setStyleSheet(OVERLAY_BTN)
        self.action_button.clicked.connect(self._on_action_clicked)
        card_layout.addWidget(self.action_button, 0, Qt.AlignmentFlag.AlignVCenter)

        main_layout.addWidget(self.card)

    def _set_card_style(self, border_accent: str = BORDER):
        self.card.setStyleSheet(
            f"QWidget#overlayCard {{ "
            f"background-color: {MUTED}; "
            f"border: 1px solid {border_accent}; "
            f"border-radius: 12px; "
            f"}}"
        )

    # ── Dragging ─────────────────────────────────────────────

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = None

    # ── Persistent mode ──────────────────────────────────────

    def set_persistent(self, enabled: bool):
        self._persistent = enabled
        if enabled:
            self.show_idle()
            self.show()
        elif self.current_state == "idle":
            super().hide()

    # ── Button action ────────────────────────────────────────

    def _on_action_clicked(self):
        if self.current_state == "recording":
            self.stop_clicked.emit()
        elif self.current_state in ("idle", "success"):
            self.record_clicked.emit()

    # ── Animations ───────────────────────────────────────────

    def _pulse_dot(self):
        self._dot_visible = not self._dot_visible
        if self._dot_visible:
            color = RED if self.current_state == "recording" else AMBER
            self.status_dot.setStyleSheet(f"background-color: {color}; border-radius: 4px;")
        else:
            self.status_dot.setStyleSheet(f"background-color: transparent; border-radius: 4px;")

    def _animate_dots(self):
        self._dots_count = (self._dots_count + 1) % 4
        dots = "." * self._dots_count + "\u00A0" * (3 - self._dots_count)
        if self.current_state == "recording":
            self.status_label.setText(f"Grabando{dots}")
        elif self.current_state == "processing":
            self.status_label.setText(f"Transcribiendo{dots}")

    def _stop_animations(self):
        self._dot_pulse_timer.stop()
        self._dots_timer.stop()
        self.waveform.stop()

    # ── State methods ────────────────────────────────────────

    def show_idle(self):
        self.current_state = "idle"
        self._stop_animations()
        self.status_label.setText("Listo")
        self.status_label.setStyleSheet(f"color: {TEXT}; font-size: 13px; font-weight: 600; {LABEL_BASE}")
        self.sub_label.hide()
        self.status_dot.setStyleSheet(f"background-color: {TEXT_DIM}; border-radius: 4px;")
        self._set_card_style()
        self.waveform.hide()
        self.action_button.setText("Grabar")
        self.action_button.setStyleSheet(OVERLAY_BTN)
        self.action_button.show()

    def show_recording(self):
        self.current_state = "recording"
        self.status_label.setText("Grabando")
        self.status_label.setStyleSheet(f"color: {TEXT}; font-size: 13px; font-weight: 600; {LABEL_BASE}")
        self.sub_label.setText("Suelta para transcribir")
        self.sub_label.show()
        self.status_dot.setStyleSheet(f"background-color: {RED}; border-radius: 4px;")
        self._set_card_style()
        self.waveform.show()
        self.waveform.start()
        self._dot_pulse_timer.start(500)
        self._dots_timer.start(400)
        self.action_button.setText("Detener")
        self.action_button.setStyleSheet(OVERLAY_BTN_RECORDING)
        self.action_button.show()
        self.show()

    def show_processing(self):
        self.current_state = "processing"
        self.status_label.setText("Transcribiendo")
        self.status_label.setStyleSheet(f"color: {TEXT}; font-size: 13px; font-weight: 600; {LABEL_BASE}")
        self.sub_label.setText("Procesando audio...")
        self.sub_label.show()
        self.status_dot.setStyleSheet(f"background-color: {AMBER}; border-radius: 4px;")
        self._set_card_style()
        self.waveform.stop()
        self.waveform.hide()
        self._dot_pulse_timer.start(500)
        self._dots_timer.start(400)
        self.action_button.hide()

    def show_success(self, auto_hide_delay: int = 1500):
        self.current_state = "success"
        self._stop_animations()
        self.status_label.setText("Copiado al portapapeles")
        self.status_label.setStyleSheet(f"color: {GREEN}; font-size: 13px; font-weight: 600; {LABEL_BASE}")
        self.sub_label.hide()
        self.status_dot.setStyleSheet(f"background-color: {GREEN}; border-radius: 4px;")
        self._set_card_style()
        self.waveform.stop()
        self.waveform.hide()
        self.action_button.setText("Grabar")
        self.action_button.setStyleSheet(OVERLAY_BTN)
        self.action_button.show()

        if not self._persistent:
            QTimer.singleShot(auto_hide_delay, self._auto_hide)
        else:
            QTimer.singleShot(auto_hide_delay, self.show_idle)

    def show_error(self, message: str = "Error", auto_hide_delay: int = 3000):
        self.current_state = "error"
        self._stop_animations()
        self.status_label.setText("Error")
        self.status_label.setStyleSheet(f"color: {RED}; font-size: 13px; font-weight: 600; {LABEL_BASE}")
        self.sub_label.setText(message)
        self.sub_label.show()
        self.status_dot.setStyleSheet(f"background-color: {RED}; border-radius: 4px;")
        self._set_card_style()
        self.waveform.stop()
        self.waveform.hide()
        self.action_button.hide()

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
