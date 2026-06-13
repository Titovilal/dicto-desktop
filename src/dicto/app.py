"""DictoApp — starts Qt, builds dependencies, wires signals.

This is the only place Qt, the event bus, settings, theme and i18n meet. The
core stays Qt-free; ``app.py`` subscribes to the domain event bus and bridges it
to the UI. For Phase 0 the wiring is small (tray + empty window + live theme and
language), but the shape is what later phases plug into.
"""

from __future__ import annotations

import ctypes
import logging
import signal
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv

from dicto.config.settings import Settings, get_settings
from dicto.core.cleanup import clean_dictation
from dicto.core.events import EventBus
from dicto.core.result_router import route_result
from dicto.i18n import set_language
from dicto.services.api.dictionary import DictionaryService
from dicto.services.api.library import LibraryService
from dicto.services.api.mocks import MockStore, set_mock_store
from dicto.services.api.transform import TransformService
from dicto.utils.logger import get_logger, setup_logging

logger = get_logger(__name__)

_APP_USER_MODEL_ID = "dicto.desktop.3"


def _set_app_user_model_id() -> None:
    """Tell Windows our AppUserModelID so notifications/taskbar group correctly."""
    if sys.platform == "win32":
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(_APP_USER_MODEL_ID)
        except Exception:  # noqa: BLE001
            logger.debug("could not set AppUserModelID", exc_info=True)


