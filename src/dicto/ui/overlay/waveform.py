"""Animated waveform bars — token-coloured, used by the overlay and mic test.

Colour comes from a theme ``Token`` (re-painted on theme change). Modes:
``live`` (bars scroll as ``set_level`` pushes RMS), ``pulse`` (transcribing),
``settle`` (success flourish). Holds no audio, only the last ``bar_count`` levels.
"""

from __future__ import annotations

import math
from collections import deque

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget

from dicto.ui.theme.manager import ThemeManager
from dicto.ui.theme.tokens import Token


class WaveformWidget(QWidget):
    """Animated bars whose colour follows a theme token."""

    def __init__(
        self,
        theme: ThemeManager,
        *,
        token: Token = Token.STATUS_RECORDING,
        bar_count: int = 18,
        bar_width: int = 2,
        bar_gap: int = 2,
        height: int = 16,
        fixed_width: int | None = None,
        mode: str = "live",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._theme = theme
        self._token = token
        self.bar_count = bar_count
        self.bar_width = bar_width
        self.bar_gap = bar_gap
        self.bar_heights: deque[float] = deque([0.0] * bar_count, maxlen=bar_count)
        self.mode = mode
        self._fixed_width = fixed_width is not None
        self.setFixedHeight(height)
        if fixed_width is not None:
            self.setFixedSize(fixed_width, height)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_bars)
        self._tick = 0

        # Re-paint when the theme flips so the colour stays correct.
        self._theme.themeChanged.connect(self._on_theme_changed)

    # ── colour ──────────────────────────────────────────────────────────

    def set_token(self, token: Token) -> None:
        self._token = token
        self.update()

    def _color(self) -> str:
        return self._theme.color(self._token)

    def _on_theme_changed(self, _effective: str) -> None:
        self.update()

    # ── feed / control ──────────────────────────────────────────────────

    def set_level(self, level: float) -> None:
        """Push a new audio level (0..1); bars scroll left (live mode)."""
        self.bar_heights.append(max(0.0, min(1.0, level)))
        self.update()

    def start(self) -> None:
        self._tick = 0
        self.bar_heights.clear()
        for _ in range(self.bar_count):
            self.bar_heights.append(0.0)
        if self.mode == "live":
            self.update()
            return
        self.update()
        self._timer.start(50)

    def stop(self) -> None:
        self._timer.stop()

    def clear(self) -> None:
        self._timer.stop()
        self.bar_heights.clear()
        for _ in range(self.bar_count):
            self.bar_heights.append(0.0)
        self.update()

    # ── animation ───────────────────────────────────────────────────────

    def _update_bars(self) -> None:
        self._tick += 1
        if self.mode == "live":
            return
        if self.mode == "pulse":
            center = self.bar_count / 2
            for i in range(self.bar_count):
                dist = abs(i - center) / center
                phase = self._tick * 0.2 - dist * 3.0
                self.bar_heights[i] = 0.15 + 0.85 * max(0.0, math.sin(phase)) ** 2
        elif self.mode == "settle":
            progress = self._tick * 0.15
            center = self.bar_count / 2
            for i in range(self.bar_count):
                dist = abs(i - center) / max(1, center)
                t = max(0.0, progress - dist * 0.6)
                if t <= 0:
                    self.bar_heights[i] = 0.0
                else:
                    rise = 1.0 - math.exp(-t * 4.0)
                    bounce = math.sin(t * 5.0) * math.exp(-t * 2.0) * 0.35
                    fade = max(0.0, 1.0 - max(0.0, progress - 1.5) * 0.6)
                    self.bar_heights[i] = max(0.0, (rise + bounce) * 0.7 * fade)
            if progress > 3.2:
                self.clear()
                return
        else:  # "wave"
            for i in range(self.bar_count):
                phase = i * 0.7 + self._tick * 0.15
                self.bar_heights[i] = 0.2 + 0.8 * abs(math.sin(phase))
        self.update()

    def _ensure_bar_count(self) -> None:
        step = self.bar_width + self.bar_gap
        count = max(1, (self.width() + self.bar_gap) // step)
        if count != self.bar_count:
            self.bar_count = count
            self.bar_heights = deque([0.0] * count, maxlen=count)

    def resizeEvent(self, event) -> None:  # noqa: N802, ANN001 — Qt override
        super().resizeEvent(event)
        if not self._fixed_width:
            self._ensure_bar_count()

    def paintEvent(self, event) -> None:  # noqa: N802, ANN001 — Qt override
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        step = self.bar_width + self.bar_gap
        total_width = self.bar_count * step - self.bar_gap
        start_x = (self.width() - total_width) // 2
        max_h = self.height()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(self._color()))
        floor = max(1, self.bar_width // 2 + 1)
        for i in range(self.bar_count):
            h = max(floor, int(self.bar_heights[i] * max_h))
            x = start_x + i * step
            y = (max_h - h) // 2
            painter.drawRoundedRect(x, y, self.bar_width, h, 1, 1)
        painter.end()
