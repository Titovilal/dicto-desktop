"""Launch the app, render each view, and save screenshots to ``screenshots/``.

A dev aid for visual iteration: lets an agent (or you) *see* the UI without a
human at the keyboard. It boots the real ``DictoApp``, shows each surface
(main window, overlay, settings modal, dictionary modal), and grabs each one.

Modals are frameless + translucent. On Windows neither ``grabWindow(winId)``
(renders black) nor desktop-region capture (frameless geometry is unreliable)
works, so we render each widget with ``widget.grab()``. The translucent margin
around a modal's rounded card paints as the widget's base colour rather than
true transparency, but the card, its border and rounded corners render exactly
— which is what matters for visual iteration.

Usage::

    PYTHONPATH=src .venv/Scripts/python.exe scripts/screenshot.py            # light
    PYTHONPATH=src .venv/Scripts/python.exe scripts/screenshot.py --theme dark
"""

from __future__ import annotations

import argparse
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "windows")

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QWidget

from dicto.app import DictoApp
from dicto.core.state import AppState

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "screenshots"))


def _grab(widget: QWidget, name: str) -> None:
    """Render the widget itself (reliable for frameless translucent modals)."""
    QApplication.processEvents()
    pix = widget.grab()
    path = os.path.join(OUT, name + ".png")
    pix.save(path)
    print("saved", path, pix.width(), "x", pix.height())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--theme", choices=("light", "dark"), default="light")
    args = parser.parse_args()

    os.makedirs(OUT, exist_ok=True)

    app_obj = DictoApp()
    app = app_obj.app
    if args.theme != app_obj.settings.appearance.theme:
        app_obj.theme.set_theme(args.theme)
    suffix = "" if args.theme == "light" else "_dark"

    def shoot() -> None:
        win = app_obj.window
        win.show()
        _grab(win, f"01_main_window{suffix}")

        ov = app_obj.overlay
        ov.set_state(AppState.RECORDING)
        ov.show()
        _grab(ov, f"02_overlay{suffix}")
        ov.hide()

        app_obj._open_settings()
        _grab(app_obj._settings_modal, f"03_settings{suffix}")
        app_obj._settings_modal.close()

        app_obj._open_dictionary()
        _grab(app_obj._dictionary_modal, f"04_dictionary{suffix}")

        app.quit()

    QTimer.singleShot(700, shoot)
    app_obj._show_window()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
