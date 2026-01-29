#!/usr/bin/env python3
"""
Voice to Clipboard - Main entry point
A minimalist desktop application for voice-to-text transcription.
"""

import sys
import signal
from pathlib import Path

from dotenv import load_dotenv

# Load .env file before importing other modules that use settings
load_dotenv()

from PySide6.QtWidgets import QApplication  # noqa: E402
from PySide6.QtCore import QTimer, Slot  # noqa: E402

from src.config.settings import get_settings  # noqa: E402
from src.controller import Controller, AppState  # noqa: E402
from src.ui.tray import TrayManager  # noqa: E402
from src.ui.overlay import OverlayWindow  # noqa: E402


class VoiceToClipboardApp:
    """Main application class."""

    controller: Controller | None
    tray_manager: TrayManager | None
    overlay: OverlayWindow | None

    def __init__(self):
        """Initialize application."""
        # Create Qt application
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Voice to Clipboard")
        self.app.setQuitOnLastWindowClosed(False)  # Keep running in tray

        # Load settings
        print("Loading settings...")
        self.settings = get_settings()

        # Create default config if it doesn't exist
        config_path = Path.cwd() / "config.yaml"
        if not config_path.exists():
            print("Creating default config.yaml...")
            self.settings.create_default_config()
            print(
                "Please edit config.yaml and set your OpenAI API key, then restart the app."
            )
            print("You can also set OPENAI_API_KEY environment variable.")

        # Initialize components
        print("Initializing components...")
        self.controller = None
        self.tray_manager = None
        self.overlay = None

        self._init_components()
        self._connect_signals()

        # Setup signal handlers for clean exit
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Timer to allow Python signal handlers to run
        self.timer = QTimer()
        self.timer.timeout.connect(lambda: None)
        self.timer.start(500)

    def _init_components(self):
        """Initialize all application components."""
        try:
            # Initialize controller
            self.controller = Controller(self.settings)

            # Initialize tray manager
            self.tray_manager = TrayManager(self.app, self.settings)

            # Initialize overlay window
            self.overlay = OverlayWindow(
                position=self.settings.overlay_position,
                size=self.settings.overlay_size,
                opacity=self.settings.overlay_opacity,
            )

            print("All components initialized successfully")

        except Exception as e:
            print(f"Failed to initialize components: {e}")
            sys.exit(1)

    def _connect_signals(self):
        """Connect signals between components."""
        assert self.controller is not None
        assert self.tray_manager is not None
        assert self.overlay is not None

        # Controller state changes -> Update UI
        self.controller.state_changed.connect(self._on_state_changed)

        # Controller events -> Update overlay
        self.controller.recording_started.connect(self.overlay.show_recording)
        self.controller.recording_stopped.connect(self._on_recording_stopped)
        self.controller.transcription_completed.connect(
            self._on_transcription_completed
        )
        self.controller.error_occurred.connect(self._on_error)

        # Tray actions
        self.tray_manager.quit_requested.connect(self.quit)

        # Auto-return to idle after success/error overlay hides
        controller = self.controller
        QTimer.singleShot(0, lambda: controller.return_to_idle)

        print("Signals connected")

    @Slot(AppState)
    def _on_state_changed(self, state: AppState):
        """Handle application state changes."""
        assert self.tray_manager is not None
        assert self.overlay is not None

        # Update tray status
        self.tray_manager.update_status(state.value)

        # Update overlay based on state
        if state == AppState.RECORDING:
            self.tray_manager.set_recording_icon()

        elif state == AppState.PROCESSING:
            self.overlay.show_processing()

        elif state == AppState.IDLE:
            self.tray_manager.set_idle_icon()
            # Overlay will auto-hide after success/error

        elif state == AppState.ERROR:
            # Overlay will be updated by error_occurred signal
            pass

    @Slot(float)
    def _on_recording_stopped(self, duration: float):
        """Handle recording stopped event."""
        print(f"Recording stopped, duration: {duration:.1f}s")

    @Slot(str)
    def _on_transcription_completed(self, text: str):
        """Handle successful transcription."""
        assert self.controller is not None
        assert self.tray_manager is not None
        assert self.overlay is not None

        # Update tray with last transcription
        self.tray_manager.update_last_transcription(text)

        # Show success overlay
        self.overlay.show_success()

        # Show success notification
        preview = text[:100] + "..." if len(text) > 100 else text
        self.tray_manager.show_success(f"Copied to clipboard: {preview}")

        # Return to idle after overlay hides
        QTimer.singleShot(1500, self.controller.return_to_idle)

    @Slot(str)
    def _on_error(self, error_message: str):
        """Handle error."""
        assert self.controller is not None
        assert self.tray_manager is not None
        assert self.overlay is not None

        # Show error overlay
        short_message = (
            error_message[:30] + "..." if len(error_message) > 30 else error_message
        )
        self.overlay.show_error(short_message)

        # Show error notification
        self.tray_manager.show_error(error_message)

        # Return to idle after overlay hides
        QTimer.singleShot(3000, self.controller.return_to_idle)

    def _signal_handler(self, signum, frame):
        """Handle system signals for clean shutdown."""
        print(f"\nReceived signal {signum}, shutting down...")
        self.quit()

    def run(self):
        """Start the application."""
        assert self.controller is not None

        print("\n" + "=" * 60)
        print("Voice to Clipboard started!")
        print("=" * 60)
        print(
            f"Hotkey: {'+'.join(self.settings.hotkey_modifiers).upper()} + {self.settings.hotkey_key.upper()}"
        )
        print("Press the hotkey and speak, release to transcribe.")
        print("Check system tray for status and options.")
        print("=" * 60 + "\n")

        try:
            # Start controller
            self.controller.start()

            # Run Qt event loop
            sys.exit(self.app.exec())

        except KeyboardInterrupt:
            print("\nKeyboard interrupt received")
            self.quit()

        except Exception as e:
            print(f"Fatal error: {e}")
            import traceback

            traceback.print_exc()
            self.quit()

    def quit(self):
        """Clean shutdown of the application."""
        print("\nShutting down Voice to Clipboard...")

        # Stop controller
        if self.controller:
            self.controller.stop()

        # Clean up tray
        if self.tray_manager:
            self.tray_manager.cleanup()

        # Close overlay
        if self.overlay:
            self.overlay.close()

        # Quit Qt application
        self.app.quit()

        print("Goodbye!")


def main():
    """Main entry point."""
    try:
        app = VoiceToClipboardApp()
        app.run()
    except Exception as e:
        print(f"Failed to start application: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