class DictoApp:
    """Owns the QApplication and the top-level objects, and wires them."""

    def __init__(self, settings: Settings | None = None) -> None:
        # Import Qt lazily so importing this module (and the pure core) never
        # requires a display / QApplication — keeps unit tests headless.
        from PySide6.QtWidgets import QApplication

        from dicto.orchestrator import RecordingOrchestrator
        from dicto.services.clipboard import Clipboard
        from dicto.services.hotkey import HotkeyListener
        from dicto.services.injector import Injector
        from dicto.ui.main.window import MainWindow
        from dicto.ui.overlay.overlay import Overlay
        from dicto.ui.theme.manager import ThemeManager
        from dicto.ui.tray import Tray

        self.settings = settings or get_settings()

        self.app = QApplication.instance() or QApplication(sys.argv)
        # Fusion honours our stylesheet everywhere (native styles ignore some
        # QSS, especially on popups), giving consistent theming.
        self.app.setStyle("Fusion")
        self.app.setQuitOnLastWindowClosed(False)  # tray keeps us alive

        # i18n: apply the saved language before any widget builds its text.
        set_language(self.settings.appearance.language)

        # Domain event bus (Qt-free); the orchestrator bridges it to Qt.
        self.bus = EventBus()

        # Backend (Phase 4): library + dictionary, mocked in-process for now,
        # wired with a real UTC clock so saved transcripts carry honest stamps.
        set_mock_store(MockStore(clock=lambda: datetime.now(timezone.utc).isoformat()))
        self.library = LibraryService()
        self.dictionary = DictionaryService()
        # Transform (Phase 5): AI presets over a transcript; builds its own
        # API client lazily from the saved key, results cached in the store.
        self.transform = TransformService()

        # Theme: build, then apply so the stylesheet exists before widgets show.
        self.theme = ThemeManager(self.app, theme=self.settings.appearance.theme)
        self.theme.apply()

        # Orchestration: owns recording lifecycle, bridges the bus to Qt.
        self.orchestrator = RecordingOrchestrator(self.settings, self.bus)

        # Delivery (Phase 3): cursor injection with a clipboard fallback. Both
        # share one clipboard so the injected text and the fallback are the same.
        self.clipboard = Clipboard()
        self.injector = Injector(self.clipboard)

        # UI
        self.window = MainWindow(
            self.library, self.clipboard, self.theme, self.transform, self.settings
        )
        hotkey_label = " + ".join(
            part.capitalize()
            for part in (*self.settings.hotkey.modifiers, self.settings.hotkey.key)
        )
        self.tray = Tray(hotkey_label, self.settings.audio.include_system_audio)
        self.overlay = Overlay(self.theme, self.settings)

        # Global hotkey (degrades gracefully where pynput is unavailable).
        mode = self.settings.behavior.recording_mode
        self.hotkey = HotkeyListener(
            self.settings.hotkey.modifiers,
            self.settings.hotkey.key,
            mode=mode,
            on_start=self._on_hotkey_start,
            on_stop=self._on_hotkey_stop,
        )

        self._wire()
        self.hotkey.start()

    def _wire(self) -> None:
        self.tray.openRequested.connect(self._show_window)
        self.tray.dictionaryRequested.connect(self._open_dictionary)
        self.tray.settingsRequested.connect(self._open_settings)
        self.tray.quitRequested.connect(self.quit)
        self.tray.recordRequested.connect(self.orchestrator.toggle)
        self.tray.systemAudioToggled.connect(self._on_system_audio_toggled)

        # Main-window rail intent.
        self.window.recordRequested.connect(self.orchestrator.toggle)
        self.window.dictionaryRequested.connect(self._open_dictionary)
        self.window.settingsRequested.connect(self._open_settings)

        # Orchestrator → UI.
        self.orchestrator.stateChanged.connect(self.tray.set_state)
        self.orchestrator.stateChanged.connect(self.overlay.set_state)
        self.orchestrator.levelChanged.connect(self.overlay.set_level)
        self.orchestrator.transcriptionDone.connect(self._on_transcription_done)

        # Overlay → orchestrator (visual intent → lifecycle).
        self.overlay.stopRequested.connect(self.orchestrator.stop_recording)
        self.overlay.pauseRequested.connect(self.orchestrator.pause)
        self.overlay.resumeRequested.connect(self.orchestrator.resume)
        self.overlay.openAppRequested.connect(self._show_window)

    # ── hotkey callbacks (fire on pynput's thread) ──────────────────────

    def _on_hotkey_start(self) -> None:
        # In toggle mode the matcher only fires start; route through toggle so a
        # second tap stops. In hold mode start begins recording.
        if self.settings.behavior.recording_mode == "toggle":
            self.orchestrator.toggle()
        else:
            self.orchestrator.start_recording()

    def _on_hotkey_stop(self) -> None:
        # Only meaningful in hold mode (key-up stops).
        self.orchestrator.stop_recording()

    def _on_transcription_done(self, text: str) -> None:
        # Clean the dictation, save it, then let the result router decide
        # cursor vs clipboard (with a fallback when injection isn't available).
        if not text:
            return

        if self.settings.behavior.cleanup_enabled:
            text = clean_dictation(text, lang=self.settings.transcription.language)
            if not text:
                return

        # Save every transcript so dictation is never lost. Best-effort — a save
        # failure must not break delivery.
        try:
            self.library.create(text=text, language=self.settings.transcription.language)
            self.window.refresh_library()
        except Exception:  # noqa: BLE001
            logger.warning("failed to save transcript to library", exc_info=True)

        decision = route_result(
            text=text,
            auto_paste=self.settings.behavior.auto_paste,
            auto_enter=self.settings.behavior.auto_enter,
            can_inject=self.injector.available(),
        )

        if decision.inject:
            if not self.injector.inject(text, auto_enter=decision.auto_enter):
                # Injection failed at the last moment — the text is already on
                # the clipboard (the injector staged it), so nothing is lost.
                logger.info("injection failed; text left on clipboard")
        elif decision.clipboard:
            self.clipboard.copy(text)
            if decision.used_fallback:
                logger.info("cursor injection unavailable; copied to clipboard instead")

    def _show_window(self) -> None:
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    def _open_settings(self) -> None:
        # Lazy import + lazy build: the modal only exists once asked for.
        from dicto.ui.main.settings_modal import SettingsModal

        self._show_window()
        if getattr(self, "_settings_modal", None) is None:
            self._settings_modal = SettingsModal(self.theme, self.settings, self.window)
            # Keep the tray's "system audio" check in sync with the modal toggle.
            self._settings_modal._sysaudio.toggled.connect(self.tray.set_system_audio)
        self._settings_modal.open_centered()

    def _on_system_audio_toggled(self, on: bool) -> None:
        self.settings.audio.include_system_audio = on
        self.settings.save()
        modal = getattr(self, "_settings_modal", None)
        if modal is not None:
            modal._sysaudio.setChecked(on)

    def _open_dictionary(self) -> None:
        # Lazy import + lazy build, like the settings modal.
        from dicto.ui.main.dictionary_modal import DictionaryModal

        self._show_window()
        if getattr(self, "_dictionary_modal", None) is None:
            self._dictionary_modal = DictionaryModal(self.dictionary, self.theme, self.window)
        self._dictionary_modal.open_centered()

    def quit(self) -> None:
        logger.info("quitting")
        self.hotkey.stop()
        self.orchestrator.dispose()
        self.overlay.dispose()
        self.tray.dispose()
        self.app.quit()

    def run(self) -> int:
        # Let Ctrl+C work from a console run.
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        self._show_window()
        return self.app.exec()


def main() -> int:
    """Console/entrypoint: ``dicto`` and ``python -m dicto``."""
    load_dotenv()
    setup_logging(logging.INFO)
    _set_app_user_model_id()
    logger.info("starting Dicto")
    return DictoApp().run()
