"""
System tray manager for Dicto application.
"""

from __future__ import annotations

import logging
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import QObject, Signal, Slot

from src.utils.icons import get_icon_path
from src.ui.main_window_styles import TRAY_MENU_STYLE
from src.i18n import t

logger = logging.getLogger(__name__)


class TrayManager(QObject):
    """Manages the system tray icon and menu."""

    quit_requested = Signal()
    show_window_requested = Signal()
    open_config_requested = Signal()
    update_requested = Signal()

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.tray_icon: QSystemTrayIcon | None = None
        self.menu: QMenu | None = None
        self.update_action: QAction | None = None
        self._update_version: str | None = None
        self._status_label: str = t("status_idle")
        self._create_tray_icon()

    def _create_tray_icon(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.warning("System tray is not available on this system")
            return

        self.tray_icon = QSystemTrayIcon(self.app)
        self.tray_icon.setIcon(self._get_icon())
        self.tray_icon.setToolTip("Dicto")
        self.tray_icon.activated.connect(self._on_tray_activated)
        self._create_menu()
        self.tray_icon.show()
        logger.info("System tray icon created")

    def _create_menu(self):
        self.menu = QMenu()
        self.menu.setStyleSheet(TRAY_MENU_STYLE)

        # Show window
        show_action = QAction(t("open_dicto"), self.menu)
        show_action.triggered.connect(self._on_show_window)
        self.menu.addAction(show_action)

        # Settings
        settings_action = QAction(t("settings"), self.menu)
        settings_action.triggered.connect(self._on_open_config)
        self.menu.addAction(settings_action)

        # Update entry — hidden until the startup check finds a newer release.
        self.update_action = QAction(t("check_for_updates"), self.menu)
        self.update_action.triggered.connect(self._on_update_requested)
        self.update_action.setVisible(False)
        self.menu.addAction(self.update_action)

        self.menu.addSeparator()

        # Quit
        quit_action = QAction(t("quit"), self.menu)
        quit_action.triggered.connect(self._on_quit)
        self.menu.addAction(quit_action)

        if self.tray_icon:
            self.tray_icon.setContextMenu(self.menu)

    def _get_icon(self) -> QIcon:
        icon_path = get_icon_path()
        if icon_path:
            return QIcon(str(icon_path))
        from PySide6.QtWidgets import QStyle

        return self.app.style().standardIcon(QStyle.StandardPixmap.SP_MediaVolume)

    @Slot(QSystemTrayIcon.ActivationReason)
    def _on_tray_activated(self, reason):
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self.show_window_requested.emit()

    @Slot()
    def _on_show_window(self):
        self.show_window_requested.emit()

    @Slot()
    def _on_open_config(self):
        self.open_config_requested.emit()

    @Slot()
    def _on_quit(self):
        self.quit_requested.emit()

    @Slot()
    def _on_update_requested(self):
        self.update_requested.emit()

    @Slot(str)
    def notify_update_available(self, version: str):
        """Advertise a pending update in the menu, tooltip and a notification."""
        self._update_version = version
        if self.update_action:
            self.update_action.setText(t("update_available", version=version))
            self.update_action.setVisible(True)
        self._refresh_tooltip()
        self.show_message("Dicto", t("update_available", version=version))

    def _refresh_tooltip(self):
        """Rebuild the tooltip from the current status + pending update."""
        if not self.tray_icon:
            return
        tooltip = f"Dicto — {self._status_label}"
        if self._update_version:
            tooltip += f"\n{t('update_available', version=self._update_version)}"
        self.tray_icon.setToolTip(tooltip)

    @Slot(str)
    def update_status(self, status: str):
        if self.tray_icon:
            status_labels = {
                "idle": t("status_idle"),
                "recording": t("status_recording"),
                "processing": t("status_processing"),
                "success": t("status_success"),
                "error": t("status_error"),
            }
            self._status_label = status_labels.get(status, status)
            self._refresh_tooltip()
            self._update_tray_icon(status)

    def _update_tray_icon(self, status: str):
        """Update tray icon color based on status."""
        if not self.tray_icon:
            return
        status_icon_map = {
            "recording": "icon_red",
            "processing": "icon_amber",
            "success": "icon_green",
            "idle": "icon_green",
            "error": "icon_red",
        }
        icon_name = status_icon_map.get(status)
        if icon_name:
            icon_path = get_icon_path(icon_name)
            if icon_path:
                self.tray_icon.setIcon(QIcon(str(icon_path)))
                return
        self.tray_icon.setIcon(self._get_icon())

    def show_message(self, title: str, message: str, icon_type=None):
        if self.tray_icon:
            if icon_type is None:
                icon_type = QSystemTrayIcon.MessageIcon.Information
            self.tray_icon.showMessage(title, message, icon_type, 3000)

    def show_error(self, message: str):
        self.show_message(
            f"Dicto — {t('error')}", message, QSystemTrayIcon.MessageIcon.Critical
        )

    def show_warning(self, message: str):
        """A partial success: shown with the Warning icon, never as Critical."""
        self.show_message("Dicto", message, QSystemTrayIcon.MessageIcon.Warning)

    def show_success(self, message: str):
        self.show_message("Dicto", message, QSystemTrayIcon.MessageIcon.Information)

    def cleanup(self):
        if self.tray_icon:
            self.tray_icon.hide()
            logger.info("Tray icon cleaned up")
