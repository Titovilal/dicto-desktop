"""MainWindow — library list (left) + detail view (right) in a splitter.

Selecting a transcript loads it in the detail view; saving or auto-saving
refreshes the list. (The settings modal — the third zone — lands in Phase 6.)
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QSplitter, QWidget

from dicto.i18n import on_language_changed, t
from dicto.services.api.library import LibraryService
from dicto.services.clipboard import Clipboard
from dicto.ui import icons
from dicto.ui.main.detail_view import DetailView
from dicto.ui.main.library_view import LibraryView


class MainWindow(QMainWindow):
    def __init__(
        self,
        library: LibraryService | None = None,
        clipboard: Clipboard | None = None,
    ) -> None:
        super().__init__()
        self.setWindowIcon(icons.app_icon())
        self.resize(1000, 640)

        self._library = library or LibraryService()

        self._library_view = LibraryView(self._library)
        self._detail_view = DetailView(self._library, clipboard)

        # Pad each pane; the splitter itself stays flush.
        left = self._wrap(self._library_view)
        right = self._wrap(self._detail_view)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        splitter.setChildrenCollapsible(False)
        self.setCentralWidget(splitter)

        # Library selection drives the detail view; saves/edits refresh the list.
        self._library_view.transcriptSelected.connect(self._detail_view.load)
        self._library_view.emptied.connect(self._detail_view.show_empty)
        self._detail_view.saved.connect(lambda _id: self._library_view.refresh())
        self._detail_view.statusMessage.connect(self._show_status)

        self.retranslate()
        self._unsub_lang = on_language_changed(lambda _lang: self.retranslate())

    @staticmethod
    def _wrap(widget: QWidget) -> QWidget:
        from PySide6.QtWidgets import QVBoxLayout

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.addWidget(widget)
        return container

    def refresh_library(self) -> None:
        """Reload the library list (called after a transcript is auto-saved)."""
        self._library_view.refresh()

    def _show_status(self, message: str) -> None:
        self.statusBar().showMessage(message, 3000)

    def retranslate(self) -> None:
        self.setWindowTitle(t("window.title"))

    def closeEvent(self, event) -> None:  # noqa: N802 — Qt override
        # Closing hides to tray rather than quitting; the tray is the anchor.
        event.ignore()
        self.hide()
