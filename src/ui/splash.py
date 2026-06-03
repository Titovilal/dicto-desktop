"""
Splash window displayed while application loads.
Matches the overlay/main window aesthetic: dark zinc theme, JetBrains Mono, waveform animation.
"""

import math

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QFont

from src.i18n import t
from src.ui.main_window_styles import (
    BG,
    BORDER,
    TEXT,
    TEXT_DIM,
    PRIMARY,
    FONT,
)


class _MiniWaveform(QWidget):
    """Small animated waveform (pulse mode) for the splash screen."""

    BAR_COUNT = 12
    BAR_W = 3
    BAR_GAP = 2

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(
            self.BAR_COUNT * (self.BAR_W + self.BAR_GAP) - self.BAR_GAP, 20
        )
        self._tick = 0
        self._heights = [0.0] * self.BAR_COUNT
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update)
        self._timer.start(50)

    def _update(self):
        self._tick += 1
        center = self.BAR_COUNT / 2
        for i in range(self.BAR_COUNT):
            dist = abs(i - center) / center
            phase = self._tick * 0.22 - dist * 2.8
            self._heights[i] = 0.12 + 0.88 * max(0.0, math.sin(phase)) ** 2
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(PRIMARY))
        step = self.BAR_W + self.BAR_GAP
        max_h = self.height()
        for i in range(self.BAR_COUNT):
            h = max(2, int(self._heights[i] * max_h))
            x = i * step
            y = (max_h - h) // 2
            painter.drawRoundedRect(x, y, self.BAR_W, h, 1, 1)
        painter.end()

    def stop(self):
        self._timer.stop()


class SplashWindow(QWidget):
    """Frameless, centered splash window shown during app startup."""

    def __init__(self):
        super().__init__()
        self._setup_window()
        self._setup_ui()

    def _setup_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(200, 80)
        self._center_on_screen()

    def _center_on_screen(self):
        from PySide6.QtWidgets import QApplication

        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Loading label
        self.label = QLabel(t("loading"))
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet(
            f"color: {TEXT}; font-size: 12px; font-weight: 600;"
            f" font-family: {FONT}; background: transparent;"
            " letter-spacing: -0.5px;"
        )
        layout.addWidget(self.label)

        # Waveform row — centered
        wf_row = QHBoxLayout()
        wf_row.setContentsMargins(0, 0, 0, 0)
        wf_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._waveform = _MiniWaveform()
        wf_row.addWidget(self._waveform)
        layout.addLayout(wf_row)

    def paintEvent(self, event):
        """Draw a rounded card matching the overlay style."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background fill
        painter.setBrush(QColor(BG))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 10, 10)

        # Border
        from PySide6.QtGui import QPen
        pen = QPen(QColor(BORDER))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        # Inset by 0.5px so the border sits inside the rounded rect
        r = self.rect().adjusted(1, 1, -1, -1)
        painter.drawRoundedRect(r, 10, 10)

        painter.end()

    def close(self):
        self._waveform.stop()
        super().close()
