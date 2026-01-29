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
            print("Audio recorder initialized")

            # Initialize transcriber
            api_key = self.settings.transcription_api_key
            provider = self.settings.transcription_provider
            if not api_key:
                env_var = "GROQ_API_KEY" if provider == "groq" else "OPENAI_API_KEY"
                print(
                    f"Warning: No API key found. Set {env_var} environment variable or add to config.yaml"
                )
            else:
                self.transcriber = Transcriber(
                    api_key=api_key,
                    language=self.settings.transcription_language,
                    provider=provider,
                )
                print(f"Transcriber initialized (provider: {provider})")

            # Initialize hotkey listener
            self.hotkey_listener = HotkeyListener(
                modifiers=self.settings.hotkey_modifiers,
                key=self.settings.hotkey_key,
                on_press=self._on_hotkey_press,
                on_release=self._on_hotkey_release,
            )
            print("Hotkey listener initialized")

        except Exception as e:
            print(f"Error initializing services: {e}")
            traceback.print_exc()
            raise

    def start(self):
        """Start the controller and all services."""
        try:
            # Start hotkey listener
            if self.hotkey_listener:
                self.hotkey_listener.start()

            self._set_state(AppState.IDLE)
            print("Controller started successfully")

        except Exception as e:
            print(f"Error starting controller: {e}")
            traceback.print_exc()
            raise

    def stop(self):
        """Stop the controller and clean up resources."""
        print("Stopping controller...")

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

        print("Controller stopped")

    def _set_state(self, new_state: AppState):
        """
        Set application state and emit signal.

        Args:
            new_state: New application state
        """
        if self.current_state != new_state:
            self.current_state = new_state
            self.state_changed.emit(new_state)
            print(f"State changed: {new_state.value}")

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
        try:
            self._set_state(AppState.RECORDING)
            self.recording_started.emit()

            if self.recorder.start_recording():
                print("Recording started")
            else:
                self._handle_error(
                    "Failed to start recording. Check microphone permissions."
                )

        except Exception as e:
            self._handle_error(f"Error starting recording: {e}")

    def _stop_recording_and_process(self):
        """Stop recording and start transcription process."""
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

            print(f"Transcribing audio: {audio_file_path}")

            # Transcribe
            text = self.transcriber.transcribe(audio_file_path)

            if not text:
                self._handle_error("Transcription returned empty text")
                return

            # Copy to clipboard
            if ClipboardManager.copy(text):
                self._set_state(AppState.SUCCESS)
                self.transcription_completed.emit(text)
                print(f"Transcription successful: {text}")

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
            # Small delay to ensure clipboard is ready, then paste
            QTimer.singleShot(100, self._do_auto_paste)

    def _do_auto_paste(self):
        """Execute Ctrl+V keystroke."""
        try:
            self.keyboard_controller.press(keyboard.Key.ctrl)
            self.keyboard_controller.press("v")
            self.keyboard_controller.release("v")
            self.keyboard_controller.release(keyboard.Key.ctrl)
            print("Auto-paste: Ctrl+V executed")

            if self.settings.auto_enter:
                # Small delay before Enter
                QTimer.singleShot(50, self._do_auto_enter)

        except Exception as e:
            print(f"Error performing auto-paste: {e}")

    def _do_auto_enter(self):
        """Execute Enter keystroke."""
        try:
            self.keyboard_controller.press(keyboard.Key.enter)
            self.keyboard_controller.release(keyboard.Key.enter)
            print("Auto-enter: Enter executed")

        except Exception as e:
            print(f"Error performing auto-enter: {e}")

    def _handle_error(self, error_message: str):
        """
        Handle error and set error state.

        Args:
            error_message: Error message to display
        """
        print(f"ERROR: {error_message}")
        self._set_state(AppState.ERROR)
        self.error_occurred.emit(error_message)

        # Clean up temporary file if exists
        if self.recorder:
            self.recorder.cleanup_temp_file()

    @Slot()
    def return_to_idle(self):
        """Return to idle state (called after success or error display)."""
        self._set_state(AppState.IDLE)

    def get_state(self) -> AppState:
        """Get current application state."""
        return self.current_state
