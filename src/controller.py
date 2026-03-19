"""
Main controller that orchestrates all application components.
"""

import traceback
from concurrent.futures import ThreadPoolExecutor
from enum import Enum

from pynput import keyboard
from PySide6.QtCore import QObject, Signal, Slot, QTimer

from src.config.settings import Settings
from src.services.hotkey import HotkeyListener
from src.services.recorder import AudioRecorder
from src.services.transcriber import Transcriber, TranscriptionError, APIKeyError
from src.services.clipboard import ClipboardManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AppState(Enum):
    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"
    SUCCESS = "success"
    ERROR = "error"


class Controller(QObject):
    state_changed = Signal(AppState)
    recording_started = Signal()
    recording_stopped = Signal(float)
    transcription_completed = Signal(str)
    error_occurred = Signal(str)

    # Internal signals to bounce results back to the main thread
    _transcription_done = Signal(str)
    _transcription_failed = Signal(str)

    def __init__(self, settings: Settings):
        super().__init__()
        self.settings = settings
        self.current_state = AppState.IDLE

        self.hotkey_listener: HotkeyListener | None = None
        self.recorder: AudioRecorder | None = None
        self.transcriber: Transcriber | None = None
        self.keyboard_controller = keyboard.Controller()

        # Single persistent thread pool – no QThread lifecycle issues
        self._pool = ThreadPoolExecutor(max_workers=1)

        # Connect internal signals (thread-safe delivery to main thread)
        self._transcription_done.connect(self._on_transcribe_finished)
        self._transcription_failed.connect(self._on_transcribe_error)

        self._init_services()

    def _init_services(self):
        try:
            self.recorder = AudioRecorder(
                sample_rate=self.settings.audio_sample_rate,
                channels=self.settings.audio_channels,
                max_duration=self.settings.audio_max_duration,
            )

            api_key = self.settings.transcription_api_key
            if not api_key:
                logger.warning("No API key found. Set DICTO_API_KEY or add to config.yaml")
            else:
                self.transcriber = Transcriber(
                    api_key=api_key,
                    language=self.settings.transcription_language,
                    model=self.settings.transcription_model,
                )

            self.hotkey_listener = HotkeyListener(
                modifiers=self.settings.hotkey_modifiers,
                key=self.settings.hotkey_key,
                on_press=self._on_hotkey_press,
                on_release=self._on_hotkey_release,
            )
        except Exception as e:
            logger.error(f"Error initializing services: {e}")
            traceback.print_exc()
            raise

    # ── Lifecycle ────────────────────────────────────────────

    def start(self):
        if self.hotkey_listener:
            self.hotkey_listener.start()
        self._set_state(AppState.IDLE)
        logger.info("Controller started successfully")

    def stop(self):
        logger.info("Stopping controller...")
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        if self.recorder and self.recorder.is_recording:
            self.recorder.stop_recording()
        self._pool.shutdown(wait=True, cancel_futures=True)
        if self.recorder:
            self.recorder.close()
        if self.transcriber:
            self.transcriber.close()
        logger.info("Controller stopped")

    # ── State ────────────────────────────────────────────────

    def _set_state(self, new_state: AppState):
        if self.current_state != new_state:
            self.current_state = new_state
            self.state_changed.emit(new_state)

    # ── Hotkey callbacks ─────────────────────────────────────

    def _on_hotkey_press(self):
        if self.current_state in (AppState.IDLE, AppState.SUCCESS):
            self._start_recording()

    def _on_hotkey_release(self):
        if self.current_state == AppState.RECORDING:
            self._stop_recording_and_process()

    # ── Recording ────────────────────────────────────────────

    def _start_recording(self):
        if not self.recorder:
            self._handle_error("Audio recorder not initialized")
            return
        try:
            self._set_state(AppState.RECORDING)
            self.recording_started.emit()
            if not self.recorder.start_recording():
                self._handle_error("Failed to start recording. Check microphone permissions.")
        except Exception as e:
            self._handle_error(f"Error starting recording: {e}")

    def _stop_recording_and_process(self):
        if not self.recorder:
            self._handle_error("Audio recorder not initialized")
            return
        try:
            audio_file_path = self.recorder.stop_recording()
            duration = self.recorder.get_recording_duration()
            self.recording_stopped.emit(duration)

            if not audio_file_path:
                self._handle_error("No audio recorded")
                return

            self._set_state(AppState.PROCESSING)
            self._transcribe_audio(audio_file_path)
        except Exception as e:
            self._handle_error(f"Error stopping recording: {e}")

    # ── Transcription ────────────────────────────────────────

    def _transcribe_audio(self, audio_file_path: str):
        if not self.transcriber:
            self._handle_error("Transcriber not initialized. Set API key in environment or config.yaml")
            return

        logger.info(f"Transcribing audio: {audio_file_path}")

        def _do_transcribe():
            try:
                text = self.transcriber.transcribe(audio_file_path)
                if text:
                    self._transcription_done.emit(text)
                else:
                    self._transcription_failed.emit("Transcription returned empty text")
            except (APIKeyError, TranscriptionError) as e:
                self._transcription_failed.emit(str(e))
            except Exception as e:
                traceback.print_exc()
                self._transcription_failed.emit(f"Unexpected error: {e}")

        self._pool.submit(_do_transcribe)

    @Slot(str)
    def _on_transcribe_finished(self, text: str):
        if self.recorder:
            self.recorder.cleanup_temp_file()
        if ClipboardManager.copy(text):
            self._set_state(AppState.SUCCESS)
            self.transcription_completed.emit(text)
            logger.info(f"Transcription successful: {text}")
            self._perform_auto_actions()
        else:
            self._handle_error("Failed to copy to clipboard")

    @Slot(str)
    def _on_transcribe_error(self, error_message: str):
        if self.recorder:
            self.recorder.cleanup_temp_file()
        self._handle_error(error_message)

    # ── Auto-paste / auto-enter ──────────────────────────────

    def _perform_auto_actions(self):
        if self.settings.auto_paste:
            QTimer.singleShot(100, self._do_auto_paste)

    def _do_auto_paste(self):
        try:
            self.keyboard_controller.press(keyboard.Key.ctrl)
            self.keyboard_controller.press("v")
            self.keyboard_controller.release("v")
            self.keyboard_controller.release(keyboard.Key.ctrl)
            if self.settings.auto_enter:
                QTimer.singleShot(50, self._do_auto_enter)
        except Exception as e:
            logger.error(f"Error performing auto-paste: {e}")

    def _do_auto_enter(self):
        try:
            self.keyboard_controller.press(keyboard.Key.enter)
            self.keyboard_controller.release(keyboard.Key.enter)
        except Exception as e:
            logger.error(f"Error performing auto-enter: {e}")

    # ── Error handling ───────────────────────────────────────

    def _handle_error(self, error_message: str):
        logger.error(error_message)
        self._set_state(AppState.ERROR)
        self.error_occurred.emit(error_message)

    # ── Public slots ─────────────────────────────────────────

    @Slot()
    def return_to_idle(self):
        self._set_state(AppState.IDLE)

    @Slot()
    def start_recording_manual(self):
        if self.current_state in (AppState.IDLE, AppState.SUCCESS):
            self._start_recording()

    @Slot()
    def stop_recording_manual(self):
        if self.current_state == AppState.RECORDING:
            self._stop_recording_and_process()
