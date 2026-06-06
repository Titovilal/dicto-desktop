"""System tray — the anchor of the app.

Shows a status-coloured icon and a small menu (Open / Settings / Quit). The
tray text and menu re-localise on ``languageChanged``; the icon recolours when
the app state changes.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from dicto.core.state import AppState
from dicto.i18n import on_language_changed, t
from dicto.ui import icons

logger = logging.getLogger(__name__)


class Tray(QObject):
    """Wraps a QSystemTrayIcon with localised menu and status icon."""

    openRequested = Signal()
    settingsRequested = Signal()
    quitRequested = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._tray = QSystemTrayIcon(icons.status_icon("idle"), parent)
        self._menu = QMenu()
        self._build_menu()
        self._tray.setContextMenu(self._menu)
        self._tray.activated.connect(self._on_activated)
        self.set_state(AppState.IDLE)
        self._tray.show()

        # Re-localise menu and tooltip when the language changes.
        self._unsub_lang = on_language_changed(lambda _lang: self.retranslate())

    def _build_menu(self) -> None:
        self._act_open = self._menu.addAction("")
        self._act_settings = self._menu.addAction("")
        self._menu.addSeparator()
        self._act_quit = self._menu.addAction("")
        self._act_open.triggered.connect(self.openRequested)
        self._act_settings.triggered.connect(self.settingsRequested)
        self._act_quit.triggered.connect(self.quitRequested)
        self.retranslate()

    def retranslate(self) -> None:
        self._act_open.setText(t("tray.open"))
        self._act_settings.setText(t("tray.settings"))
        self._act_quit.setText(t("tray.quit"))

    def set_state(self, state: AppState) -> None:
        """Recolour the icon and update the tooltip for the app state."""
        self._tray.setIcon(icons.status_icon(state.value))
        self._tray.setToolTip(f"{t('app.name')} — {t(f'status.{state.value}')}")

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.openRequested.emit()

    def dispose(self) -> None:
        self._unsub_lang()
        self._tray.hide()

    @staticmethod
    def is_available() -> bool:
        return QSystemTrayIcon.isSystemTrayAvailable() and QApplication.instance() is not None
