"""
Unified waveform visualization widget.
Used by both the main window and the overlay with different parameters.
"""

import math

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor

from src.ui.main_window_styles import RED


class WaveformWidget(QWidget):
    """Animated waveform bars. Configurable bar count, size, and color."""

    def __init__(
        self,
        bar_count: int = 18,
        bar_width: int = 2,
        bar_gap: int = 2,
        height: int = 28,
        color: str = RED,
        fixed_width: int | None = None,
        mode: str = "wave",
        parent=None,
    ):
        super().__init__(parent)
        self.bar_count = bar_count
        self.bar_width = bar_width
        self.bar_gap = bar_gap
        self.bar_heights = [0.3] * bar_count
        self.color = color
        self.mode = mode
        self._fixed_width = fixed_width is not None
        self.setFixedHeight(height)
        if fixed_width is not None:
            self.setFixedSize(fixed_width, height)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_bars)
        self._tick = 0

    def set_level(self, level: float):
        """Push a new audio level (0.0-1.0) into the bar display (scrolling left)."""
        self.bar_heights = self.bar_heights[1:] + [level]
        self.update()

    def start(self):
        self._tick = 0
        if self.mode == "live":
            self.bar_heights = [0.0] * self.bar_count
            return
        self.bar_heights = [0.0] * self.bar_count
        self.update()
        self._timer.start(50)

    def stop(self):
        self._timer.stop()

    def _update_bars(self):
        self._tick += 1

        if self.mode == "live":
            return

        if self.mode == "pulse":
            center = self.bar_count / 2
            for i in range(self.bar_count):
                dist = abs(i - center) / center
                phase = self._tick * 0.2 - dist * 3.0
                self.bar_heights[i] = 0.15 + 0.85 * max(0, math.sin(phase)) ** 2

        elif self.mode == "settle":
            progress = self._tick * 0.06
            center = self.bar_count / 2
            all_done = True
            for i in range(self.bar_count):
                delay = abs(i - center) / max(1, center) * 0.3
                t = max(0.0, progress - delay)
                # Smooth bell curve: rise then fade using a single easing
                val = t * math.exp(1.0 - t) if t > 0 else 0.0
                # Clamp and scale
                self.bar_heights[i] = min(0.4, val * 0.35)
                if self.bar_heights[i] > 0.01:
                    all_done = False
            if all_done and progress > 2.0:
                self.bar_heights = [0.0] * self.bar_count
                self._timer.stop()

        else:  # "wave" (default)
            for i in range(self.bar_count):
                phase = i * 0.7 + self._tick * 0.15
                self.bar_heights[i] = 0.2 + 0.8 * abs(math.sin(phase))

        self.update()

    def _ensure_bar_count(self):
        """Recalculate bar_count to fill the widget width."""
        step = self.bar_width + self.bar_gap
        count = max(1, (self.width() + self.bar_gap) // step)
        if count != self.bar_count:
            self.bar_count = count
            self.bar_heights = [0.3] * count

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self._fixed_width:
            self._ensure_bar_count()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        step = self.bar_width + self.bar_gap
        total_width = self.bar_count * step - self.bar_gap
        start_x = (self.width() - total_width) // 2
        max_h = self.height()

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(self.color))

        for i in range(self.bar_count):
            h = max(max(1, self.bar_width // 2 + 1), int(self.bar_heights[i] * max_h))
            x = start_x + i * step
            y = (max_h - h) // 2
            painter.drawRoundedRect(x, y, self.bar_width, h, 1, 1)

        painter.end()
