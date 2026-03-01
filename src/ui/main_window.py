"""
Main window for Dicto application.
"""

import logging
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
    QSizePolicy,
)
from PySide6.QtCore import Signal, Slot, Qt, QSize, QUrl
from PySide6.QtGui import QIcon, QFont, QPainter, QColor, QPixmap, QDesktopServices

from src.utils.icons import get_icon_path
from src.ui.main_window_styles import (
    GLOBAL_STYLE,
    TRANSCRIPTION_TEXT,
    ICON_BUTTON,
    STATUS_LABEL,
    SECTION_LABEL,
    SETTINGS_TITLE,
    FLAT_BUTTON,
    ACCENT_BUTTON,
    TOOLBAR_BUTTON,
    RECORD_BUTTON_IDLE,
    RECORD_BUTTON_RECORDING,
    SEPARATOR,
    TEXT,
    TEXT_DIM,
    SVG_BACK,
)

logger = logging.getLogger(__name__)


def _make_icon(svg_data: str, size: int, color: str) -> QIcon:
    """Create a QIcon from inline SVG data with a given color."""
    from PySide6.QtSvg import QSvgRenderer

    colored = svg_data.replace("currentColor", color)
    renderer = QSvgRenderer(colored.encode())
    px = QPixmap(QSize(size, size))
    px.fill(QColor(0, 0, 0, 0))
    painter = QPainter(px)
    renderer.render(painter)
    painter.end()
    icon = QIcon()
    icon.addPixmap(px)
    return icon


