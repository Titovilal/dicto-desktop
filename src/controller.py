"""
Main controller that orchestrates all application components.
"""

from PySide6.QtCore import QObject, Signal, Slot, QTimer
from enum import Enum
import traceback

from pynput import keyboard

from src.config.settings import Settings
from src.services.hotkey import HotkeyListener
from src.services.recorder import AudioRecorder
from src.services.transcriber import Transcriber, TranscriptionError, APIKeyError
from src.services.clipboard import ClipboardManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AppState(Enum):
    """Application states."""

    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"
    SUCCESS = "success"
    ERROR = "error"


class Controller(QObject):
    """Main application controller."""

    # Signals for state changes
    state_changed = Signal(AppState)
    recording_started = Signal()
    recording_stopped = Signal(float)  # duration in seconds
    transcription_completed = Signal(str)  # transcribed text
    error_occurred = Signal(str)  # error message

    # Internal signals for thread-safe timer scheduling
    # (QTimer.singleShot must be called from the Qt main thread)
    _auto_paste_requested = Signal()
    _auto_enter_requested = Signal()

    hotkey_listener: HotkeyListener | None
    recorder: AudioRecorder | None
    transcriber: Transcriber | None

    def __init__(self, settings: Settings):
        """
        Initialize controller.

        Args:
            settings: Application settings
        """
        super().__init__()

        self.settings = settings
        self.current_state = AppState.IDLE

        # Initialize services
        self.hotkey_listener = None
        self.recorder = None
        self.transcriber = None
        self.keyboard_controller = keyboard.Controller()

        # Connect internal signals for thread-safe timer scheduling
        self._auto_paste_requested.connect(self._schedule_auto_paste)
        self._auto_enter_requested.connect(self._schedule_auto_enter)

        self._init_services()

    def _init_services(self):
        """Initialize all services."""
        try:
            # Initialize audio recorder
            self.recorder = AudioRecorder(
                sample_rate=self.settings.audio_sample_rate,
                channels=self.settings.audio_channels,
                max_duration=self.settings.audio_max_duration,
            )
            logger.info("Audio recorder initialized")

            # Initialize transcriber
            api_key = self.settings.transcription_api_key
            provider = self.settings.transcription_provider
            if not api_key:
                env_var = "GROQ_API_KEY" if provider == "groq" else "OPENAI_API_KEY"
                logger.warning(
                    f"No API key found. Set {env_var} environment variable or add to config.yaml"
                )
            else:
                self.transcriber = Transcriber(
                    api_key=api_key,
                    language=self.settings.transcription_language,
                    provider=provider,
                )
                logger.info(f"Transcriber initialized (provider: {provider})")

            # Initialize hotkey listener
            self.hotkey_listener = HotkeyListener(
                modifiers=self.settings.hotkey_modifiers,
                key=self.settings.hotkey_key,
                on_press=self._on_hotkey_press,
                on_release=self._on_hotkey_release,
            )
            logger.info("Hotkey listener initialized")

        except Exception as e:
            logger.error(f"Error initializing services: {e}")
            traceback.print_exc()
            raise

    def start(self):
        """Start the controller and all services."""
        try:
            # Start hotkey listener
            if self.hotkey_listener:
                self.hotkey_listener.start()

            self._set_state(AppState.IDLE)
            logger.info("Controller started successfully")

        except Exception as e:
            logger.error(f"Error starting controller: {e}")
            traceback.print_exc()
            raise

    def stop(self):
        """Stop the controller and clean up resources."""
        logger.info("Stopping controller...")

        # Stop hotkey listener
        if self.hotkey_listener:
            self.hotkey_listener.stop()

        # Stop recording if active
        if self.recorder and self.recorder.is_recording:
            self.recorder.stop_recording()

        # Clean up resources
        if self.recorder:
            self.recorder.close()

        if self.transcriber:
            self.transcriber.close()

        logger.info("Controller stopped")

    def _set_state(self, new_state: AppState):
        """
        Set application state and emit signal.

        Args:
            new_state: New application state
        """
        if self.current_state != new_state:
            self.current_state = new_state
            self.state_changed.emit(new_state)
            logger.debug(f"State changed: {new_state.value}")

    def _on_hotkey_press(self):
        """Callback when hotkey is pressed - start recording."""
        if self.current_state == AppState.IDLE:
            self._start_recording()

    def _on_hotkey_release(self):
        """Callback when hotkey is released - stop recording and process."""
        if self.current_state == AppState.RECORDING:
            self._stop_recording_and_process()

    def _start_recording(self):
        """Start audio recording."""
        if self.recorder is None:
            self._handle_error("Audio recorder not initialized")
            return

        try:
            self._set_state(AppState.RECORDING)
            self.recording_started.emit()

            if self.recorder.start_recording():
                logger.info("Recording started")
            else:
                self._handle_error(
                    "Failed to start recording. Check microphone permissions."
                )

        except Exception as e:
            self._handle_error(f"Error starting recording: {e}")

    def _stop_recording_and_process(self):
        """Stop recording and start transcription process."""
        if self.recorder is None:
            self._handle_error("Audio recorder not initialized")
            return

        try:
            # Stop recording
            audio_file_path = self.recorder.stop_recording()
            duration = self.recorder.get_recording_duration()

            self.recording_stopped.emit(duration)

            if not audio_file_path:
                self._handle_error("No audio recorded")
                return

            # Start processing
            self._set_state(AppState.PROCESSING)
            self._transcribe_audio(audio_file_path)

        except Exception as e:
            self._handle_error(f"Error stopping recording: {e}")

    def _transcribe_audio(self, audio_file_path: str):
        """
        Transcribe audio file and copy to clipboard.

        Args:
            audio_file_path: Path to audio file
        """
        try:
            # Check if transcriber is initialized
            if not self.transcriber:
                self._handle_error(
                    "Transcriber not initialized. Please set API key in environment or config.yaml"
                )
                return

            logger.info(f"Transcribing audio: {audio_file_path}")

            # Transcribe
            text = self.transcriber.transcribe(audio_file_path)

            if not text:
                self._handle_error("Transcription returned empty text")
                return

            # Copy to clipboard
            if ClipboardManager.copy(text):
                self._set_state(AppState.SUCCESS)
                self.transcription_completed.emit(text)
                logger.info(f"Transcription successful: {text}")

                # Auto-paste and auto-enter if enabled
                self._perform_auto_actions()

                # Return to idle after a short delay (handled by UI)
            else:
                self._handle_error("Failed to copy to clipboard")

        except APIKeyError as e:
            self._handle_error(f"API Key Error: {e}")

        except TranscriptionError as e:
            self._handle_error(f"Transcription Error: {e}")

        except Exception as e:
            self._handle_error(f"Unexpected error during transcription: {e}")
            traceback.print_exc()

        finally:
            # Clean up temporary audio file
            if self.recorder:
                self.recorder.cleanup_temp_file()

    def _perform_auto_actions(self):
        """Perform auto-paste (Ctrl+V) and auto-enter if enabled."""
        if self.settings.auto_paste:
            # Emit signal to schedule timer on Qt main thread
            self._auto_paste_requested.emit()

    @Slot()
    def _schedule_auto_paste(self):
        """Schedule auto-paste with delay (runs on Qt main thread)."""
        QTimer.singleShot(100, self._do_auto_paste)

    @Slot()
    def _schedule_auto_enter(self):
        """Schedule auto-enter with delay (runs on Qt main thread)."""
        QTimer.singleShot(50, self._do_auto_enter)

    def _do_auto_paste(self):
        """Execute Ctrl+V keystroke."""
        try:
            self.keyboard_controller.press(keyboard.Key.ctrl)
            self.keyboard_controller.press("v")
            self.keyboard_controller.release("v")
            self.keyboard_controller.release(keyboard.Key.ctrl)
            logger.debug("Auto-paste: Ctrl+V executed")

            if self.settings.auto_enter:
                # Emit signal to schedule timer on Qt main thread
                self._auto_enter_requested.emit()

        except Exception as e:
            logger.error(f"Error performing auto-paste: {e}")

    def _do_auto_enter(self):
        """Execute Enter keystroke."""
        try:
            self.keyboard_controller.press(keyboard.Key.enter)
            self.keyboard_controller.release(keyboard.Key.enter)
            logger.debug("Auto-enter: Enter executed")

        except Exception as e:
            logger.error(f"Error performing auto-enter: {e}")

    def _handle_error(self, error_message: str):
        """
        Handle error and set error state.

        Args:
            error_message: Error message to display
        """
        logger.error(error_message)
        self._set_state(AppState.ERROR)
        self.error_occurred.emit(error_message)

        # Clean up temporary file if exists
        if self.recorder:
            self.recorder.cleanup_temp_file()

    @Slot()
    def return_to_idle(self):
        """Return to idle state (called after success or error display)."""
        self._set_state(AppState.IDLE)

    @Slot()
    def start_recording_manual(self):
        """Start recording manually (from UI button)."""
        if self.current_state == AppState.IDLE:
            self._start_recording()

    @Slot()
    def stop_recording_manual(self):
        """Stop recording manually (from UI button)."""
        if self.current_state == AppState.RECORDING:
            self._stop_recording_and_process()
