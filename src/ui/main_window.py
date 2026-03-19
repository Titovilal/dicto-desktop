"""
Main window for Dicto application.
Redesigned to match the dicto web component aesthetic.
"""

import logging
import math
import os

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QStackedWidget,
    QCheckBox,
    QComboBox,
    QApplication,
    QTextEdit,
    QLineEdit,
    QScrollArea,
)
from PySide6.QtCore import Signal, Slot, Qt, QSize, QUrl, QTimer, QEvent
from PySide6.QtGui import QIcon, QFont, QPainter, QColor, QPixmap, QDesktopServices, QMouseEvent

from src.utils.icons import get_icon_path
from src.ui.main_window_styles import (
    GLOBAL_STYLE,
    DOT_IDLE,
    DOT_RECORDING,
    DOT_PROCESSING,
    DOT_SUCCESS,
    HEADER_BUTTON,
    HEADER_BUTTON_CLOSE,
    HEADER_BUTTON_ACTIVE,
    TAB_BUTTON,
    TAB_BUTTON_ACTIVE,
    TAB_BUTTON_DISABLED,
    CONTENT_TEXT,
    IDLE_TEXT,
    IDLE_TEXT_BOLD,
    RECORDING_LABEL,
    PROCESSING_LABEL,
    TIMER_RECORDING,
    TIMER_PROCESSING,
    RECORD_BUTTON_IDLE,
    RECORD_BUTTON_RECORDING,
    RECORD_BUTTON_PROCESSING,
    FOOTER_TEXT_BUTTON,
    FOOTER_TEXT_BUTTON_SUCCESS,
    SECTION_LABEL,
    SETTINGS_TITLE,
    ICON_BUTTON,
    FLAT_BUTTON,
    ACCENT_BUTTON,
    SEPARATOR,
    SVG_SETTINGS,
    SVG_CLOSE,
    SVG_EXTERNAL,
    SVG_AUDIO_LINES,
    SVG_BACK,
    BG,
    MUTED,
    BORDER,
    TEXT,
    TEXT_DIM,
    RED,
)

logger = logging.getLogger(__name__)


def _make_icon(svg_data: str, size: int, color: str) -> QIcon:
    """Create a QIcon from inline SVG data with a given color."""
    from PySide6.QtSvg import QSvgRenderer
    from PySide6.QtWidgets import QApplication

    scale = 2
    app = QApplication.instance()
    if app:
        screen = app.primaryScreen()
        if screen:
            scale = max(2, int(screen.devicePixelRatio()))

    colored = svg_data.replace("currentColor", color)
    renderer = QSvgRenderer(colored.encode())
    px = QPixmap(QSize(size * scale, size * scale))
    px.fill(QColor(0, 0, 0, 0))
    painter = QPainter(px)
    renderer.render(painter)
    painter.end()
    px.setDevicePixelRatio(scale)
    icon = QIcon()
    icon.addPixmap(px)
    return icon