class MainWindow(QMainWindow):
    """Main application window with controls and settings."""

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

    # Signals
    play_clicked = Signal()
    stop_clicked = Signal()
    copy_clicked = Signal()

    def __init__(self, settings=None):
        super().__init__()
        self.settings = settings
        self.is_recording = False
        self.last_transcription = ""
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        self.setWindowTitle("Dicto")
        self.setMinimumSize(380, 420)
        self.resize(400, 460)
        self.setStyleSheet(GLOBAL_STYLE)

        icon_path = get_icon_path()
        if icon_path:
            self.setWindowIcon(QIcon(str(icon_path)))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.pages = QStackedWidget()
        main_layout.addWidget(self.pages)

        self._create_main_page()
        self._create_settings_page()

    # ── Main Page ──────────────────────────────────────────────

    def _create_main_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(0)

        # Transcription area (hero)
        self.transcription_text = QTextEdit()
        self.transcription_text.setReadOnly(True)
        self.transcription_text.setPlaceholderText("Press record or use your hotkey to start transcribing...")
        self.transcription_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.transcription_text.setStyleSheet(TRANSCRIPTION_TEXT)
        layout.addWidget(self.transcription_text)
        layout.addSpacing(10)

        # Bottom toolbar: record | copy | ---status--- | settings
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)

        self.play_stop_button = QPushButton("Record")
        self.play_stop_button.setFixedHeight(32)
        self.play_stop_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_record_button_idle_style()
        self.play_stop_button.clicked.connect(self._on_play_stop_clicked)
        toolbar.addWidget(self.play_stop_button)

        self.copy_button = QPushButton("Copy")
        self.copy_button.setFixedHeight(32)
        self.copy_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_button.setStyleSheet(TOOLBAR_BUTTON)
        self.copy_button.clicked.connect(self._on_copy_clicked)
        toolbar.addWidget(self.copy_button)

        toolbar.addStretch()

        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet(STATUS_LABEL)
        toolbar.addWidget(self.status_label)

        toolbar.addStretch()

        self.web_button = QPushButton("Web")
        self.web_button.setFixedHeight(32)
        self.web_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.web_button.setStyleSheet(TOOLBAR_BUTTON)
        self.web_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://dicto.io")))
        toolbar.addWidget(self.web_button)

        self.settings_button = QPushButton("Settings")
        self.settings_button.setFixedHeight(32)
        self.settings_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_button.setStyleSheet(TOOLBAR_BUTTON)
        self.settings_button.clicked.connect(lambda: self.pages.setCurrentIndex(1))
        toolbar.addWidget(self.settings_button)

        layout.addLayout(toolbar)
        self.pages.addWidget(page)

    # ── Settings Page ──────────────────────────────────────────

    def _create_settings_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(0)

        # Header with back button
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)

        back_btn = QPushButton()
        back_btn.setFixedSize(32, 32)
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.setIcon(_make_icon(SVG_BACK, 18, TEXT_DIM))
        back_btn.setIconSize(QSize(18, 18))
        back_btn.setStyleSheet(ICON_BUTTON)
        back_btn.clicked.connect(lambda: self.pages.setCurrentIndex(0))
        header.addWidget(back_btn)

        title = QLabel("Settings")
        title_font = QFont()
        title_font.setPointSize(15)
        title_font.setWeight(QFont.Weight.DemiBold)
        title.setFont(title_font)
        title.setStyleSheet(SETTINGS_TITLE)
        header.addWidget(title)

        header.addStretch()
        layout.addLayout(header)
        layout.addSpacing(20)

        # -- Behavior section --
        layout.addWidget(self._section_label("Behavior"))
        layout.addSpacing(6)

        self.auto_paste_checkbox = QCheckBox("Auto paste after transcription")
        self.auto_paste_checkbox.stateChanged.connect(self._on_auto_paste_changed)
        layout.addWidget(self.auto_paste_checkbox)

        self.auto_enter_checkbox = QCheckBox("Press enter after paste")
        self.auto_enter_checkbox.stateChanged.connect(self._on_auto_enter_changed)
        layout.addWidget(self.auto_enter_checkbox)

        self.show_notifications_checkbox = QCheckBox("Show success notifications")
        self.show_notifications_checkbox.stateChanged.connect(self._on_show_notifications_changed)
        layout.addWidget(self.show_notifications_checkbox)

        self.always_on_top_checkbox = QCheckBox("Always on top")
        self.always_on_top_checkbox.stateChanged.connect(self._on_always_on_top_changed)
        layout.addWidget(self.always_on_top_checkbox)

        layout.addSpacing(16)
        layout.addWidget(self._make_separator())
        layout.addSpacing(16)

        # -- Language section --
        layout.addWidget(self._section_label("Language"))
        layout.addSpacing(8)

        self.language_combo = QComboBox()
        for code, name in self.LANGUAGES.items():
            self.language_combo.addItem(name, code)
        self.language_combo.currentIndexChanged.connect(self._on_language_changed)
        layout.addWidget(self.language_combo)

        layout.addSpacing(16)
        layout.addWidget(self._make_separator())
        layout.addSpacing(16)

        # -- API Key section --
        layout.addWidget(self._section_label("API Key"))
        layout.addSpacing(8)

        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("gsk_...")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.api_key_input)
        layout.addSpacing(8)

        api_row = QHBoxLayout()
        api_row.setSpacing(8)

        self.toggle_api_key_button = QPushButton("Show")
        self.toggle_api_key_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_api_key_button.setFixedHeight(32)
        self.toggle_api_key_button.setStyleSheet(FLAT_BUTTON)
        self.toggle_api_key_button.clicked.connect(self._on_toggle_api_key_visibility)
        api_row.addWidget(self.toggle_api_key_button)

        self.save_api_key_button = QPushButton("Save")
        self.save_api_key_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_api_key_button.setFixedHeight(32)
        self.save_api_key_button.setStyleSheet(ACCENT_BUTTON)
        self.save_api_key_button.clicked.connect(self._on_save_api_key)
        api_row.addWidget(self.save_api_key_button)

        layout.addLayout(api_row)
        layout.addStretch()

        self.pages.addWidget(page)

    # ── Helpers ────────────────────────────────────────────────

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

    def _apply_record_button_idle_style(self):
        self.play_stop_button.setText("Record")
        self.play_stop_button.setStyleSheet(RECORD_BUTTON_IDLE)

    def _apply_record_button_recording_style(self):
        self.play_stop_button.setText("Stop")
        self.play_stop_button.setStyleSheet(RECORD_BUTTON_RECORDING)

    # ── Load settings ──────────────────────────────────────────

    def _load_settings(self):
        if not self.settings:
            return

        self.auto_paste_checkbox.setChecked(self.settings.auto_paste)
        self.auto_enter_checkbox.setChecked(self.settings.auto_enter)
        self.show_notifications_checkbox.setChecked(self.settings.show_success_notifications)

        self.always_on_top_checkbox.setChecked(self.settings.always_on_top)
        if self.settings.always_on_top:
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)

        current_language = self.settings.transcription_language
        index = self.language_combo.findData(current_language)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)

        if self.settings.transcription_api_key:
            self.api_key_input.setText(self.settings.transcription_api_key)

    # ── Slots ──────────────────────────────────────────────────

    @Slot()
    def _on_play_stop_clicked(self):
        if self.is_recording:
            self.stop_clicked.emit()
        else:
            self.play_clicked.emit()

    @Slot()
    def _on_copy_clicked(self):
        if self.last_transcription:
            clipboard = QApplication.clipboard()
            if clipboard:
                clipboard.setText(self.last_transcription)
                logger.info("Last transcription copied to clipboard")
        self.copy_clicked.emit()

    @Slot(int)
    def _on_auto_paste_changed(self, state: int):
        checked = state == Qt.CheckState.Checked.value
        logger.info(f"Auto-paste {'enabled' if checked else 'disabled'}")
        if self.settings:
            self.settings.auto_paste = checked
            self.settings.save()

    @Slot(int)
    def _on_auto_enter_changed(self, state: int):
        checked = state == Qt.CheckState.Checked.value
        logger.info(f"Auto-enter {'enabled' if checked else 'disabled'}")
        if self.settings:
            self.settings.auto_enter = checked
            self.settings.save()

    @Slot(int)
    def _on_always_on_top_changed(self, state: int):
        checked = state == Qt.CheckState.Checked.value
        logger.info(f"Always on top {'enabled' if checked else 'disabled'}")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, checked)
        self.show()
        if self.settings:
            self.settings.always_on_top = checked
            self.settings.save()

    @Slot(int)
    def _on_show_notifications_changed(self, state: int):
        checked = state == Qt.CheckState.Checked.value
        logger.info(f"Show success notifications {'enabled' if checked else 'disabled'}")
        if self.settings:
            self.settings.show_success_notifications = checked
            self.settings.save()

    @Slot(int)
    def _on_language_changed(self, index: int):
        language_code = self.language_combo.itemData(index)
        language_name = self.language_combo.itemText(index)
        logger.info(f"Language changed to: {language_name} ({language_code})")
        if self.settings:
            self.settings.transcription_language = language_code
            self.settings.save()

    @Slot()
    def _on_save_api_key(self):
        api_key = self.api_key_input.text().strip()
        if not api_key:
            self.status_label.setText("API key is empty")
            return
        if not api_key.startswith("gsk_"):
            self.status_label.setText("Invalid key (should start with gsk_)")
            return
        if self.settings:
            self.settings.transcription_api_key = api_key
            self.settings.save()
            self.status_label.setText("API key saved")
            logger.info("Groq API key saved")

    @Slot()
    def _on_toggle_api_key_visibility(self):
        if self.api_key_input.echoMode() == QLineEdit.EchoMode.Password:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_api_key_button.setText("Hide")
        else:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_api_key_button.setText("Show")

    # ── State updates ──────────────────────────────────────────

    @Slot(str)
    def update_status(self, status: str):
        self.status_label.setText(status.capitalize())

    @Slot()
    def set_recording_state(self):
        self.is_recording = True
        self._apply_record_button_recording_style()
        self.update_status("Recording...")

    @Slot()
    def set_idle_state(self):
        self.is_recording = False
        self._apply_record_button_idle_style()
        self.update_status("Ready")

    @Slot()
    def set_processing_state(self):
        self.is_recording = False
        self._apply_record_button_idle_style()
        self.update_status("Transcribing...")

    @Slot(str)
    def update_transcription(self, text: str):
        self.last_transcription = text
        self.transcription_text.setText(text)

    @Slot()
    def show_settings_tab(self):
        self.pages.setCurrentIndex(1)
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        logger.info("Main window hidden to tray")
