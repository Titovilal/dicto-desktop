"""DetailView — the right zone: view/edit one transcript, copy, export.

View/edit a transcript's body, title and tags; save back to the library, copy the
body, export to ``.txt`` / ``.md``. The export content is pure
(``core/export.build_export``); this widget only drives the dialog and clipboard.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from dicto.core import export
from dicto.core.models import Transcript
from dicto.i18n import on_language_changed, t
from dicto.services.api.library import LibraryService
from dicto.services.clipboard import Clipboard


class DetailView(QWidget):
    """View and edit a single transcript; copy and export it."""

    saved = Signal(str)  # transcript id
    statusMessage = Signal(str)  # transient feedback

    def __init__(
        self,
        library: LibraryService,
        clipboard: Clipboard | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._library = library
        self._clipboard = clipboard or Clipboard()
        self._current: Transcript | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        self._title = QLineEdit()
        self._title.setProperty("heading", True)
        root.addWidget(self._title)

        self._meta = QLabel()
        self._meta.setProperty("muted", True)
        root.addWidget(self._meta)

        self._tags = QLineEdit()
        root.addWidget(self._tags)

        self._body = QTextEdit()
        self._body.setAcceptRichText(False)
        root.addWidget(self._body, 1)

        actions = QHBoxLayout()
        self._save_btn = QPushButton()
        self._save_btn.setProperty("accent", True)
        self._save_btn.clicked.connect(self._on_save)
        self._copy_btn = QPushButton()
        self._copy_btn.clicked.connect(self._on_copy)
        self._export_btn = QPushButton()
        self._export_btn.clicked.connect(self._on_export)
        actions.addWidget(self._save_btn)
        actions.addWidget(self._copy_btn)
        actions.addWidget(self._export_btn)
        actions.addStretch(1)
        root.addLayout(actions)

        self.retranslate()
        self.show_empty()
        self._unsub_lang = on_language_changed(lambda _l: self.retranslate())

    # ── load / clear ─────────────────────────────────────────────────────

    def load(self, transcript_id: str) -> None:
        """Show the transcript with this id (no-op if it vanished)."""
        transcript = self._library.get(transcript_id)
        if transcript is None:
            self.show_empty()
            return
        self._current = transcript
        self._title.setText(transcript.title or "")
        self._tags.setText(", ".join(transcript.tags))
        self._body.setPlainText(transcript.text)
        self._meta.setText(self._meta_text(transcript))
        self._set_enabled(True)

    def show_empty(self) -> None:
        """Clear the view when nothing is selected."""
        self._current = None
        self._title.clear()
        self._tags.clear()
        self._body.clear()
        self._meta.setText(t("detail.none"))
        self._set_enabled(False)

    def _set_enabled(self, enabled: bool) -> None:
        for w in (self._title, self._tags, self._body, self._save_btn, self._copy_btn, self._export_btn):
            w.setEnabled(enabled)

    @staticmethod
    def _meta_text(transcript: Transcript) -> str:
        bits = [transcript.created_at]
        if transcript.language:
            bits.append(transcript.language)
        return " · ".join(b for b in bits if b)

    def _parse_tags(self) -> list[str]:
        return [tag.strip() for tag in self._tags.text().split(",") if tag.strip()]

    # ── actions ──────────────────────────────────────────────────────────

    def _edited_transcript(self) -> Transcript | None:
        """The current transcript with the on-screen edits applied (for export)."""
        if self._current is None:
            return None
        from dataclasses import replace

        return replace(
            self._current,
            text=self._body.toPlainText(),
            title=self._title.text().strip() or None,
            tags=self._parse_tags(),
        )

    def _on_save(self) -> None:
        if self._current is None:
            return
        updated = self._library.update(
            self._current.id,
            text=self._body.toPlainText(),
            title=self._title.text().strip() or None,
            tags=self._parse_tags(),
        )
        if updated is not None:
            self._current = updated
            self._meta.setText(self._meta_text(updated))
            self.statusMessage.emit(t("detail.saved"))
            self.saved.emit(updated.id)

    def _on_copy(self) -> None:
        if self._current is None:
            return
        self._clipboard.copy(self._body.toPlainText())
        self.statusMessage.emit(t("detail.copied"))

    def _on_export(self) -> None:
        transcript = self._edited_transcript()
        if transcript is None:
            return
        # A small menu so the user picks the format before the file dialog.
        menu = QMenu(self)
        menu.addAction(t("detail.export_txt"))
        act_md = menu.addAction(t("detail.export_md"))
        chosen = menu.exec(self._export_btn.mapToGlobal(self._export_btn.rect().bottomLeft()))
        if chosen is None:
            return
        fmt = "md" if chosen is act_md else "txt"
        self._export_to_file(transcript, fmt)

    def _export_to_file(self, transcript: Transcript, fmt: str) -> None:
        payload = export.build_export(transcript, fmt)
        filt = "Markdown (*.md)" if fmt == "md" else "Text (*.txt)"
        path, _ = QFileDialog.getSaveFileName(self, t("detail.export"), payload.filename, filt)
        if not path:
            return
        export.write_export(transcript, path, fmt)
        self.statusMessage.emit(t("detail.exported"))

    # ── i18n ─────────────────────────────────────────────────────────────

    def retranslate(self) -> None:
        self._title.setPlaceholderText(t("detail.title_placeholder"))
        self._tags.setPlaceholderText(t("detail.tags_placeholder"))
        self._body.setPlaceholderText(t("detail.body_placeholder"))
        self._save_btn.setText(t("common.save"))
        self._copy_btn.setText(t("detail.copy"))
        self._export_btn.setText(t("detail.export"))
        if self._current is None:
            self._meta.setText(t("detail.none"))
