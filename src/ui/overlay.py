"""
Overlay window for visual feedback during recording and processing.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QPainter, QColor, QPen


class OverlayWindow(QWidget):
    """Frameless, transparent overlay window showing application state."""

    def __init__(
        self, position: str = "top-right", size: int = 100, opacity: float = 0.9
    ):
        """
        Initialize overlay window.

        Args:
            position: Screen position (top-left, top-right, bottom-left, bottom-right, center)
            size: Window size in pixels
            opacity: Window opacity (0.0 to 1.0)
        """
        super().__init__()

        self.position_name = position
        self.window_size = size
        self.window_opacity = opacity

        # Animation properties
        self._pulse_value = 0.0
        self.pulse_animation = None

        self._setup_window()
        self._setup_ui()

    def _setup_window(self):
        """Configure window properties."""
        # Frameless, always on top, tool window (doesn't appear in taskbar)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )

        # Transparent background
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Don't take focus
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        # Set size
        self.setFixedSize(self.window_size, self.window_size)

        # Set opacity
        self.setWindowOpacity(self.window_opacity)

        # Position window
        self._position_window()

        # Hide by default
        self.hide()

    def _position_window(self):
        """Position window on screen according to configuration."""
        from PySide6.QtWidgets import QApplication

        screen = QApplication.primaryScreen().geometry()
        margin = 20  # Margin from screen edges

        if self.position_name == "top-left":
            x = margin
            y = margin
        elif self.position_name == "top-right":
            x = screen.width() - self.window_size - margin
            y = margin
        elif self.position_name == "bottom-left":
            x = margin
            y = screen.height() - self.window_size - margin
        elif self.position_name == "bottom-right":
            x = screen.width() - self.window_size - margin
            y = screen.height() - self.window_size - margin
        elif self.position_name == "center":
            x = (screen.width() - self.window_size) // 2
            y = (screen.height() - self.window_size) // 2
        else:
            # Default to top-right
            x = screen.width() - self.window_size - margin
            y = margin

        self.move(x, y)

    def _setup_ui(self):
        """Setup UI components."""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 12px;
                font-weight: bold;
                background: transparent;
            }
        """)

        layout.addWidget(self.status_label)
        self.setLayout(layout)

        # Current state
        self.current_state = "idle"

    def paintEvent(self, event):
        """Custom paint event for drawing the overlay."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw based on current state
        if self.current_state == "recording":
            self._draw_recording(painter)
        elif self.current_state == "processing":
            self._draw_processing(painter)
        elif self.current_state == "success":
            self._draw_success(painter)
        elif self.current_state == "error":
            self._draw_error(painter)

    def _draw_recording(self, painter: QPainter):
        """Draw recording state (pulsing red circle)."""
        # Background circle
        bg_color = QColor(40, 40, 40, 200)
        painter.setBrush(bg_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(10, 10, self.window_size - 20, self.window_size - 20)

        # Pulsing red circle in center
        center_x = self.window_size // 2
        center_y = self.window_size // 2
        base_radius = 20
        pulse_radius = base_radius + int(self._pulse_value * 10)

        red_color = QColor(255, 50, 50, 200)
        painter.setBrush(red_color)
        painter.drawEllipse(
            center_x - pulse_radius,
            center_y - pulse_radius,
            pulse_radius * 2,
            pulse_radius * 2,
        )

    def _draw_processing(self, painter: QPainter):
        """Draw processing state (spinner)."""
        # Background circle
        bg_color = QColor(40, 40, 40, 200)
        painter.setBrush(bg_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(10, 10, self.window_size - 20, self.window_size - 20)

        # Spinner arc (simplified - just a circle for now)
        center_x = self.window_size // 2
        center_y = self.window_size // 2
        radius = 25

        blue_color = QColor(50, 150, 255, 200)
        pen = QPen(blue_color, 4)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(
            center_x - radius, center_y - radius, radius * 2, radius * 2
        )

    def _draw_success(self, painter: QPainter):
        """Draw success state (green checkmark)."""
        # Background circle
        bg_color = QColor(40, 40, 40, 200)
        painter.setBrush(bg_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(10, 10, self.window_size - 20, self.window_size - 20)

        # Green circle
        center_x = self.window_size // 2
        center_y = self.window_size // 2
        radius = 30

        green_color = QColor(50, 255, 50, 200)
        painter.setBrush(green_color)
        painter.drawEllipse(
            center_x - radius, center_y - radius, radius * 2, radius * 2
        )

        # Simple checkmark (simplified as "✓" text for now)
        painter.setPen(QColor(255, 255, 255))

    def _draw_error(self, painter: QPainter):
        """Draw error state (red X)."""
        # Background circle
        bg_color = QColor(40, 40, 40, 200)
        painter.setBrush(bg_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(10, 10, self.window_size - 20, self.window_size - 20)

        # Red circle
        center_x = self.window_size // 2
        center_y = self.window_size // 2
        radius = 30

        red_color = QColor(255, 50, 50, 200)
        painter.setBrush(red_color)
        painter.drawEllipse(
            center_x - radius, center_y - radius, radius * 2, radius * 2
        )

        # X mark (simplified)
        painter.setPen(QPen(QColor(255, 255, 255), 3))
        offset = 15
        painter.drawLine(
            center_x - offset, center_y - offset, center_x + offset, center_y + offset
        )
        painter.drawLine(
            center_x + offset, center_y - offset, center_x - offset, center_y + offset
        )

    # Property for pulse animation
    def get_pulse_value(self):
        return self._pulse_value

    def set_pulse_value(self, value):
        self._pulse_value = value
        self.update()  # Trigger repaint

    pulse_value = Property(float, get_pulse_value, set_pulse_value)

    def show_recording(self):
        """Show recording state with pulsing animation."""
        self.current_state = "recording"
        self.status_label.setText("Recording...")
        self.show()

        # Start pulse animation
        self._start_pulse_animation()

    def show_processing(self):
        """Show processing state."""
        self.current_state = "processing"
        self.status_label.setText("Transcribing...")
        self._stop_pulse_animation()
        self.update()

    def show_success(self, auto_hide_delay: int = 1500):
        """
        Show success state.

        Args:
            auto_hide_delay: Milliseconds before auto-hiding
        """
        self.current_state = "success"
        self.status_label.setText("Success!")
        self._stop_pulse_animation()
        self.update()

        # Auto-hide after delay
        QTimer.singleShot(auto_hide_delay, self.hide)

    def show_error(self, message: str = "Error", auto_hide_delay: int = 3000):
        """
        Show error state.

        Args:
            message: Error message to display
            auto_hide_delay: Milliseconds before auto-hiding
        """
        self.current_state = "error"
        self.status_label.setText(message)
        self._stop_pulse_animation()
        self.update()

        # Auto-hide after delay
        QTimer.singleShot(auto_hide_delay, self.hide)

    def _start_pulse_animation(self):
        """Start pulse animation for recording state."""
        if self.pulse_animation:
            self.pulse_animation.stop()

        self.pulse_animation = QPropertyAnimation(self, b"pulse_value")
        self.pulse_animation.setDuration(1000)  # 1 second
        self.pulse_animation.setStartValue(0.0)
        self.pulse_animation.setEndValue(1.0)
        self.pulse_animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        self.pulse_animation.setLoopCount(-1)  # Infinite loop
        self.pulse_animation.start()

    def _stop_pulse_animation(self):
        """Stop pulse animation."""
        if self.pulse_animation:
            self.pulse_animation.stop()
            self.pulse_animation = None

    def hide(self):
        """Override hide to stop animations."""
        self._stop_pulse_animation()
        super().hide()
