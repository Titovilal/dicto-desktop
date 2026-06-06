"""LibraryView — the left zone: a searchable, sortable list of transcripts.

Search/sort/tag-filter the saved transcripts; emit the selected one's id. The
query semantics are pure (``services/api/library.query_transcripts``); this
widget only renders and selects.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from dicto.core.models import Transcript
from dicto.i18n import on_language_changed, t
from dicto.services.api.library import LibraryQuery, LibraryService, SortKey

# Sort options shown in the combo, in display order: (key, i18n key).
_SORTS: tuple[tuple[SortKey, str], ...] = (
    ("created_desc", "library.sort.newest"),
    ("created_asc", "library.sort.oldest"),
    ("title", "library.sort.title"),
)

_ID_ROLE = Qt.ItemDataRole.UserRole


def _preview(transcript: Transcript) -> str:
    """A one-line label for a transcript: its title, or a trimmed body."""
    title = (transcript.title or "").strip()
    if title:
        return title
    body = " ".join(transcript.text.split())
    return (body[:80] + "…") if len(body) > 80 else (body or "—")


class LibraryView(QWidget):
    """List + search + sort + tag filter over the user's transcripts."""

    transcriptSelected = Signal(str)  # transcript id
    emptied = Signal()  # nothing left / nothing selected

    def __init__(self, library: LibraryService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._library = library

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        self._heading = QLabel()
        self._heading.setProperty("heading", True)
        root.addWidget(self._heading)

        self._search = QLineEdit()
        self._search.setClearButtonEnabled(True)
        self._search.textChanged.connect(self._reload)
        root.addWidget(self._search)

        controls = QHBoxLayout()
        self._sort = QComboBox()
        for _key, label_key in _SORTS:
            self._sort.addItem(t(label_key))
        self._sort.currentIndexChanged.connect(self._reload)
        controls.addWidget(self._sort, 1)

        self._tag = QComboBox()
        self._tag.currentIndexChanged.connect(self._reload)
        controls.addWidget(self._tag, 1)
        root.addLayout(controls)

        self._list = QListWidget()
        self._list.currentItemChanged.connect(self._on_current_changed)
        root.addWidget(self._list, 1)

        self._empty = QLabel()
        self._empty.setProperty("muted", True)
        self._empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty.setWordWrap(True)
        root.addWidget(self._empty)

        self.retranslate()
        self.refresh()
        self._unsub_lang = on_language_changed(lambda _l: self.retranslate())

    # ── data ─────────────────────────────────────────────────────────────

    def _current_query(self) -> LibraryQuery:
        sort_key = _SORTS[max(0, self._sort.currentIndex())][0]
        tag = self._tag.currentData()
        return LibraryQuery(text=self._search.text(), tag=tag, sort=sort_key)

    def _reload(self) -> None:
        """Re-run the query and repopulate the list, preserving selection."""
        previous = self._selected_id()
        self._list.blockSignals(True)
        self._list.clear()
        items = self._library.list(self._current_query())
        for transcript in items:
            row = QListWidgetItem(_preview(transcript))
            row.setData(_ID_ROLE, transcript.id)
            self._list.addItem(row)
            if transcript.id == previous:
                self._list.setCurrentItem(row)
        self._list.blockSignals(False)

        has_items = self._list.count() > 0
        self._list.setVisible(has_items)
        self._empty.setVisible(not has_items)

        if not has_items:
            self.emptied.emit()
        elif self._list.currentItem() is None:
            # Selection was filtered out — pick the first row.
            self._list.setCurrentRow(0)
        else:
            self._emit_current()

    def _reload_tags(self) -> None:
        """Rebuild the tag filter, keeping the current choice if still present."""
        current = self._tag.currentData()
        self._tag.blockSignals(True)
        self._tag.clear()
        self._tag.addItem(t("library.tag.all"), None)
        for tag in self._library.all_tags():
            self._tag.addItem(tag, tag)
        # Restore selection.
        idx = self._tag.findData(current)
        self._tag.setCurrentIndex(idx if idx >= 0 else 0)
        self._tag.blockSignals(False)

    def refresh(self) -> None:
        """Reload tags then rows — call after a transcript is added/edited."""
        self._reload_tags()
        self._reload()

    # ── selection ────────────────────────────────────────────────────────

    def _selected_id(self) -> str | None:
        item = self._list.currentItem()
        return item.data(_ID_ROLE) if item is not None else None

    def _on_current_changed(self, *_args: object) -> None:
        self._emit_current()

    def _emit_current(self) -> None:
        transcript_id = self._selected_id()
        if transcript_id is not None:
            self.transcriptSelected.emit(transcript_id)
        else:
            self.emptied.emit()

    # ── i18n ─────────────────────────────────────────────────────────────

    def retranslate(self) -> None:
        self._heading.setText(t("window.library"))
        self._search.setPlaceholderText(t("library.search"))
        self._empty.setText(t("window.empty"))
        # Sort labels (index order matches _SORTS).
        for i, (_key, label_key) in enumerate(_SORTS):
            self._sort.setItemText(i, t(label_key))
        # "All tags" entry; rebuild keeps the tag list itself.
        if self._tag.count() > 0:
            self._tag.setItemText(0, t("library.tag.all"))
