"""
System tray manager for Voice to Clipboard application.
"""

from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction, QActionGroup
from PySide6.QtCore import QObject, Signal, Slot


class TrayManager(QObject):
    """Manages the system tray icon and menu."""

    tray_icon: QSystemTrayIcon | None
    menu: QMenu | None

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
    quit_requested = Signal()
    show_last_transcription = Signal()
    auto_paste_changed = Signal(bool)
    auto_enter_changed = Signal(bool)
    language_changed = Signal(str)

    def __init__(self, app, settings=None):
        """
        Initialize tray manager.

        Args:
            app: QApplication instance
            settings: Settings instance for persisting preferences
        """
        super().__init__()

        self.app = app
        self.settings = settings
        self.tray_icon = None
        self.menu = None
        self.last_transcription = ""

        self._create_tray_icon()

    def _create_tray_icon(self):
        """Create system tray icon and menu."""
        # Check if system tray is available
        if not QSystemTrayIcon.isSystemTrayAvailable():
            print("System tray is not available on this system")
            return

        # Create tray icon
        self.tray_icon = QSystemTrayIcon(self.app)

        # Set icon (using default for now, can be customized)
        # For now we'll use a simple built-in icon
        # In production, you'd want to use custom icons from assets folder
        icon = self._get_default_icon()
        self.tray_icon.setIcon(icon)

        # Set tooltip
        self.tray_icon.setToolTip("Voice to Clipboard")

        # Create context menu
        self._create_menu()

        # Show tray icon
        self.tray_icon.show()
        print("System tray icon created")

    def _create_menu(self):
        """Create context menu for tray icon."""
        self.menu = QMenu()

        # Last transcription action
        self.last_transcription_action = QAction(
            "Last Transcription: (none)", self.menu
        )
        self.last_transcription_action.triggered.connect(
            self._on_show_last_transcription
        )
        self.menu.addAction(self.last_transcription_action)

        self.menu.addSeparator()

        # Status action (disabled, just shows current state)
        self.status_action = QAction("Status: Idle", self.menu)
        self.status_action.setEnabled(False)
        self.menu.addAction(self.status_action)

        self.menu.addSeparator()

        # Auto-paste option (Ctrl+V after copy)
        self.auto_paste_action = QAction("Auto Paste (Ctrl+V)", self.menu)
        self.auto_paste_action.setCheckable(True)
        if self.settings:
            self.auto_paste_action.setChecked(self.settings.auto_paste)
        self.auto_paste_action.triggered.connect(self._on_auto_paste_changed)
        self.menu.addAction(self.auto_paste_action)

        # Auto-enter option (press Enter after paste)
        self.auto_enter_action = QAction("Auto Enter", self.menu)
        self.auto_enter_action.setCheckable(True)
        if self.settings:
            self.auto_enter_action.setChecked(self.settings.auto_enter)
        self.auto_enter_action.triggered.connect(self._on_auto_enter_changed)
        self.menu.addAction(self.auto_enter_action)

        self.menu.addSeparator()

        # Language submenu
        self.language_menu = QMenu("Language", self.menu)
        self.language_action_group = QActionGroup(self.language_menu)
        self.language_action_group.setExclusive(True)
        self.language_actions = {}

        current_language = (
            self.settings.transcription_language if self.settings else "auto"
        )

        for code, name in self.LANGUAGES.items():
            action = QAction(name, self.language_menu)
            action.setCheckable(True)
            action.setChecked(code == current_language)
            action.setData(code)
            action.triggered.connect(self._on_language_changed)
            self.language_action_group.addAction(action)
            self.language_menu.addAction(action)
            self.language_actions[code] = action

        self.menu.addMenu(self.language_menu)

        self.menu.addSeparator()

        # Quit action
        quit_action = QAction("Quit", self.menu)
        quit_action.triggered.connect(self._on_quit)
        self.menu.addAction(quit_action)

        # Set context menu
        if self.tray_icon is not None:
            self.tray_icon.setContextMenu(self.menu)

    def _get_default_icon(self) -> QIcon:
        """
        Get default icon for tray.

        Returns:
            QIcon instance
        """
        # For now, use a standard system icon
        # In production, load custom icon from assets/icons/
        from PySide6.QtWidgets import QStyle

        style = self.app.style()
        icon = style.standardIcon(QStyle.StandardPixmap.SP_MediaVolume)
        return icon

    @Slot()
    def _on_show_last_transcription(self):
        """Handle show last transcription action."""
        if self.last_transcription:
            self.show_last_transcription.emit()
            # Show a message with the last transcription
            if self.tray_icon:
                self.tray_icon.showMessage(
                    "Last Transcription",
                    self.last_transcription,
                    QSystemTrayIcon.MessageIcon.Information,
                    3000,  # 3 seconds
                )
        else:
            if self.tray_icon:
                self.tray_icon.showMessage(
                    "No Transcription",
                    "No transcription available yet",
                    QSystemTrayIcon.MessageIcon.Information,
                    2000,
                )

    @Slot()
    def _on_quit(self):
        """Handle quit action."""
        print("Quit requested from tray menu")
        self.quit_requested.emit()

    @Slot()
    def _on_auto_paste_changed(self):
        """Handle auto-paste toggle."""
        checked = self.auto_paste_action.isChecked()
        print(f"Auto-paste {'enabled' if checked else 'disabled'}")
        if self.settings:
            self.settings.auto_paste = checked
            self.settings.save()
        self.auto_paste_changed.emit(checked)

    @Slot()
    def _on_auto_enter_changed(self):
        """Handle auto-enter toggle."""
        checked = self.auto_enter_action.isChecked()
        print(f"Auto-enter {'enabled' if checked else 'disabled'}")
        if self.settings:
            self.settings.auto_enter = checked
            self.settings.save()
        self.auto_enter_changed.emit(checked)

    @Slot()
    def _on_language_changed(self):
        """Handle language selection."""
        action = self.language_action_group.checkedAction()
        if action:
            language_code = action.data()
            language_name = self.LANGUAGES.get(language_code, language_code)
            print(f"Language changed to: {language_name} ({language_code})")
            if self.settings:
                self.settings.transcription_language = language_code
                self.settings.save()
            self.language_changed.emit(language_code)

    @Slot(str)
    def update_last_transcription(self, text: str):
        """
        Update last transcription text.

        Args:
            text: Transcribed text
        """
        self.last_transcription = text
        # Update menu item
        preview = text[:50] + "..." if len(text) > 50 else text
        self.last_transcription_action.setText(f"Last: {preview}")

    @Slot(str)
    def update_status(self, status: str):
        """
        Update status text in menu.

        Args:
            status: Status text
        """
        if self.status_action:
            self.status_action.setText(f"Status: {status.capitalize()}")

    @Slot()
    def set_recording_icon(self):
        """Change icon to indicate recording state."""
        # In production, load a different icon for recording state
        # For now, keep the same icon
        pass

    @Slot()
    def set_idle_icon(self):
        """Change icon back to idle state."""
        # In production, load the normal icon
        # For now, keep the same icon
        pass

    def show_message(self, title: str, message: str, icon_type=None):
        """
        Show a notification message.

        Args:
            title: Message title
            message: Message text
            icon_type: QSystemTrayIcon.MessageIcon type
        """
        if self.tray_icon:
            if icon_type is None:
                icon_type = QSystemTrayIcon.MessageIcon.Information

            self.tray_icon.showMessage(title, message, icon_type, 3000)

    def show_error(self, message: str):
        """
        Show error notification.

        Args:
            message: Error message
        """
        self.show_message("Error", message, QSystemTrayIcon.MessageIcon.Critical)

    def show_success(self, message: str):
        """
        Show success notification.

        Args:
            message: Success message
        """
        self.show_message("Success", message, QSystemTrayIcon.MessageIcon.Information)

    def cleanup(self):
        """Clean up tray icon."""
        if self.tray_icon:
            self.tray_icon.hide()
            print("Tray icon cleaned up")
