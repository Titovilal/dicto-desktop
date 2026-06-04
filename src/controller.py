"""
Main controller that orchestrates all application components.
"""

from __future__ import annotations

import traceback
from concurrent.futures import ThreadPoolExecutor
from enum import Enum

from PySide6.QtCore import QObject, Signal, Slot, QTimer

from src.config.settings import Settings
from src.services.hotkey import HotkeyListener, create_hotkey_listener
from src.services.keyboard_actions import KeyboardService
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
    transform_completed = Signal(str, str)  # (format_id, transformed_text)
    transform_failed = Signal(str, str)  # (format_id, error_message)
    error_occurred = Signal(str)
    audio_level_changed = Signal(float)

    cancel_completed = Signal()
    presets_loaded = Signal(list)  # list of preset dicts

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
        self.keyboard = KeyboardService()

        self._cancelled: bool = False

        # Single persistent thread pool – no QThread lifecycle issues
        self._pool = ThreadPoolExecutor(max_workers=1)

        # Connect internal signals (thread-safe delivery to main thread)
        self._transcription_done.connect(self._on_transcribe_finished)
        self._transcription_failed.connect(self._on_transcribe_error)

        self._init_services()
        if self.recorder:
            self.recorder.set_audio_level_callback(self._on_audio_level)

    def _init_services(self):
        try:
            self.recorder = AudioRecorder(
                sample_rate=self.settings.audio_sample_rate,
                channels=self.settings.audio_channels,
                max_duration=self.settings.audio_max_duration,
                input_device=self.settings.audio_input_device,
                include_system_audio=self.settings.audio_include_system_audio,
            )

            api_key = self.settings.transcription_api_key
            if not api_key:
                logger.warning(
                    "No API key found. Set DICTO_API_KEY or add to config.yaml"
                )
            else:
                self.transcriber = Transcriber(
                    api_key=api_key,
                    language=self.settings.transcription_language,
                    model=self.settings.transcription_model,
                    transformation_model=self.settings.transformation_model,
                )

            # Global hotkeys require a supported keyboard backend (X11 on Linux,
            # native on Windows/macOS). On headless/Wayland dev containers pynput
            # cannot acquire a display, so degrade gracefully: keep the GUI usable
            # for development and leave the listeners disabled.
            try:
                self.hotkey_listener = create_hotkey_listener(
                    modifiers=self.settings.hotkey_modifiers,
                    key=self.settings.hotkey_key,
                    on_press=self._on_hotkey_press,
                    on_release=self._on_hotkey_release,
                    on_toggle=self._on_hotkey_toggle,
                    shortcut_id="dicto-record",
                    description="Dicto: Record voice",
                )
            except Exception as e:
                self.hotkey_listener = None
                logger.warning(
                    f"Global hotkeys unavailable on this platform: {e}. "
                    "The GUI will run without hotkey support."
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
        self.fetch_presets()
        logger.info("Controller started successfully")

    def fetch_presets(self):
        """Fetch favorite presets from the API in the background."""
        if not self.transcriber:
            return

        def _do_fetch():
            try:
                assert self.transcriber is not None
                presets = self.transcriber.get_favorite_presets()
                self.presets_loaded.emit(presets)
            except Exception as e:
                logger.warning(f"Failed to fetch presets: {e}")

        self._pool.submit(_do_fetch)

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
            logger.debug(f"State: {self.current_state.value} -> {new_state.value}")
            self.current_state = new_state
            self.state_changed.emit(new_state)

    # ── Hotkey callbacks ─────────────────────────────────────

    def _on_hotkey_press(self):
        if self.current_state in (AppState.IDLE, AppState.SUCCESS):
            self._start_recording()

    def _on_hotkey_release(self):
        if self.current_state == AppState.RECORDING:
            self._stop_recording_and_process()

    def _on_hotkey_toggle(self):
        """Single entry point for toggle-style hotkeys (Wayland portal).

        The Wayland GlobalShortcuts portal fires one neutral activation per tap
        (Deactivated is unreliable across compositors), so the listener can't
        track press/release itself. We decide start vs stop here, from the
        controller's own state — the single source of truth — which avoids the
        listener and controller drifting out of sync.
        """
        if self.current_state in (AppState.IDLE, AppState.SUCCESS):
            self._start_recording()
        elif self.current_state == AppState.RECORDING:
            self._stop_recording_and_process()
        # PROCESSING: ignore taps while a transcription is in flight.

    # ── Recording ────────────────────────────────────────────

    def _start_recording(self):
        if not self.recorder:
            self._handle_error("Audio recorder not initialized")
            return
        try:
            self._cancelled = False
            self._set_state(AppState.RECORDING)
            self.recording_started.emit()
            if not self.recorder.start_recording():
                self._handle_error(
                    "Failed to start recording. Check microphone permissions."
                )
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
                rec_error = self.recorder.get_last_error()
                self._handle_error(rec_error or "No audio recorded")
                return

            self._set_state(AppState.PROCESSING)
            self._transcribe_audio(audio_file_path)
        except Exception as e:
            self._handle_error(f"Error stopping recording: {e}")

    # ── Transcription ────────────────────────────────────────

    def _transcribe_audio(self, audio_file_path: str):
        if not self.transcriber:
            self._handle_error(
                "Transcriber not initialized. Set API key in environment or config.yaml"
            )
            return

        logger.info(f"Transcribing audio: {audio_file_path}")

        def _do_transcribe():
            try:
                assert self.transcriber is not None
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
        if self._cancelled:
            self._cancelled = False
            if self.recorder:
                self.recorder.cleanup_temp_file()
            return
        if self.recorder:
            self.recorder.cleanup_temp_file()
        if ClipboardManager.copy(text):
            self._set_state(AppState.SUCCESS)
            self.transcription_completed.emit(text)
            logger.info(f"Transcription successful: {text}")
            self._perform_auto_actions(
                self.settings.auto_paste, self.settings.auto_enter
            )
        else:
            self._handle_error("Failed to copy to clipboard")

    @Slot(str)
    def _on_transcribe_error(self, error_message: str):
        if self.recorder:
            self.recorder.cleanup_temp_file()
        self._handle_error(error_message)

    # ── Auto-paste / auto-enter ──────────────────────────────

    def _perform_auto_actions(self, auto_paste: bool, auto_enter: bool):
        if auto_paste:
            QTimer.singleShot(100, lambda: self._do_auto_paste(auto_enter))

    def _do_auto_paste(self, auto_enter: bool):
        try:
            self.keyboard.paste()
            if auto_enter:
                QTimer.singleShot(50, self._do_auto_enter)
        except Exception as e:
            logger.error(f"Error performing auto-paste: {e}")

    def _do_auto_enter(self):
        try:
            self.keyboard.enter()
        except Exception as e:
            logger.error(f"Error performing auto-enter: {e}")

    # ── Audio level callback ────────────────────────────────

    def _on_audio_level(self, level: float):
        """Called from audio thread; emit signal for thread-safe delivery."""
        self.audio_level_changed.emit(level)

    # ── Error handling ───────────────────────────────────────

    def _handle_error(self, error_message: str):
        logger.error(error_message)
        self._set_state(AppState.ERROR)
        self.error_occurred.emit(error_message)

    # ── Public slots ─────────────────────────────────────────

    @Slot()
    def cancel(self):
        """Cancel the current operation and return to idle."""
        if self.current_state == AppState.RECORDING:
            if self.recorder and self.recorder.is_recording:
                self.recorder.stop_recording()
                self.recorder.cleanup_temp_file()
            self._set_state(AppState.IDLE)
            self.cancel_completed.emit()
        elif self.current_state == AppState.PROCESSING:
            self._cancelled = True
            self._set_state(AppState.IDLE)
            self.cancel_completed.emit()

    @Slot()
    def return_to_idle(self):
        self._set_state(AppState.IDLE)

    @Slot(object)
    def update_input_device(self, device_id):
        if self.recorder:
            self.recorder.set_input_device(device_id)

    @Slot(bool)
    def update_include_system_audio(self, enabled: bool):
        if self.recorder:
            self.recorder.set_include_system_audio(enabled)

    @Slot()
    def start_recording_manual(self):
        if self.current_state in (AppState.IDLE, AppState.SUCCESS):
            self._start_recording()

    @Slot()
    def stop_recording_manual(self):
        if self.current_state == AppState.RECORDING:
            self._stop_recording_and_process()
        elif self.current_state == AppState.PROCESSING:
            self.cancel()

    # ── Hotkey updates ──────────────────────────────────────────

    def _update_hotkey_listener(
        self,
        listener_attr: str,
        modifiers: list[str],
        key: str,
        on_press,
        on_release,
        on_toggle=None,
        mode: str = "hold",
        suppress_key: bool = False,
        shortcut_id: str = "dicto-shortcut",
        description: str = "Dicto shortcut",
    ):
        """Generic hotkey listener update: stop old -> create new -> start."""
        old_listener = getattr(self, listener_attr)
        if old_listener:
            old_listener.stop()
        new_listener = create_hotkey_listener(
            modifiers=modifiers,
            key=key,
            on_press=on_press,
            on_release=on_release,
            on_toggle=on_toggle,
            mode=mode,
            suppress_key=suppress_key,
            shortcut_id=shortcut_id,
            description=description,
        )
        setattr(self, listener_attr, new_listener)
        new_listener.start()
        logger.info(f"Hotkey updated ({listener_attr}): {'+'.join(modifiers)}+{key}")

    def update_recording_hotkey(self, modifiers: list[str], key: str):
        self._update_hotkey_listener(
            "hotkey_listener",
            modifiers,
            key,
            self._on_hotkey_press,
            self._on_hotkey_release,
            on_toggle=self._on_hotkey_toggle,
            shortcut_id="dicto-record",
            description="Dicto: Record voice",
        )

    # ── Transform ─────────────────────────────────────────────

    @Slot(str, str, str)
    def request_transform(self, format_id: str, text: str, instructions: str):
        """Request a text transformation in the background thread pool."""
        if not self.transcriber:
            self.transform_failed.emit(format_id, "Transcriber not initialized")
            return

        def _do_transform():
            try:
                assert self.transcriber is not None
                result = self.transcriber.transform(text, instructions)
                self.transform_completed.emit(format_id, result)
            except Exception as e:
                self.transform_failed.emit(format_id, str(e))

        self._pool.submit(_do_transform)
