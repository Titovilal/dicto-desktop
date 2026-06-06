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

from dotenv import load_dotenv

from dicto.config.settings import Settings, get_settings
from dicto.core.events import EventBus
from dicto.i18n import set_language
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

        from dicto.ui.main.window import MainWindow
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

        # Domain event bus (Qt-free); later phases publish onto it.
        self.bus = EventBus()

        # Theme: build, then apply so the stylesheet exists before widgets show.
        self.theme = ThemeManager(self.app, theme=self.settings.appearance.theme)
        self.theme.apply()

        # UI
        self.window = MainWindow()
        self.tray = Tray()

        self._wire()

    def _wire(self) -> None:
        self.tray.openRequested.connect(self._show_window)
        self.tray.settingsRequested.connect(self._show_window)
        self.tray.quitRequested.connect(self.quit)

    def _show_window(self) -> None:
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    def quit(self) -> None:
        logger.info("quitting")
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
