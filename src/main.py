#!/usr/bin/env python3
"""
Dicto - Main entry point
A minimalist desktop application for voice-to-text transcription.
"""

from __future__ import annotations

import sys
import signal
from pathlib import Path

# Set Windows AppUserModelID for proper notification branding
# Must be done before creating QApplication
if sys.platform == "win32":
    import ctypes

    app_id = "dicto.desktop.1.0"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)

import os

# Warn Linux users running under Wayland
if sys.platform == "linux" and os.environ.get("XDG_SESSION_TYPE") == "wayland":
    from PySide6.QtWidgets import (
        QApplication,
        QComboBox,
        QVBoxLayout,
        QDialog,
        QLabel,
        QDialogButtonBox,
    )

    _WAYLAND_MESSAGES = {
        "en": {
            "title": "Dicto - Wayland detected",
            "text": (
                "Dicto requires an X11 session to work correctly.\n\n"
                "Global hotkeys and keyboard simulation do not work on Wayland.\n\n"
                "To switch to X11:\n"
                "1. Log out\n"
                "2. On the login screen, select 'Ubuntu on Xorg' (or equivalent)\n"
                "3. Log in and run Dicto again"
            ),
        },
        "es": {
            "title": "Dicto - Wayland detectado",
            "text": (
                "Dicto necesita una sesión X11 para funcionar correctamente.\n\n"
                "Los hotkeys globales y la simulación de teclado no funcionan en Wayland.\n\n"
                "Para cambiar a X11:\n"
                "1. Cierra sesión\n"
                "2. En la pantalla de login, selecciona 'Ubuntu on Xorg' (o equivalente)\n"
                "3. Inicia sesión y vuelve a ejecutar Dicto"
            ),
        },
        "de": {
            "title": "Dicto - Wayland erkannt",
            "text": (
                "Dicto benötigt eine X11-Sitzung, um korrekt zu funktionieren.\n\n"
                "Globale Hotkeys und Tastatursimulation funktionieren unter Wayland nicht.\n\n"
                "So wechselst du zu X11:\n"
                "1. Melde dich ab\n"
                "2. Wähle im Anmeldebildschirm 'Ubuntu on Xorg' (oder äquivalent)\n"
                "3. Melde dich an und starte Dicto erneut"
            ),
        },
        "fr": {
            "title": "Dicto - Wayland détecté",
            "text": (
                "Dicto nécessite une session X11 pour fonctionner correctement.\n\n"
                "Les raccourcis globaux et la simulation clavier ne fonctionnent pas sous Wayland.\n\n"
                "Pour passer à X11 :\n"
                "1. Déconnectez-vous\n"
                "2. Sur l'écran de connexion, sélectionnez 'Ubuntu on Xorg' (ou équivalent)\n"
                "3. Connectez-vous et relancez Dicto"
            ),
        },
        "pt": {
            "title": "Dicto - Wayland detectado",
            "text": (
                "O Dicto precisa de uma sessão X11 para funcionar corretamente.\n\n"
                "Atalhos globais e simulação de teclado não funcionam no Wayland.\n\n"
                "Para mudar para X11:\n"
                "1. Encerre a sessão\n"
                "2. Na tela de login, selecione 'Ubuntu on Xorg' (ou equivalente)\n"
                "3. Faça login e execute o Dicto novamente"
            ),
        },
    }

    _LANG_NAMES = {
        "en": "English",
        "es": "Español",
        "de": "Deutsch",
        "fr": "Français",
        "pt": "Português",
    }

    _app = QApplication(sys.argv)

    _dialog = QDialog()
    _dialog.setWindowTitle("Dicto - Wayland")
    _layout = QVBoxLayout(_dialog)

    _combo = QComboBox()
    for code, name in _LANG_NAMES.items():
        _combo.addItem(name, code)
    _combo.setCurrentIndex(1)  # Default: es
    _layout.addWidget(_combo)

    _label = QLabel(_WAYLAND_MESSAGES["es"]["text"])
    _label.setWordWrap(True)
    _layout.addWidget(_label)

    _buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
    _buttons.accepted.connect(_dialog.accept)
    _layout.addWidget(_buttons)

    def _on_lang_changed(index):
        lang = _combo.itemData(index)
        msgs = _WAYLAND_MESSAGES[lang]
        _dialog.setWindowTitle(msgs["title"])
        _label.setText(msgs["text"])

    _combo.currentIndexChanged.connect(_on_lang_changed)

    _dialog.exec()
    sys.exit(1)