class WaveformWidget(QWidget):
    """Animated waveform bars for recording state."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.bar_count = 18
        self.bar_heights = [0.3] * self.bar_count
        self.setFixedHeight(28)

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
            phase = (i * 0.7 + self._tick * 0.15)
            self.bar_heights[i] = 0.2 + 0.8 * abs(math.sin(phase))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        total_width = self.bar_count * 4 - 2  # 2px bar + 2px gap
        start_x = (self.width() - total_width) // 2
        max_h = self.height()

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(RED))

        for i in range(self.bar_count):
            h = max(2, int(self.bar_heights[i] * max_h))
            x = start_x + i * 4
            y = (max_h - h) // 2
            painter.drawRoundedRect(x, y, 2, h, 1, 1)

        painter.end()


class MainWindow(QMainWindow):
    """Main application window matching the web component design."""

    LANGUAGES = {
        "auto": "Auto-detect",
        "es": "Español",
        "en": "English",
        "fr": "Français",
        "de": "Deutsch",
        "it": "Italiano",
        "pt": "Português",
        "zh": "中文",
        "ja": "日本語",
        "ko": "한국어",
    }

    FORMAT_INSTRUCTIONS = {
        "email": "Reescribe el siguiente texto como un correo electrónico profesional. Mantén el idioma original del texto.",
        "notes": "Convierte el siguiente texto en notas organizadas con viñetas. Mantén el idioma original del texto.",
        "tweet": "Reescribe el siguiente texto como un post corto para redes sociales. Mantén el idioma original del texto.",
    }

    # Signals
    play_clicked = Signal()
    stop_clicked = Signal()
    copy_clicked = Signal()
    transform_requested = Signal(str, str, str)  # (format_id, text, instructions)
    persistent_overlay_changed = Signal(bool)

    def __init__(self, settings=None):
        super().__init__()
        self.settings = settings
        self.is_recording = False
        self.is_processing = False
        self.last_transcription = ""
        self._drag_pos = None
        self._elapsed_seconds = 0
        self._copied = False
        self._settings_open = False
        self._format_cache: dict[str, str] = {}  # format_id -> transformed text
        self._transforming_format: str | None = None
        self._setup_ui()
        self._load_settings()

        # Elapsed timer
        self._elapsed_timer = QTimer(self)
        self._elapsed_timer.timeout.connect(self._tick_elapsed)

        # Dot pulse timer
        self._dot_visible = True
        self._dot_pulse_timer = QTimer(self)
        self._dot_pulse_timer.timeout.connect(self._pulse_dot)

    def _setup_ui(self):
        self.setWindowTitle("Dicto")
        self.setFixedSize(420, 380)
        self.setStyleSheet(GLOBAL_STYLE)

        # Frameless window with transparent background for rounded corners
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        icon_path = get_icon_path()
        if icon_path:
            self.setWindowIcon(QIcon(str(icon_path)))

        central_widget = QWidget()
        central_widget.setObjectName("centralCard")
        central_widget.setStyleSheet(f"QWidget#centralCard {{ background-color: {MUTED}; border: 1px solid {BORDER}; border-radius: 16px; }}")
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._create_header(main_layout)
        self._create_tabs_bar(main_layout)

        # Content stack
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack, 1)

        self._create_idle_page()
        self._create_recording_page()
        self._create_done_page()
        self._create_settings_page()

        self._create_footer(main_layout)

        # Start on idle
        self.content_stack.setCurrentIndex(0)

    # ── Header ──────────────────────────────────────────────

    def _create_header(self, parent_layout):
        header = QWidget()
        header.setFixedHeight(38)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 0, 8, 0)
        layout.setSpacing(8)

        # Status dot
        self.status_dot = QWidget()
        self.status_dot.setFixedSize(8, 8)
        self.status_dot.setStyleSheet(DOT_IDLE)
        layout.addWidget(self.status_dot)

        # Title
        title = QLabel("dicto")
        title.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {TEXT}; letter-spacing: -0.5px;")
        layout.addWidget(title)

        layout.addStretch()

        # Timer label (hidden by default)
        self.timer_label = QLabel("")
        self.timer_label.setStyleSheet(TIMER_RECORDING)
        self.timer_label.hide()
        layout.addWidget(self.timer_label)

        # Web button
        web_btn = QPushButton()
        web_btn.setFixedSize(28, 28)
        web_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        web_btn.setIcon(_make_icon(SVG_EXTERNAL, 16, TEXT_DIM))
        web_btn.setIconSize(QSize(16, 16))
        web_btn.setStyleSheet(HEADER_BUTTON)
        web_btn.setToolTip("Ir a la web")
        web_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(os.environ.get("DICTO_WEB_URL", "https://app.dicto.io"))))
        web_btn._icon_normal = _make_icon(SVG_EXTERNAL, 16, TEXT_DIM)
        web_btn._icon_hover = _make_icon(SVG_EXTERNAL, 16, TEXT)
        web_btn.installEventFilter(self)
        layout.addWidget(web_btn)

        # Settings button
        self.settings_button = QPushButton()
        self.settings_button.setFixedSize(28, 28)
        self.settings_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_button.setIcon(_make_icon(SVG_SETTINGS, 16, TEXT_DIM))
        self.settings_button.setIconSize(QSize(16, 16))
        self.settings_button.setStyleSheet(HEADER_BUTTON)
        self.settings_button.setToolTip("Ajustes")
        self.settings_button.clicked.connect(self._toggle_settings)
        layout.addWidget(self.settings_button)

        # Close button
        close_btn = QPushButton()
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setIcon(_make_icon(SVG_CLOSE, 16, TEXT_DIM))
        close_btn.setIconSize(QSize(16, 16))
        close_btn.setStyleSheet(HEADER_BUTTON_CLOSE)
        close_btn.setToolTip("Cerrar")
        close_btn.clicked.connect(self.close)
        close_btn._icon_normal = _make_icon(SVG_CLOSE, 16, TEXT_DIM)
        close_btn._icon_hover = _make_icon(SVG_CLOSE, 16, RED)
        close_btn.installEventFilter(self)
        layout.addWidget(close_btn)

        parent_layout.addWidget(header)

        # Separator line
        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {BORDER};")
        parent_layout.addWidget(sep)

    # ── Format Tabs ─────────────────────────────────────────

    def _create_tabs_bar(self, parent_layout):
        self.tabs_bar = QWidget()
        self.tabs_bar.setFixedHeight(32)

        layout = QHBoxLayout(self.tabs_bar)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(4)

        self.format_tabs = []
        formats = [("raw", "Original"), ("email", "Correo"), ("notes", "Notas"), ("tweet", "Post")]
        for fid, label in formats:
            btn = QPushButton(label)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(TAB_BUTTON_ACTIVE if fid == "raw" else TAB_BUTTON_DISABLED)
            btn.setProperty("format_id", fid)
            btn.clicked.connect(lambda checked, b=btn: self._on_format_clicked(b))
            self.format_tabs.append(btn)
            layout.addWidget(btn)

        layout.addStretch()
        parent_layout.addWidget(self.tabs_bar)

        # Separator line
        self.tabs_sep = QWidget()
        self.tabs_sep.setFixedHeight(1)
        self.tabs_sep.setStyleSheet(f"background-color: {BORDER};")
        parent_layout.addWidget(self.tabs_sep)

        self._active_format = "raw"

    def _update_tabs_enabled(self, enabled: bool):
        for btn in self.format_tabs:
            fid = btn.property("format_id")
            if fid == self._active_format:
                btn.setStyleSheet(TAB_BUTTON_ACTIVE)
            elif enabled:
                btn.setStyleSheet(TAB_BUTTON)
            else:
                btn.setStyleSheet(TAB_BUTTON_DISABLED)

    def _on_format_clicked(self, btn):
        fid = btn.property("format_id")
        if fid == self._active_format:
            return
        self._active_format = fid
        self._update_tabs_enabled(True)

        if not self.last_transcription:
            return

        if fid == "raw":
            self.transcription_text.setText(self.last_transcription)
            self.copy_button.show()
            return

        # Check cache
        if fid in self._format_cache:
            self.transcription_text.setText(self._format_cache[fid])
            self.copy_button.show()
            return

        # Request transform
        self._transforming_format = fid
        self.transcription_text.setText("")
        self.processing_label.setText("TRANSFORMANDO")
        self.processing_label.show()
        self.copy_button.hide()

        instructions = self.FORMAT_INSTRUCTIONS.get(fid, "")
        self.transform_requested.emit(fid, self.last_transcription, instructions)

    @Slot(str, str)
    def on_transform_completed(self, format_id: str, text: str):
        self._format_cache[format_id] = text
        self._transforming_format = None
        if self._active_format == format_id:
            self.processing_label.hide()
            self.transcription_text.setText(text)
            self.copy_button.show()

    @Slot(str, str)
    def on_transform_failed(self, format_id: str, error: str):
        self._transforming_format = None
        if self._active_format == format_id:
            self.processing_label.hide()
            self.transcription_text.setText(f"Error: {error}")
            self.copy_button.hide()

    # ── Idle Page ───────────────────────────────────────────

    def _create_idle_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Icon circle
        icon_container = QWidget()
        icon_container.setFixedSize(28, 28)
        icon_container.setStyleSheet(f"border: 1px solid {BORDER}; border-radius: 14px;")
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(5, 5, 5, 5)
        icon_label = QLabel()
        icon_label.setPixmap(_make_icon(SVG_AUDIO_LINES, 16, TEXT_DIM).pixmap(16, 16))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_layout.addWidget(icon_label)
        layout.addWidget(icon_container, 0, Qt.AlignmentFlag.AlignCenter)

        layout.addSpacing(8)

        # Text
        text_widget = QWidget()
        text_layout = QHBoxLayout(text_widget)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(0)
        text_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl1 = QLabel("Pulsa ")
        lbl1.setStyleSheet(IDLE_TEXT)
        text_layout.addWidget(lbl1)

        lbl2 = QLabel("Grabar")
        lbl2.setStyleSheet(IDLE_TEXT_BOLD)
        text_layout.addWidget(lbl2)

        lbl3 = QLabel(" para comenzar")
        lbl3.setStyleSheet(IDLE_TEXT)
        text_layout.addWidget(lbl3)

        layout.addWidget(text_widget)
        self.content_stack.addWidget(page)

    # ── Recording Page ──────────────────────────────────────

    def _create_recording_page(self):
        page = QWidget()
        page.setStyleSheet("")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 16, 16, 16)

        self.recording_label = QLabel("ESCUCHANDO")
        self.recording_label.setStyleSheet(RECORDING_LABEL)
        layout.addWidget(self.recording_label)

        # Animated dots timer
        self._dots_count = 0
        self._dots_timer = QTimer(self)
        self._dots_timer.timeout.connect(self._animate_dots)

        layout.addStretch()

        self.waveform = WaveformWidget()
        layout.addWidget(self.waveform, 0, Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()
        self.content_stack.addWidget(page)

    def _animate_dots(self):
        self._dots_count = (self._dots_count + 1) % 4
        dots = "." * self._dots_count + "\u00A0" * (3 - self._dots_count)
        if self.is_recording:
            self.recording_label.setText(f"ESCUCHANDO{dots}")
        elif self.is_processing:
            self.processing_label.setText(f"PROCESANDO{dots}")

    # ── Done Page ───────────────────────────────────────────

    def _create_done_page(self):
        page = QWidget()
        page.setStyleSheet("")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 16, 16, 16)

        # Processing label (shown before text arrives, at top)
        self.processing_label = QLabel("PROCESANDO")
        self.processing_label.setStyleSheet(PROCESSING_LABEL)
        self.processing_label.hide()
        layout.addWidget(self.processing_label)

        self.transcription_text = QTextEdit()
        self.transcription_text.setReadOnly(True)
        self.transcription_text.setStyleSheet(CONTENT_TEXT)
        self.transcription_text.setFrameShape(QTextEdit.Shape.NoFrame)
        layout.addWidget(self.transcription_text)

        self.content_stack.addWidget(page)

    # ── Settings Page ───────────────────────────────────────

    def _create_settings_page(self):
        page = QWidget()
        page.setStyleSheet("")
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet(f"""
            QScrollArea {{ background-color: {MUTED}; border: none; }}
            QScrollArea > QWidget > QWidget {{ background-color: {MUTED}; }}
            QScrollBar:vertical {{ width: 6px; background-color: {MUTED}; }}
            QScrollBar::handle:vertical {{ background-color: rgba(255,255,255,0.15); border-radius: 3px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}
        """)

        scroll_content = QWidget()
        scroll_content.setStyleSheet(f"background-color: {MUTED};")
        layout = QVBoxLayout(scroll_content)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(0)

        # Behavior section
        layout.addWidget(self._section_label("Comportamiento"))
        layout.addSpacing(6)

        self.auto_paste_checkbox = QCheckBox("Pegar automáticamente tras transcribir")
        self.auto_paste_checkbox.stateChanged.connect(self._on_auto_paste_changed)
        layout.addWidget(self.auto_paste_checkbox)

        self.auto_enter_checkbox = QCheckBox("Pulsar enter tras pegar")
        self.auto_enter_checkbox.stateChanged.connect(self._on_auto_enter_changed)
        layout.addWidget(self.auto_enter_checkbox)

        self.show_notifications_checkbox = QCheckBox("Mostrar notificaciones de éxito")
        self.show_notifications_checkbox.stateChanged.connect(self._on_show_notifications_changed)
        layout.addWidget(self.show_notifications_checkbox)

        self.always_on_top_checkbox = QCheckBox("Siempre visible")
        self.always_on_top_checkbox.stateChanged.connect(self._on_always_on_top_changed)
        layout.addWidget(self.always_on_top_checkbox)

        self.persistent_overlay_checkbox = QCheckBox("Overlay permanente")
        self.persistent_overlay_checkbox.stateChanged.connect(self._on_persistent_overlay_changed)
        layout.addWidget(self.persistent_overlay_checkbox)

        layout.addSpacing(12)
        layout.addWidget(self._make_separator())
        layout.addSpacing(12)

        # Language section
        layout.addWidget(self._section_label("Idioma"))
        layout.addSpacing(8)

        self.language_combo = QComboBox()
        self.language_combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.language_combo.wheelEvent = lambda e: e.ignore()
        for code, name in self.LANGUAGES.items():
            self.language_combo.addItem(name, code)
        self.language_combo.currentIndexChanged.connect(self._on_language_changed)
        layout.addWidget(self.language_combo)

        layout.addSpacing(12)
        layout.addWidget(self._make_separator())
        layout.addSpacing(12)

        # Model section
        layout.addWidget(self._section_label("Modelo"))
        layout.addSpacing(8)

        self.model_combo = QComboBox()
        self.model_combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.model_combo.wheelEvent = lambda e: e.ignore()
        self.model_combo.addItem("Whisper V3 Turbo (rápido)", "v3-turbo")
        self.model_combo.addItem("Whisper V3 (preciso)", "v3")
        self.model_combo.currentIndexChanged.connect(self._on_model_changed)
        layout.addWidget(self.model_combo)

        layout.addSpacing(12)
        layout.addWidget(self._make_separator())
        layout.addSpacing(12)

        # API Key section
        layout.addWidget(self._section_label("API Key"))
        layout.addSpacing(8)

        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("sk-dicto-...")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.api_key_input)
        layout.addSpacing(8)

        api_row = QHBoxLayout()
        api_row.setSpacing(8)

        self.toggle_api_key_button = QPushButton("Mostrar")
        self.toggle_api_key_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_api_key_button.setFixedHeight(32)
        self.toggle_api_key_button.setStyleSheet(FLAT_BUTTON)
        self.toggle_api_key_button.clicked.connect(self._on_toggle_api_key_visibility)
        api_row.addWidget(self.toggle_api_key_button)

        self.save_api_key_button = QPushButton("Guardar")
        self.save_api_key_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_api_key_button.setFixedHeight(32)
        self.save_api_key_button.setStyleSheet(ACCENT_BUTTON)
        self.save_api_key_button.clicked.connect(self._on_save_api_key)
        api_row.addWidget(self.save_api_key_button)

        layout.addLayout(api_row)
        layout.addStretch()

        scroll.setWidget(scroll_content)
        page_layout.addWidget(scroll)
        self.content_stack.addWidget(page)

    # ── Footer ──────────────────────────────────────────────

    def _create_footer(self, parent_layout):
        # Separator line before footer
        self.footer_sep = QWidget()
        self.footer_sep.setFixedHeight(1)
        self.footer_sep.setStyleSheet(f"background-color: {BORDER};")
        parent_layout.addWidget(self.footer_sep)

        self.footer = QWidget()
        self.footer.setFixedHeight(42)

        layout = QHBoxLayout(self.footer)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(4)

        self.record_button = QPushButton("Grabar")
        self.record_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.record_button.setStyleSheet(RECORD_BUTTON_IDLE)
        self.record_button.clicked.connect(self._on_play_stop_clicked)
        layout.addWidget(self.record_button)

        self.copy_button = QPushButton("Copiar")
        self.copy_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_button.setStyleSheet(FOOTER_TEXT_BUTTON)
        self.copy_button.clicked.connect(self._on_copy_clicked)
        self.copy_button.hide()
        layout.addWidget(self.copy_button)

        layout.addStretch()

        # Status label (for settings feedback, right-aligned)
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.status_label)

        parent_layout.addWidget(self.footer)

    # ── Helpers ─────────────────────────────────────────────

    @staticmethod
    def _section_label(text: str) -> QLabel:
        label = QLabel(text.upper())
        label.setStyleSheet(SECTION_LABEL)
        return label

    @staticmethod
    def _make_separator() -> QWidget:
        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setStyleSheet(SEPARATOR)
        return sep

    def eventFilter(self, obj, event):
        if hasattr(obj, '_icon_hover'):
            if event.type() == QEvent.Type.Enter:
                obj.setIcon(obj._icon_hover)
            elif event.type() == QEvent.Type.Leave:
                obj.setIcon(obj._icon_normal)
        return super().eventFilter(obj, event)

    def _format_elapsed(self) -> str:
        m = self._elapsed_seconds // 60
        s = self._elapsed_seconds % 60
        return f"{m:02d}:{s:02d}"

    def _tick_elapsed(self):
        self._elapsed_seconds += 1
        self.timer_label.setText(self._format_elapsed())

    def _pulse_dot(self):
        self._dot_visible = not self._dot_visible
        if self._dot_visible:
            if self.is_recording:
                self.status_dot.setStyleSheet(DOT_RECORDING)
            elif self.is_processing:
                self.status_dot.setStyleSheet(DOT_PROCESSING)
        else:
            self.status_dot.setStyleSheet(f"background-color: transparent; border-radius: 4px;")

    def _toggle_settings(self):
        if self._settings_open:
            self._close_settings()
        else:
            self._open_settings()

    def _open_settings(self):
        self._settings_open = True
        self._prev_page = self.content_stack.currentIndex()
        self.content_stack.setCurrentIndex(3)  # settings page
        self.settings_button.setIcon(_make_icon(SVG_SETTINGS, 16, TEXT))
        self.settings_button.setStyleSheet(HEADER_BUTTON_ACTIVE)
        self.footer.hide()
        self.footer_sep.hide()
        self.tabs_bar.hide()
        self.tabs_sep.hide()

    def _close_settings(self):
        self._settings_open = False
        self.content_stack.setCurrentIndex(getattr(self, '_prev_page', 0))
        self.settings_button.setIcon(_make_icon(SVG_SETTINGS, 16, TEXT_DIM))
        self.settings_button.setStyleSheet(HEADER_BUTTON)
        self.footer.show()
        self.footer_sep.show()
        self.tabs_bar.show()
        self.tabs_sep.show()

    # ── Load settings ───────────────────────────────────────

    def _load_settings(self):
        if not self.settings:
            return

        self.auto_paste_checkbox.setChecked(self.settings.auto_paste)
        self.auto_enter_checkbox.setChecked(self.settings.auto_enter)
        self.show_notifications_checkbox.setChecked(self.settings.show_success_notifications)

        self.always_on_top_checkbox.setChecked(self.settings.always_on_top)
        self.persistent_overlay_checkbox.setChecked(self.settings.persistent_overlay)
        if self.settings.always_on_top:
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)

        current_language = self.settings.transcription_language
        index = self.language_combo.findData(current_language)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)

        current_model = self.settings.transcription_model
        model_index = self.model_combo.findData(current_model)
        if model_index >= 0:
            self.model_combo.setCurrentIndex(model_index)

        if self.settings.transcription_api_key:
            self.api_key_input.setText(self.settings.transcription_api_key)

    # ── Mouse dragging (frameless window) ───────────────────

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

    # ── Slots ───────────────────────────────────────────────

    @Slot()
    def _on_play_stop_clicked(self):
        if self.is_recording:
            self.stop_clicked.emit()
        else:
            self.play_clicked.emit()

    @Slot()
    def _on_copy_clicked(self):
        text_to_copy = self._get_current_text()
        if text_to_copy:
            clipboard = QApplication.clipboard()
            if clipboard:
                clipboard.setText(text_to_copy)
                self._copied = True
                self.copy_button.setText("Copiado")
                self.copy_button.setStyleSheet(FOOTER_TEXT_BUTTON_SUCCESS)
                QTimer.singleShot(2000, self._reset_copy_button)
                logger.info("Last transcription copied to clipboard")
        self.copy_clicked.emit()

    def _get_current_text(self) -> str:
        """Return the text currently displayed (raw or transformed)."""
        if self._active_format == "raw":
            return self.last_transcription
        return self._format_cache.get(self._active_format, self.last_transcription)

    def _reset_copy_button(self):
        self._copied = False
        self.copy_button.setText("Copiar")
        self.copy_button.setStyleSheet(FOOTER_TEXT_BUTTON)

    @Slot(int)
    def _on_auto_paste_changed(self, state: int):
        checked = state == Qt.CheckState.Checked.value
        if self.settings:
            self.settings.auto_paste = checked
            self.settings.save()

    @Slot(int)
    def _on_auto_enter_changed(self, state: int):
        checked = state == Qt.CheckState.Checked.value
        if self.settings:
            self.settings.auto_enter = checked
            self.settings.save()

    @Slot(int)
    def _on_always_on_top_changed(self, state: int):
        checked = state == Qt.CheckState.Checked.value
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, checked)
        self.show()
        if self.settings:
            self.settings.always_on_top = checked
            self.settings.save()

    @Slot(int)
    def _on_show_notifications_changed(self, state: int):
        checked = state == Qt.CheckState.Checked.value
        if self.settings:
            self.settings.show_success_notifications = checked
            self.settings.save()

    @Slot(int)
    def _on_language_changed(self, index: int):
        language_code = self.language_combo.itemData(index)
        if self.settings:
            self.settings.transcription_language = language_code
            self.settings.save()

    @Slot(int)
    def _on_persistent_overlay_changed(self, state: int):
        checked = state == Qt.CheckState.Checked.value
        if self.settings:
            self.settings.persistent_overlay = checked
            self.settings.save()
        self.persistent_overlay_changed.emit(checked)

    @Slot(int)
    def _on_model_changed(self, index: int):
        model = self.model_combo.itemData(index)
        if self.settings:
            self.settings.transcription_model = model
            self.settings.save()

    @Slot()
    def _on_save_api_key(self):
        api_key = self.api_key_input.text().strip()
        if not api_key:
            self.status_label.setText("API key vacía")
            return
        if not api_key.startswith("sk-dicto-"):
            self.status_label.setText("Key inválida (debe empezar con sk-dicto-)")
            return
        if self.settings:
            self.settings.transcription_api_key = api_key
            self.settings.save()
            self.status_label.setText("API key guardada")
            logger.info("Dicto API key saved")

    @Slot()
    def _on_toggle_api_key_visibility(self):
        if self.api_key_input.echoMode() == QLineEdit.EchoMode.Password:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_api_key_button.setText("Ocultar")
        else:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_api_key_button.setText("Mostrar")

    # ── State updates ───────────────────────────────────────

    @Slot(str)
    def update_status(self, status: str):
        self.status_label.setText(status.capitalize())

    @Slot()
    def set_recording_state(self):
        self.is_recording = True
        self.is_processing = False

        # UI updates
        self.content_stack.setCurrentIndex(1)  # recording page
        self.record_button.setText("Detener")
        self.record_button.setStyleSheet(RECORD_BUTTON_RECORDING)
        self.copy_button.hide()
        self.status_label.setText("")

        # Status dot
        self.status_dot.setStyleSheet(DOT_RECORDING)
        self._dot_pulse_timer.start(500)

        # Timer
        self._elapsed_seconds = 0
        self.timer_label.setText("00:00")
        self.timer_label.setStyleSheet(TIMER_RECORDING)
        self.timer_label.show()
        self._elapsed_timer.start(1000)

        # Waveform
        self.waveform.start()

        # Dots animation
        self._dots_timer.start(400)

        # Tabs
        self._update_tabs_enabled(False)

    @Slot()
    def set_idle_state(self):
        self.is_recording = False
        self.is_processing = False

        # If there's a transcription, keep showing it instead of going back to idle page
        if self.last_transcription:
            self.content_stack.setCurrentIndex(2)  # done page
        else:
            self.content_stack.setCurrentIndex(0)  # idle page

        self.record_button.setText("Grabar")
        self.record_button.setStyleSheet(RECORD_BUTTON_IDLE)
        self.status_label.setText("")

        # Stop timers
        self._elapsed_timer.stop()
        self._dot_pulse_timer.stop()
        self._dots_timer.stop()
        self.timer_label.hide()
        self.waveform.stop()

        # Status dot
        self.status_dot.setStyleSheet(DOT_IDLE)

        # Tabs
        if self.last_transcription:
            self._update_tabs_enabled(True)
        else:
            self.copy_button.hide()
            self._update_tabs_enabled(False)

    @Slot()
    def set_processing_state(self):
        self.is_recording = False
        self.is_processing = True

        self.content_stack.setCurrentIndex(2)  # done page
        self.transcription_text.clear()
        self.processing_label.show()
        self.record_button.setText("Procesando…")
        self.record_button.setStyleSheet(RECORD_BUTTON_PROCESSING)
        self.copy_button.hide()

        # Stop recording animations
        self.waveform.stop()

        # Timer continues but changes color
        self._elapsed_seconds = 0
        self.timer_label.setText("00:00")
        self.timer_label.setStyleSheet(TIMER_PROCESSING)
        self.timer_label.show()
        self._elapsed_timer.start(1000)

        # Dot
        self.status_dot.setStyleSheet(DOT_PROCESSING)
        self._dot_pulse_timer.start(500)

        # Dots animation
        self._dots_timer.start(400)

        # Tabs
        self._update_tabs_enabled(False)

    @Slot(str)
    def update_transcription(self, text: str):
        self.last_transcription = text
        self.is_processing = False
        self._format_cache.clear()
        self._transforming_format = None

        # Show done page with text
        self.content_stack.setCurrentIndex(2)
        self.processing_label.hide()
        self.transcription_text.setText(text)

        # Button states
        self.record_button.setText("Grabar")
        self.record_button.setStyleSheet(RECORD_BUTTON_IDLE)
        self.copy_button.setText("Copiar")
        self.copy_button.setStyleSheet(FOOTER_TEXT_BUTTON)
        self.copy_button.show()

        # Stop timers
        self._elapsed_timer.stop()
        self._dot_pulse_timer.stop()
        self._dots_timer.stop()
        self.timer_label.hide()

        # Dot
        self.status_dot.setStyleSheet(DOT_SUCCESS)

        # Tabs
        self._active_format = "raw"
        self._update_tabs_enabled(True)

    @Slot()
    def show_settings_tab(self):
        self._open_settings()
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        logger.info("Main window hidden to tray")
