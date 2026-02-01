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
    QTabWidget,
    QCheckBox,
    QComboBox,
    QGroupBox,
    QFormLayout,
    QApplication,
    QTextEdit,
    QLineEdit,
)
from PySide6.QtCore import Signal, Slot, Qt
from PySide6.QtGui import QIcon

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window with controls and settings."""

    # Available languages for transcription
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
        """
        Initialize main window.

        Args:
            settings: Settings instance for persisting preferences
        """
        super().__init__()

        self.settings = settings
        self.is_recording = False
        self.last_transcription = ""

        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("Dicto")
        self.setMinimumSize(400, 350)
        self.resize(450, 400)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)

        # Tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # Create tabs
        self._create_main_tab()
        self._create_settings_tab()

    def _create_main_tab(self):
        """Create the main control tab."""
        main_tab = QWidget()
        layout = QVBoxLayout(main_tab)

        # Status label
        self.status_label = QLabel("Status: Idle")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px;")
        layout.addWidget(self.status_label)

        # Control buttons
        buttons_layout = QHBoxLayout()

        self.play_stop_button = QPushButton("Record")
        self.play_stop_button.setMinimumHeight(50)
        self.play_stop_button.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                font-weight: bold;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.play_stop_button.clicked.connect(self._on_play_stop_clicked)
        buttons_layout.addWidget(self.play_stop_button)

        self.copy_button = QPushButton("Copy")
        self.copy_button.setMinimumHeight(50)
        self.copy_button.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                font-weight: bold;
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
        """)
        self.copy_button.clicked.connect(self._on_copy_clicked)
        buttons_layout.addWidget(self.copy_button)

        layout.addLayout(buttons_layout)

        # Last transcription section
        transcription_group = QGroupBox("Last Transcription")
        transcription_layout = QVBoxLayout(transcription_group)

        self.transcription_text = QTextEdit()
        self.transcription_text.setReadOnly(True)
        self.transcription_text.setPlaceholderText("No transcription yet...")
        self.transcription_text.setMaximumHeight(150)
        transcription_layout.addWidget(self.transcription_text)

        layout.addWidget(transcription_group)

        # Add stretch to push everything to top
        layout.addStretch()

        self.tab_widget.addTab(main_tab, "Main")

    def _create_settings_tab(self):
        """Create the settings tab."""
        settings_tab = QWidget()
        layout = QVBoxLayout(settings_tab)

        # Behavior settings group
        behavior_group = QGroupBox("Behavior")
        behavior_layout = QVBoxLayout(behavior_group)

        self.auto_paste_checkbox = QCheckBox("Auto Paste (Ctrl+V after transcription)")
        self.auto_paste_checkbox.stateChanged.connect(self._on_auto_paste_changed)
        behavior_layout.addWidget(self.auto_paste_checkbox)

        self.auto_enter_checkbox = QCheckBox("Auto Enter (press Enter after paste)")
        self.auto_enter_checkbox.stateChanged.connect(self._on_auto_enter_changed)
        behavior_layout.addWidget(self.auto_enter_checkbox)

        self.show_notifications_checkbox = QCheckBox("Show Success Notifications")
        self.show_notifications_checkbox.stateChanged.connect(self._on_show_notifications_changed)
        behavior_layout.addWidget(self.show_notifications_checkbox)

        layout.addWidget(behavior_group)

        # Language settings group
        language_group = QGroupBox("Language")
        language_layout = QFormLayout(language_group)

        self.language_combo = QComboBox()
        for code, name in self.LANGUAGES.items():
            self.language_combo.addItem(name, code)
        self.language_combo.currentIndexChanged.connect(self._on_language_changed)
        language_layout.addRow("Transcription Language:", self.language_combo)

        layout.addWidget(language_group)

        # API Key settings group
        api_group = QGroupBox("API Key")
        api_layout = QVBoxLayout(api_group)

        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Enter Groq API Key (gsk_...)")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        api_layout.addWidget(self.api_key_input)

        api_buttons_layout = QHBoxLayout()

        self.toggle_api_key_button = QPushButton("Show")
        self.toggle_api_key_button.setFixedWidth(60)
        self.toggle_api_key_button.clicked.connect(self._on_toggle_api_key_visibility)
        api_buttons_layout.addWidget(self.toggle_api_key_button)

        self.save_api_key_button = QPushButton("Save API Key")
        self.save_api_key_button.clicked.connect(self._on_save_api_key)
        api_buttons_layout.addWidget(self.save_api_key_button)

        api_layout.addLayout(api_buttons_layout)

        layout.addWidget(api_group)

        # Add stretch to push everything to top
        layout.addStretch()

        self.tab_widget.addTab(settings_tab, "Settings")

    def _load_settings(self):
        """Load settings into UI controls."""
        if not self.settings:
            return

        # Behavior settings
        self.auto_paste_checkbox.setChecked(self.settings.auto_paste)
        self.auto_enter_checkbox.setChecked(self.settings.auto_enter)
        self.show_notifications_checkbox.setChecked(self.settings.show_success_notifications)

        # Language
        current_language = self.settings.transcription_language
        index = self.language_combo.findData(current_language)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)

        # API Key
        if self.settings and self.settings.transcription_api_key:
            self.api_key_input.setText(self.settings.transcription_api_key)

    @Slot()
    def _on_play_stop_clicked(self):
        """Handle play/stop button click."""
        if self.is_recording:
            self.stop_clicked.emit()
        else:
            self.play_clicked.emit()

    @Slot()
    def _on_copy_clicked(self):
        """Handle copy button click."""
        if self.last_transcription:
            clipboard = QApplication.clipboard()
            if clipboard:
                clipboard.setText(self.last_transcription)
                logger.info("Last transcription copied to clipboard")
        self.copy_clicked.emit()

    @Slot(int)
    def _on_auto_paste_changed(self, state: int):
        """Handle auto-paste checkbox change."""
        checked = state == Qt.CheckState.Checked.value
        logger.info(f"Auto-paste {'enabled' if checked else 'disabled'}")
        if self.settings:
            self.settings.auto_paste = checked
            self.settings.save()

    @Slot(int)
    def _on_auto_enter_changed(self, state: int):
        """Handle auto-enter checkbox change."""
        checked = state == Qt.CheckState.Checked.value
        logger.info(f"Auto-enter {'enabled' if checked else 'disabled'}")
        if self.settings:
            self.settings.auto_enter = checked
            self.settings.save()

    @Slot(int)
    def _on_show_notifications_changed(self, state: int):
        """Handle show notifications checkbox change."""
        checked = state == Qt.CheckState.Checked.value
        logger.info(f"Show success notifications {'enabled' if checked else 'disabled'}")
        if self.settings:
            self.settings.show_success_notifications = checked
            self.settings.save()

    @Slot(int)
    def _on_language_changed(self, index: int):
        """Handle language combobox change."""
        language_code = self.language_combo.itemData(index)
        language_name = self.language_combo.itemText(index)
        logger.info(f"Language changed to: {language_name} ({language_code})")
        if self.settings:
            self.settings.transcription_language = language_code
            self.settings.save()

    @Slot()
    def _on_save_api_key(self):
        """Handle save API key button click."""
        api_key = self.api_key_input.text().strip()

        if not api_key:
            self.status_label.setText("Status: API key is empty")
            return

        # Basic validation: Groq API keys start with "gsk_"
        if not api_key.startswith("gsk_"):
            self.status_label.setText("Status: Invalid API key (should start with 'gsk_')")
            return

        if self.settings:
            self.settings.transcription_api_key = api_key
            self.settings.save()
            self.status_label.setText("Status: API Key saved!")
            logger.info("Groq API key saved")

    @Slot()
    def _on_toggle_api_key_visibility(self):
        """Toggle API key visibility between hidden and visible."""
        if self.api_key_input.echoMode() == QLineEdit.EchoMode.Password:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_api_key_button.setText("Hide")
        else:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_api_key_button.setText("Show")

    @Slot(str)
    def update_status(self, status: str):
        """
        Update status label.

        Args:
            status: Status text
        """
        self.status_label.setText(f"Status: {status.capitalize()}")

    @Slot()
    def set_recording_state(self):
        """Set UI to recording state."""
        self.is_recording = True
        self.play_stop_button.setText("Stop")
        self.play_stop_button.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                font-weight: bold;
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:pressed {
                background-color: #c41508;
            }
        """)
        self.update_status("Recording...")

    @Slot()
    def set_idle_state(self):
        """Set UI to idle state."""
        self.is_recording = False
        self.play_stop_button.setText("Record")
        self.play_stop_button.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                font-weight: bold;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.update_status("Idle")

    @Slot()
    def set_processing_state(self):
        """Set UI to processing state."""
        self.is_recording = False
        self.play_stop_button.setText("Record")
        self.play_stop_button.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                font-weight: bold;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.update_status("Processing...")

    @Slot(str)
    def update_transcription(self, text: str):
        """
        Update last transcription text.

        Args:
            text: Transcribed text
        """
        self.last_transcription = text
        self.transcription_text.setText(text)

    def closeEvent(self, event):
        """Handle window close event - minimize to tray instead of closing."""
        event.ignore()
        self.hide()
        logger.info("Main window hidden to tray")