from dotenv import load_dotenv

# Load .env file before importing other modules that use settings
load_dotenv()

from PySide6.QtWidgets import QApplication  # noqa: E402
from PySide6.QtCore import Qt, QTimer, Slot  # noqa: E402
from PySide6.QtGui import QIcon  # noqa: E402

from src.config.settings import get_settings  # noqa: E402
from src.i18n import set_language  # noqa: E402
from src.controller import Controller, AppState  # noqa: E402
from src.ui.tray import TrayManager  # noqa: E402
from src.ui.overlay import OverlayWindow  # noqa: E402
from src.ui.main_window import MainWindow  # noqa: E402
from src.ui.splash import SplashWindow  # noqa: E402
from src.utils.logger import setup_logging, get_logger  # noqa: E402
from src.utils.icons import get_icon_path  # noqa: E402

logger = get_logger(__name__)


class DictoApp:
    """Main application class."""

    controller: Controller | None
    tray_manager: TrayManager | None
    overlay: OverlayWindow | None
    main_window: MainWindow | None
    splash: SplashWindow | None

    def __init__(self):
        """Initialize application."""
        # Create Qt application
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Dicto")
        self.app.setQuitOnLastWindowClosed(False)  # Keep running in tray

        # Load bundled fonts
        self._load_fonts()

        # Enable font antialiasing
        from PySide6.QtGui import QFont

        font = QFont("JetBrains Mono")
        font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
        font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        self.app.setFont(font)

        # Set application icon (taskbar and default window icon)
        icon_path = get_icon_path()
        if icon_path:
            self.app.setWindowIcon(QIcon(str(icon_path)))

        # Show splash window while loading
        self.splash = SplashWindow()
        self.splash.show()
        self.app.processEvents()

        # Load settings
        logger.info("Loading settings...")
        self.settings = get_settings()
        set_language(self.settings.ui_language)

        # Create default config if it doesn't exist
        config_path = Path.cwd() / "config.yaml"
        if not config_path.exists():
            logger.info("Creating default config.yaml...")
            self.settings.create_default_config()
            logger.info(
                "Please edit config.yaml and set your Dicto API key, then restart the app."
            )
            logger.info("You can also set DICTO_API_KEY environment variable.")

        # Initialize components
        logger.info("Initializing components...")
        self.controller = None
        self.tray_manager = None
        self.overlay = None
        self.main_window = None
        self._in_edit_flow = False

        self._init_components()
        self._connect_signals()

        # Close splash window
        self.splash.close()
        self.splash = None

        # Setup signal handlers for clean exit
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Timer to allow Python signal handlers to run
        self.timer = QTimer()
        self.timer.timeout.connect(lambda: None)
        self.timer.start(500)

    def _load_fonts(self):
        """Load bundled JetBrains Mono font files."""
        from PySide6.QtGui import QFontDatabase

        fonts_dir = Path(__file__).parent.parent / "assets" / "fonts"
        if fonts_dir.is_dir():
            for font_file in fonts_dir.glob("*.ttf"):
                font_id = QFontDatabase.addApplicationFont(str(font_file))
                if font_id < 0:
                    logger.warning(f"Failed to load font: {font_file.name}")
                else:
                    logger.debug(f"Loaded font: {font_file.name}")

    def _init_components(self):
        """Initialize all application components."""
        try:
            # Initialize controller
            self.controller = Controller(self.settings)

            # Initialize tray manager
            self.tray_manager = TrayManager(self.app)

            # Initialize overlay window
            self.overlay = OverlayWindow(
                position=self.settings.overlay_position,
                size=self.settings.overlay_size,
                opacity=self.settings.overlay_opacity,
            )

            # Initialize main window
            self.main_window = MainWindow(self.settings)
            self.main_window.show()

            logger.info("All components initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            sys.exit(1)

    def _connect_signals(self):
        """Connect signals between components."""
        assert self.controller is not None
        assert self.tray_manager is not None
        assert self.overlay is not None
        assert self.main_window is not None

        # Controller state changes -> Update UI
        self.controller.state_changed.connect(self._on_state_changed)

        # Controller events -> Update overlay
        self.controller.recording_started.connect(self._on_recording_started_overlay)
        self.controller.recording_stopped.connect(self._on_recording_stopped)
        self.controller.transcription_completed.connect(
            self._on_transcription_completed
        )
        self.controller.error_occurred.connect(self._on_error)

        # Controller events -> Update main window
        # recording_started -> main window is handled in _on_recording_started_overlay
        self.controller.transcription_completed.connect(
            self.main_window.update_transcription
        )

        # Main window actions -> Controller
        self.main_window.play_clicked.connect(self.controller.start_recording_manual)
        self.main_window.stop_clicked.connect(self.controller.stop_recording_manual)
        self.main_window.cancel_clicked.connect(self.controller.cancel)
        self.main_window.transform_requested.connect(self.controller.request_transform)

        # Controller transform results -> Main window
        self.controller.transform_completed.connect(
            self.main_window.on_transform_completed
        )
        self.controller.transform_failed.connect(self.main_window.on_transform_failed)

        # Presets loaded -> Main window
        self.controller.presets_loaded.connect(self.main_window.set_presets)

        # Audio level -> waveform widgets
        self.controller.audio_level_changed.connect(
            self.main_window.waveform.set_level, Qt.ConnectionType.QueuedConnection
        )
        self.controller.audio_level_changed.connect(
            self.overlay.waveform_recording.set_level,
            Qt.ConnectionType.QueuedConnection,
        )
        self.controller.audio_level_changed.connect(
            self.overlay.waveform_editing.set_level, Qt.ConnectionType.QueuedConnection
        )

        # Edit selection signals -> UI state updates
        self.controller.edit_started.connect(self._on_edit_started)
        self.controller.edit_completed.connect(self._on_edit_completed)
        self.controller.edit_failed.connect(self._on_error)

        # Hotkey changes -> Controller
        self.main_window.recording_hotkey_changed.connect(
            self.controller.update_recording_hotkey
        )
        self.main_window.edit_hotkey_changed.connect(self.controller.update_edit_hotkey)

        # Overlay record/stop buttons
        self.overlay.record_requested.connect(self.controller.start_recording_manual)
        self.overlay.stop_requested.connect(self.controller.stop_recording_manual)

        # Persistent overlay setting
        self.main_window.persistent_overlay_changed.connect(self.overlay.set_persistent)
        if self.settings.persistent_overlay:
            self.overlay.set_persistent(True)

        # Tray actions
        self.tray_manager.quit_requested.connect(self.quit)
        self.tray_manager.show_window_requested.connect(self._show_main_window)
        self.tray_manager.open_config_requested.connect(
            self.main_window.show_settings_tab
        )

        logger.info("Signals connected")

    @Slot()
    def _on_recording_started_overlay(self):
        """Show recording state on overlay and main window."""
        assert self.overlay is not None
        assert self.main_window is not None
        if self._in_edit_flow:
            self.overlay.show_editing()
            self.main_window.set_editing_state()
        else:
            self.overlay.show_recording()
            self.main_window.set_recording_state()

    @Slot(AppState)
    def _on_state_changed(self, state: AppState):
        """Handle application state changes."""
        assert self.tray_manager is not None
        assert self.overlay is not None
        assert self.main_window is not None

        # Update tray status
        self.tray_manager.update_status(state.value)

        # Update main window status
        self.main_window.update_status(state.value)

        # Update overlay based on state
        if state == AppState.PROCESSING:
            self.overlay.show_processing()
            self.main_window.set_processing_state()

        elif state == AppState.IDLE:
            self.overlay.show_idle()
            self.main_window.set_idle_state()

        elif state == AppState.ERROR:
            # Overlay will be updated by error_occurred signal
            self.main_window.set_idle_state()

    @Slot(float)
    def _on_recording_stopped(self, duration: float):
        """Handle recording stopped event."""
        logger.info(f"Recording stopped, duration: {duration:.1f}s")

    @Slot(str)
    def _on_transcription_completed(self, text: str):
        """Handle successful transcription."""
        assert self.controller is not None
        assert self.tray_manager is not None
        assert self.overlay is not None
        assert self.main_window is not None

        # Update main window with transcription
        self.main_window.update_transcription(text)

        # Show success overlay
        self.overlay.show_success()

        # Return to idle after overlay hides
        QTimer.singleShot(1500, self.controller.return_to_idle)

    @Slot(str)
    def _on_error(self, error_message: str):
        """Handle error."""
        assert self.controller is not None
        assert self.tray_manager is not None
        assert self.overlay is not None

        self._in_edit_flow = False
        # Show error overlay
        short_message = (
            error_message[:30] + "..." if len(error_message) > 30 else error_message
        )
        self.overlay.show_error(short_message)

        # Show error notification
        self.tray_manager.show_error(error_message)

        # Return to idle after overlay hides
        QTimer.singleShot(3000, self.controller.return_to_idle)

    @Slot()
    def _on_edit_started(self):
        """Handle edit selection started."""
        assert self.overlay is not None
        assert self.main_window is not None
        self._in_edit_flow = True
        self.overlay.show_editing()

    @Slot(str)
    def _on_edit_completed(self, text: str):
        """Handle edit selection completed."""
        assert self.controller is not None
        assert self.overlay is not None
        assert self.tray_manager is not None

        self._in_edit_flow = False
        self.overlay.show_success()

        QTimer.singleShot(1500, self.controller.return_to_idle)

    @Slot()
    def _show_main_window(self):
        """Show and bring main window to front."""
        if self.main_window:
            self.main_window.show()
            self.main_window.raise_()
            self.main_window.activateWindow()

    def _signal_handler(self, signum, frame):
        """Handle system signals for clean shutdown."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.quit()

    def run(self):
        """Start the application."""
        assert self.controller is not None

        logger.info("=" * 60)
        logger.info("Dicto started!")
        logger.info("=" * 60)
        logger.info(
            f"Hotkey: {'+'.join(self.settings.hotkey_modifiers).upper()} + {self.settings.hotkey_key.upper()}"
        )
        logger.info(
            f"Edit hotkey: {'+'.join(self.settings.edit_hotkey_modifiers).upper()} + {self.settings.edit_hotkey_key.upper()}"
        )
        logger.info("Press the hotkey and speak, release to transcribe.")
        logger.info("Select text and press edit hotkey to transform.")
        logger.info("Check system tray for status and options.")
        logger.info("=" * 60)

        try:
            # Start controller
            self.controller.start()

            # Run Qt event loop
            sys.exit(self.app.exec())

        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            self.quit()

        except Exception as e:
            logger.error(f"Fatal error: {e}")
            import traceback

            traceback.print_exc()
            self.quit()

    def quit(self):
        """Clean shutdown of the application."""
        logger.info("Shutting down Dicto...")

        # Cancel any active operation, then stop controller
        if self.controller:
            self.controller.cancel()
            self.controller.stop()

        # Clean up tray
        if self.tray_manager:
            self.tray_manager.cleanup()

        # Close overlay
        if self.overlay:
            self.overlay.close()

        # Close main window
        if self.main_window:
            self.main_window.close()

        # Quit Qt application
        self.app.quit()

        logger.info("Goodbye!")


def main():
    """Main entry point."""
    setup_logging()
    try:
        app = DictoApp()
        app.run()
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
