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
    recordRequested = Signal()
    dictionaryRequested = Signal()
    settingsRequested = Signal()
    quitRequested = Signal()
    systemAudioToggled = Signal(bool)

    def __init__(
        self,
        hotkey_label: str = "",
        system_audio: bool = False,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._hotkey_label = hotkey_label
        self._system_audio = system_audio
        self._state = AppState.IDLE
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
        # Order per the design: state header · record + system audio ·
        # library / dictionary / settings · quit.
        self._act_state = self._menu.addAction("")
        self._act_state.setEnabled(False)
        self._menu.addSeparator()
        self._act_record = self._menu.addAction("")
        self._act_sysaudio = self._menu.addAction("")
        self._act_sysaudio.setCheckable(True)
        self._act_sysaudio.setChecked(self._system_audio)
        self._menu.addSeparator()
        self._act_open = self._menu.addAction("")
        self._act_dictionary = self._menu.addAction("")
        self._act_settings = self._menu.addAction("")
        self._menu.addSeparator()
        self._act_quit = self._menu.addAction("")
        self._act_record.triggered.connect(self.recordRequested)
        self._act_sysaudio.toggled.connect(self.systemAudioToggled)
        self._act_open.triggered.connect(self.openRequested)
        self._act_dictionary.triggered.connect(self.dictionaryRequested)
        self._act_settings.triggered.connect(self.settingsRequested)
        self._act_quit.triggered.connect(self.quitRequested)
        self.retranslate()

    def retranslate(self) -> None:
        self._act_state.setText(f"{t('app.name')} — {t(f'status.{self._state.value}')}")
        record = t("tray.record")
        if self._hotkey_label:
            record = f"{record}\t{self._hotkey_label}"
        self._act_record.setText(record)
        self._act_sysaudio.setText(t("tray.system_audio"))
        self._act_open.setText(t("tray.open"))
        self._act_dictionary.setText(t("rail.dictionary"))
        self._act_settings.setText(t("tray.settings"))
        self._act_quit.setText(t("tray.quit"))

    def set_state(self, state: AppState) -> None:
        """Recolour the icon and update the tooltip/header for the app state."""
        self._state = state
        self._tray.setIcon(icons.status_icon(state.value))
        self._tray.setToolTip(f"{t('app.name')} — {t(f'status.{state.value}')}")
        self._act_state.setText(f"{t('app.name')} — {t(f'status.{state.value}')}")

    def set_system_audio(self, on: bool) -> None:
        """Reflect a settings change made elsewhere (e.g. the settings modal)."""
        self._act_sysaudio.blockSignals(True)
        self._act_sysaudio.setChecked(on)
        self._act_sysaudio.blockSignals(False)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.openRequested.emit()

    def dispose(self) -> None:
        self._unsub_lang()
        self._tray.hide()

    @staticmethod
    def is_available() -> bool:
        return QSystemTrayIcon.isSystemTrayAvailable() and QApplication.instance() is not None
