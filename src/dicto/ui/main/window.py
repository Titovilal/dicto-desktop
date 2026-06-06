"""MainWindow — the container that will hold the three zones.

For Phase 0 it is intentionally empty: a titled window with a placeholder label,
proving the theme and i18n refresh live. Library / detail / settings-modal land
in later phases. All text comes from ``t()``; all colour from the stylesheet.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow, QVBoxLayout, QWidget

from dicto.i18n import on_language_changed, t
from dicto.ui import icons


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowIcon(icons.app_icon())
        self.resize(900, 600)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(24, 24, 24, 24)

        self._placeholder = QLabel()
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setProperty("muted", True)
        layout.addStretch()
        layout.addWidget(self._placeholder)
        layout.addStretch()

        self.setCentralWidget(central)
        self.retranslate()

        # Refresh text live when the language changes.
        self._unsub_lang = on_language_changed(lambda _lang: self.retranslate())

    def retranslate(self) -> None:
        self.setWindowTitle(t("window.title"))
        self._placeholder.setText(t("window.empty"))

    def closeEvent(self, event) -> None:  # noqa: N802 — Qt override
        # Closing hides to tray rather than quitting; the tray is the anchor.
        event.ignore()
        self.hide()
