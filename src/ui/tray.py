"""
System tray manager for Dicto application.
"""

import logging
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import QObject, Signal, Slot

logger = logging.getLogger(__name__)


class TrayManager(QObject):
    """Manages the system tray icon and menu."""

    tray_icon: QSystemTrayIcon | None
    menu: QMenu | None

    # Signals
    quit_requested = Signal()
    show_window_requested = Signal()
    open_config_requested = Signal()

    def __init__(self, app):
        """
        Initialize tray manager.

        Args:
            app: QApplication instance
        """
        super().__init__()

        self.app = app
        self.tray_icon = None
        self.menu = None

        self._create_tray_icon()

    def _create_tray_icon(self):
        """Create system tray icon and menu."""
        # Check if system tray is available
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.warning("System tray is not available on this system")
            return

        # Create tray icon
        self.tray_icon = QSystemTrayIcon(self.app)

        # Set icon (using default for now, can be customized)
        # For now we'll use a simple built-in icon
        # In production, you'd want to use custom icons from assets folder
        icon = self._get_default_icon()
        self.tray_icon.setIcon(icon)

        # Set tooltip
        self.tray_icon.setToolTip("Dicto")

        # Create context menu
        self._create_menu()

        # Show tray icon
        self.tray_icon.show()
        logger.info("System tray icon created")

    def _create_menu(self):
        """Create context menu for tray icon."""
        self.menu = QMenu()

        # Show window action
        show_window_action = QAction("Show Window", self.menu)
        show_window_action.triggered.connect(self._on_show_window)
        self.menu.addAction(show_window_action)

        # Open config action
        open_config_action = QAction("Open Config", self.menu)
        open_config_action.triggered.connect(self._on_open_config)
        self.menu.addAction(open_config_action)

        self.menu.addSeparator()

        # Status action (disabled, just shows current state)
        self.status_action = QAction("Status: Idle", self.menu)
        self.status_action.setEnabled(False)
        self.menu.addAction(self.status_action)

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
    def _on_show_window(self):
        """Handle show window action."""
        logger.info("Show window requested from tray menu")
        self.show_window_requested.emit()

    @Slot()
    def _on_open_config(self):
        """Handle open config action."""
        logger.info("Open config requested from tray menu")
        self.open_config_requested.emit()

    @Slot()
    def _on_quit(self):
        """Handle quit action."""
        logger.info("Quit requested from tray menu")
        self.quit_requested.emit()

    @Slot(str)
    def update_status(self, status: str):
        """
        Update status text in menu.

        Args:
            status: Status text
        """
        if self.status_action:
            self.status_action.setText(f"Status: {status.capitalize()}")

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
            logger.info("Tray icon cleaned up")
