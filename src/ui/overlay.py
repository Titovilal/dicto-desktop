"""
Overlay window for visual feedback during recording and processing.
Includes a settings button (idle) that opens a popover, and a record/stop button.
Draggable by clicking and dragging anywhere on the card.
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QStackedWidget,
    QPushButton,
)
from PySide6.QtCore import Qt, QTimer, QPoint, Signal

from src.i18n import t
from src.ui.main_window_styles import (
    BG,
    BORDER,
    TEXT,
    TEXT_DIM,
    SECONDARY,
    RED,
    AMBER,
    GREEN,
    BLUE,
)
from src.ui.waveform import WaveformWidget
from src.ui.icons import SVG_SETTINGS_SMALL, SVG_RECORD, SVG_STOP, SVG_RESET


FONT = '"JetBrains Mono", "Cascadia Code", "Consolas", monospace'
LABEL_BASE = f"font-family: {FONT}; background: transparent; letter-spacing: -0.5px;"

# Button styles
_BTN_BASE = (
    "background: transparent; border: none; border-radius: 4px; padding: 2px;"
    f" font-family: {FONT};"
)
_BTN_HOVER = f"background: {SECONDARY};"


def _make_overlay_icon(svg: str, size: int, color: str):
    from PySide6.QtSvg import QSvgRenderer
    from PySide6.QtGui import QPixmap, QPainter, QColor, QIcon
    from PySide6.QtCore import QSize

    colored = svg.replace("currentColor", color)
    renderer = QSvgRenderer(colored.encode())
    px = QPixmap(QSize(size * 2, size * 2))
    px.fill(QColor(0, 0, 0, 0))
    painter = QPainter(px)
    renderer.render(painter)
    painter.end()
    px.setDevicePixelRatio(2)
    icon = QIcon()
    icon.addPixmap(px)
    return icon


class OverlayPopover(QWidget):
    """Small popover shown when clicking the settings button."""

    reset_position_clicked = Signal()
    record_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        container = QWidget()
        container.setObjectName("popoverCard")
        container.setStyleSheet(
            f"QWidget#popoverCard {{ background-color: {BG}; border: 1px solid {BORDER}; border-radius: 6px; }}"
        )
        clayout = QVBoxLayout(container)
        clayout.setContentsMargins(4, 4, 4, 4)
        clayout.setSpacing(2)

        # Reset position button
        self.reset_btn = QPushButton(t("reset_position"))
        self.reset_btn.setIcon(_make_overlay_icon(SVG_RESET, 12, TEXT_DIM))
        self.reset_btn.setStyleSheet(
            f"QPushButton {{ {_BTN_BASE} color: {TEXT}; font-size: 11px; padding: 4px 8px; text-align: left; }}"
            f"QPushButton:hover {{ {_BTN_HOVER} }}"
        )
        self.reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_btn.clicked.connect(self._on_reset)
        clayout.addWidget(self.reset_btn)

        # Record button
        self.record_btn = QPushButton(t("record"))
        self.record_btn.setIcon(_make_overlay_icon(SVG_RECORD, 12, RED))
        self.record_btn.setStyleSheet(
            f"QPushButton {{ {_BTN_BASE} color: {TEXT}; font-size: 11px; padding: 4px 8px; text-align: left; }}"
            f"QPushButton:hover {{ {_BTN_HOVER} }}"
        )
        self.record_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.record_btn.clicked.connect(self._on_record)
        clayout.addWidget(self.record_btn)

        layout.addWidget(container)
        self.adjustSize()

    def _on_reset(self):
        self.hide()
        self.reset_position_clicked.emit()

    def _on_record(self):
        self.hide()
        self.record_clicked.emit()


class OverlayWindow(QWidget):
    """Fixed overlay showing status. Draggable, with settings/record/stop buttons."""

    record_requested = Signal()
    stop_requested = Signal()

    def __init__(
        self, position: str = "top-right", size: int = 100, opacity: float = 0.85
    ):
        super().__init__()
        self.position_name = "top-right"
        self.window_opacity = opacity
        self._persistent = False

        self._dots_count = 0
        self._dots_timer = QTimer(self)
        self._dots_timer.timeout.connect(self._animate_dots)

        self._dot_visible = True
        self._dot_pulse_timer = QTimer(self)
        self._dot_pulse_timer.timeout.connect(self._pulse_dot)

        # Drag state
        self._drag_active = False
        self._drag_offset = QPoint()

        # Popover (must exist before _setup_window which calls hide())
        self._popover = OverlayPopover()
        self._setup_ui()
        self._setup_window()
        self._popover.reset_position_clicked.connect(self._reset_position)
        self._popover.record_clicked.connect(self._on_popover_record)
        self._popover.hide()

    # ── Window setup ─────────────────────────────────────────

    def _setup_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        self.setFixedSize(170, 60)
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

    def _reset_position(self):
        self._position_window()

    # ── Dragging ──────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_active = True
            self._drag_offset = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_active and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            # Reposition popover if visible
            if self._popover.isVisible():
                self._show_popover_at_button()
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_active = False
        event.accept()

    # ── UI ───────────────────────────────────────────────────

    def _setup_ui(self):
        self.current_state = "idle"

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.card = QWidget()
        self.card.setObjectName("overlayCard")
        self._set_card_style()

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(0, 6, 0, 6)
        card_layout.setSpacing(4)

        # Status row (dot + label + action button)
        status_row = QHBoxLayout()
        status_row.setContentsMargins(8, 0, 6, 0)
        status_row.setSpacing(5)

        self.status_dot = QWidget()
        self.status_dot.setFixedSize(6, 6)
        self.status_dot.setStyleSheet(
            f"background-color: {TEXT_DIM}; border-radius: 3px;"
        )
        status_row.addWidget(self.status_dot, 0, Qt.AlignmentFlag.AlignVCenter)

        self.status_label = QLabel(t("ready"))
        self.status_label.setStyleSheet(
            f"color: {TEXT}; font-size: 12px; font-weight: 600; {LABEL_BASE}"
        )
        status_row.addWidget(self.status_label, 1)

        # Action button: settings (idle) / stop (recording/editing)
        self.action_btn = QPushButton()
        self.action_btn.setFixedSize(22, 22)
        self.action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.action_btn.setStyleSheet(
            f"QPushButton {{ {_BTN_BASE} }}QPushButton:hover {{ {_BTN_HOVER} }}"
        )
        self.action_btn.clicked.connect(self._on_action_btn_clicked)
        self._action_mode = "settings"  # "settings" or "stop"
        self._update_action_btn_icon()
        status_row.addWidget(self.action_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        card_layout.addLayout(status_row)

        # Waveform area
        self.icon_stack = QStackedWidget()
        self.icon_stack.setFixedHeight(18)
        self.waveform_recording = WaveformWidget(
            bar_width=2, bar_gap=1, height=16, color=RED, mode="live"
        )
        self.waveform_processing = WaveformWidget(
            bar_width=2, bar_gap=1, height=16, color=AMBER, mode="pulse"
        )
        self.waveform_success = WaveformWidget(
            bar_width=2, bar_gap=1, height=16, color=GREEN, mode="settle"
        )
        self.waveform_editing = WaveformWidget(
            bar_width=2, bar_gap=1, height=16, color=BLUE, mode="live"
        )
        self.icon_stack.addWidget(self.waveform_recording)  # index 0
        self.icon_stack.addWidget(self.waveform_processing)  # index 1
        self.icon_stack.addWidget(self.waveform_success)  # index 2
        self.icon_stack.addWidget(self.waveform_editing)  # index 3
        self.icon_stack.setCurrentIndex(0)
        self.icon_stack.hide()
        card_layout.addWidget(self.icon_stack)

        # Hidden sub_label kept for error messages only
        self.sub_label = QLabel("")
        self.sub_label.hide()

        main_layout.addWidget(self.card)

    def _update_action_btn_icon(self):
        if self._action_mode == "settings":
            self.action_btn.setIcon(
                _make_overlay_icon(SVG_SETTINGS_SMALL, 14, TEXT_DIM)
            )
        else:
            self.action_btn.setIcon(_make_overlay_icon(SVG_STOP, 14, RED))

    def _on_action_btn_clicked(self):
        if self._action_mode == "settings":
            if self._popover.isVisible():
                self._popover.hide()
            else:
                self._show_popover_at_button()
        else:
            # Stop mode
            self.stop_requested.emit()

    def _show_popover_at_button(self):
        self._popover.adjustSize()
        # Position popover below the overlay
        pos = self.mapToGlobal(
            QPoint(self.width() - self._popover.width(), self.height() + 4)
        )
        self._popover.move(pos)
        self._popover.show()
        self._popover.raise_()

    def _on_popover_record(self):
        self.record_requested.emit()

    def _set_action_mode(self, mode: str):
        self._action_mode = mode
        self._update_action_btn_icon()
        # Hide popover when switching away from settings
        if mode != "settings" and self._popover.isVisible():
            self._popover.hide()

    def _set_card_style(self, border_accent: str = BORDER):
        self.card.setStyleSheet(
            f"QWidget#overlayCard {{ "
            f"background-color: {BG}; "
            f"border: 1px solid {border_accent}; "
            "border-radius: 8px; "
            "}"
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
            color = (
                RED
                if self.current_state == "recording"
                else BLUE
                if self.current_state == "editing"
                else AMBER
            )
            self.status_dot.setStyleSheet(
                f"background-color: {color}; border-radius: 3px;"
            )
        else:
            self.status_dot.setStyleSheet(
                "background-color: transparent; border-radius: 3px;"
            )

    def _animate_dots(self):
        self._dots_count = (self._dots_count + 1) % 4
        dots = "." * self._dots_count + "\u00a0" * (3 - self._dots_count)
        if self.current_state == "recording":
            self.status_label.setText(f"{t('recording')}{dots}")
        elif self.current_state == "processing":
            self.status_label.setText(f"{t('processing')}{dots}")
        elif self.current_state == "editing":
            self.status_label.setText(f"{self._editing_label}{dots}")

    def _stop_animations(self):
        self._dot_pulse_timer.stop()
        self._dots_timer.stop()
        self.waveform_recording.stop()
        self.waveform_processing.stop()
        self.waveform_success.stop()
        self.waveform_editing.stop()

    def _show_icon(self, index: int):
        self.icon_stack.setCurrentIndex(index)
        self.icon_stack.show()

    def _hide_icon(self):
        self.icon_stack.hide()

    # ── State methods ────────────────────────────────────────

    def show_idle(self):
        self.current_state = "idle"
        self._stop_animations()
        self.status_label.setText(t("ready"))
        self.status_label.setStyleSheet(
            f"color: {TEXT}; font-size: 12px; font-weight: 600; {LABEL_BASE}"
        )
        self.sub_label.hide()
        self.status_dot.setStyleSheet(
            f"background-color: {TEXT_DIM}; border-radius: 3px;"
        )
        self._set_card_style()
        self._hide_icon()
        self._set_action_mode("settings")

    def show_recording(self):
        self.current_state = "recording"
        self.status_label.setText(t("recording"))
        self.status_label.setStyleSheet(
            f"color: {TEXT}; font-size: 12px; font-weight: 600; {LABEL_BASE}"
        )
        self.sub_label.hide()
        self.status_dot.setStyleSheet(f"background-color: {RED}; border-radius: 3px;")
        self._set_card_style()
        self._show_icon(0)
        self.waveform_recording.start()
        self._dot_pulse_timer.start(500)
        self._dots_timer.start(400)
        self._set_action_mode("stop")
        self.show()

    def show_editing(self, recording: bool = True):
        self.current_state = "editing"
        self._editing_label = t("recording") if recording else t("editing")
        self.status_label.setText(self._editing_label)
        self.status_label.setStyleSheet(
            f"color: {TEXT}; font-size: 12px; font-weight: 600; {LABEL_BASE}"
        )
        self.sub_label.hide()
        self.status_dot.setStyleSheet(f"background-color: {BLUE}; border-radius: 3px;")
        self._set_card_style()
        self._show_icon(3)
        self.waveform_editing.start()
        self._dot_pulse_timer.start(500)
        self._dots_timer.start(400)
        self._set_action_mode("stop")
        self.show()

    def show_processing(self):
        self.current_state = "processing"
        self.status_label.setText(t("processing"))
        self.status_label.setStyleSheet(
            f"color: {TEXT}; font-size: 12px; font-weight: 600; {LABEL_BASE}"
        )
        self.sub_label.hide()
        self.status_dot.setStyleSheet(f"background-color: {AMBER}; border-radius: 3px;")
        self._set_card_style()
        self.waveform_recording.stop()
        self._show_icon(1)
        self.waveform_processing.start()
        self._dot_pulse_timer.start(500)
        self._dots_timer.start(400)
        self._set_action_mode("stop")

    def show_success(self, auto_hide_delay: int = 1500):
        self.current_state = "success"
        self._stop_animations()
        self.status_label.setText(t("copied_to_clipboard").upper())
        self.status_label.setStyleSheet(
            f"color: {GREEN}; font-size: 12px; font-weight: 600; {LABEL_BASE}"
        )
        self.sub_label.hide()
        self.status_dot.setStyleSheet(f"background-color: {GREEN}; border-radius: 3px;")
        self._set_card_style()
        self._show_icon(2)
        self.waveform_success.start()
        self._set_action_mode("settings")

        if not self._persistent:
            QTimer.singleShot(auto_hide_delay, self._auto_hide)
        else:
            QTimer.singleShot(auto_hide_delay, self.show_idle)

    def show_error(self, message: str = "Error", auto_hide_delay: int = 3000):
        self.current_state = "error"
        self._stop_animations()
        self.status_label.setText(f"{t('error')}: {message}")
        self.status_label.setStyleSheet(
            f"color: {RED}; font-size: 12px; font-weight: 600; {LABEL_BASE}"
        )
        self.sub_label.hide()
        self.status_dot.setStyleSheet(f"background-color: {RED}; border-radius: 3px;")
        self._set_card_style()
        self._hide_icon()
        self._set_action_mode("settings")

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
        self._popover.hide()
        if self._persistent:
            self.show_idle()
        else:
            super().hide()

    def close(self):
        self._popover.close()
        super().close()
