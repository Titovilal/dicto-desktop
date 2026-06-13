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

from PySide6.QtCore import QRectF, QTimer
from PySide6.QtGui import QColor, QPainter, QPainterPath
from PySide6.QtWidgets import QApplication, QWidget

from dicto.app import DictoApp
from dicto.core.state import AppState

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "screenshots"))

# Modal cards round their corners via setMask (Qt's border-radius doesn't clip a
# widget's opaque children). widget.grab() ignores that mask, so for masked
# cards we re-apply the same rounded clip to the grabbed pixmap — making the
# screenshot match what's actually on screen.
_MODAL_RADIUS = 16


def _grab(widget: QWidget, name: str) -> None:
    """Render the widget; re-clip rounded corners for masked modal cards."""
    QApplication.processEvents()
    pix = widget.grab()
    card = getattr(widget, "_card", None)
    if card is not None:
        dpr = pix.width() / max(1, widget.width())
        r = _MODAL_RADIUS * dpr
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, pix.width(), pix.height()), r, r)
        painter = QPainter(pix)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.setClipPath(path)
        painter.setClipping(False)  # paint outside the path
        # Carve the corners by filling the area outside the rounded path.
        full = QPainterPath()
        full.addRect(QRectF(0, 0, pix.width(), pix.height()))
        painter.setClipPath(full.subtracted(path))
        painter.fillRect(pix.rect(), QColor(255, 255, 255))
        painter.end()
    path_out = os.path.join(OUT, name + ".png")
    pix.save(path_out)
    print("saved", path_out, pix.width(), "x", pix.height())


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

    # Seed a transcript so the library/detail/transform views have content.
    seeded = app_obj.library.create(
        text=(
            "La mitocondria es el orgánulo encargado de producir la energía de "
            "la célula mediante la respiración celular, generando ATP."
        ),
        language="es",
        title="Apuntes de biología",
        tags=["biología"],
    )
    app_obj.window.refresh_library()

    # Seed cached transform results so the structured renderers (flashcards
    # grid, key-points list, summary prose) show real content.
    from dicto.services.api.mocks import get_mock_store

    store = get_mock_store()
    store.save_transform(
        seeded.id, "summary",
        "La mitocondria produce la energía celular (ATP) mediante la "
        "respiración celular. Es esencial para el metabolismo de la célula.",
    )
    store.save_transform(
        seeded.id, "flashcards",
        "Q: ¿Qué produce la mitocondria? / A: ATP, la moneda energética de la célula.\n"
        "Q: ¿Mediante qué proceso? / A: La respiración celular.\n"
        "Q: ¿Por qué es importante? / A: Sin ATP la célula no tiene energía.\n"
        "Q: ¿Cómo se le llama? / A: La central energética de la célula.",
    )

    def shoot() -> None:
        win = app_obj.window
        win.show()
        _grab(win, f"01_main_window{suffix}")

        # Transform tab: Flashcards (cached) — the card grid.
        win._on_transcript_selected(seeded.id)
        win._detail_view._tabs.setCurrentIndex(3)
        _grab(win, f"05_transform{suffix}")

        # Chat view ("ask your notes") with a sample exchange.
        win._open_chat(seeded.id)
        chat = win._chat_view
        chat._add_bubble("¿Qué produce la mitocondria?", user=True)
        chat._add_bubble(
            "La mitocondria produce ATP, la moneda energética de la célula, "
            "mediante la respiración celular.",
            user=False,
        )
        _grab(win, f"06_chat{suffix}")
        win._detail_stack.setCurrentWidget(win._detail_view)

        ov = app_obj.overlay
        ov.set_state(AppState.RECORDING)
        ov.show()
        _grab(ov, f"02_overlay{suffix}")
        ov.hide()

        # Modals: widget.grab() is reliable but can't show the separate dim
        # backdrop window (verify the dim in the running app instead).
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
