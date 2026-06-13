"""DetailView — the right zone: view/edit one transcript, copy, export.

Styled per the design hand-off: a large title row with actions (edit / copy /
export), a meta row (tag · date · duration · language), a tab bar (only
"Transcripción" is functional — the transform tabs activate in Phase 5) and a
footer with delivery/cleanup hints and a live word count. The export content
is pure (``core/export.build_export``); this widget only drives the dialog and
clipboard.
"""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QTabBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from dicto.core import export
from dicto.core.models import Transcript
from dicto.i18n import on_language_changed, t
from dicto.services.api.library import LibraryService
from dicto.services.clipboard import Clipboard
from dicto.ui import icons
from dicto.ui.theme.manager import ThemeManager
from dicto.ui.theme.tokens import Token

# Tab order per the design; only the first is enabled until Phase 5.
_TABS = (
    "detail.tab.transcript",
    "detail.tab.summary",
    "detail.tab.keypoints",
    "detail.tab.flashcards",
    "detail.tab.rewrite",
    "detail.tab.ask",
)


class DetailView(QWidget):
    """View and edit a single transcript; copy and export it."""

    saved = Signal(str)  # transcript id
    statusMessage = Signal(str)  # transient feedback

    def __init__(
        self,
        library: LibraryService,
        clipboard: Clipboard | None = None,
        theme: ThemeManager | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._library = library
        self._clipboard = clipboard or Clipboard()
        self._theme = theme
        self._current: Transcript | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── header: title + actions, then meta ──────────────────────────
        header = QVBoxLayout()
        header.setContentsMargins(24, 18, 24, 0)
        header.setSpacing(9)

        title_row = QHBoxLayout()
        title_row.setSpacing(6)
        self._title = QLineEdit()
        self._title.setObjectName("detailTitle")
        self._title.setProperty("bare", True)
        title_row.addWidget(self._title, 1)

        self._edit_btn = QPushButton()
        self._edit_btn.setProperty("ghost", True)
        self._edit_btn.setCheckable(True)
        self._edit_btn.toggled.connect(self._set_editing)
        title_row.addWidget(self._edit_btn)

        self._save_btn = QPushButton()
        self._save_btn.setProperty("accent", True)
        self._save_btn.clicked.connect(self._on_save)
        self._save_btn.hide()
        title_row.addWidget(self._save_btn)

        self._copy_btn = self._icon_button("copy")
        self._copy_btn.clicked.connect(self._on_copy)
        title_row.addWidget(self._copy_btn)
        self._export_btn = self._icon_button("download")
        self._export_btn.clicked.connect(self._on_export)
        title_row.addWidget(self._export_btn)
        header.addLayout(title_row)

        self._meta = QLabel()
        self._meta.setProperty("dim", True)
        header.addWidget(self._meta)

        self._tags = QLineEdit()
        self._tags.setProperty("bare", True)
        self._tags.hide()  # only while editing
        header.addWidget(self._tags)

        root.addLayout(header)

        # ── tabs ─────────────────────────────────────────────────────────
        tabs_wrap = QHBoxLayout()
        tabs_wrap.setContentsMargins(24, 8, 24, 0)
        self._tabs = QTabBar()
        self._tabs.setExpanding(False)
        self._tabs.setDrawBase(False)
        for i, _key in enumerate(_TABS):
            self._tabs.addTab("")
            if i > 0:  # transform tabs land in Phase 5
                self._tabs.setTabEnabled(i, False)
        tabs_wrap.addWidget(self._tabs)
        tabs_wrap.addStretch(1)
        root.addLayout(tabs_wrap)

        rule = QFrame()
        rule.setObjectName("tabsRule")
        rule.setFixedHeight(1)
        root.addWidget(rule)

        # ── body ─────────────────────────────────────────────────────────
        body_wrap = QVBoxLayout()
        body_wrap.setContentsMargins(24, 16, 24, 16)
        self._body = QTextEdit()
        self._body.setProperty("bare", True)
        self._body.setAcceptRichText(False)
        self._body.setReadOnly(True)
        self._body.textChanged.connect(self._refresh_word_count)
        body_wrap.addWidget(self._body, 1)
        root.addLayout(body_wrap, 1)

        # ── footer ───────────────────────────────────────────────────────
        footer = QFrame()
        footer.setObjectName("detailFooter")
        foot = QHBoxLayout(footer)
        foot.setContentsMargins(24, 8, 24, 8)
        foot.setSpacing(14)
        self._foot_insert = QLabel()
        self._foot_insert.setProperty("dim", True)
        self._foot_cleanup = QLabel()
        self._foot_cleanup.setProperty("dim", True)
        self._foot_words = QLabel()
        self._foot_words.setProperty("dim", True)
        foot.addWidget(self._foot_insert)
        foot.addWidget(self._foot_cleanup)
        foot.addWidget(self._foot_words)
        foot.addStretch(1)
        root.addWidget(footer)

        self.retranslate()
        self._refresh_icons()
        if theme is not None:
            theme.themeChanged.connect(lambda _e: self._refresh_icons())
        self.show_empty()
        self._unsub_lang = on_language_changed(lambda _l: self.retranslate())

    @staticmethod
    def _icon_button(glyph: str) -> QPushButton:
        btn = QPushButton()
        btn.setProperty("iconBtn", "bordered")
        btn.setProperty("glyph", glyph)
        btn.setFixedSize(32, 32)
        btn.setIconSize(QSize(16, 16))
        return btn

    def _refresh_icons(self) -> None:
        if self._theme is None:
            return
        mid = self._theme.color(Token.TEXT_MUTED)
        for btn in (self._copy_btn, self._export_btn):
            btn.setIcon(icons.svg_icon(btn.property("glyph"), mid, 16))
        self._edit_btn.setIcon(icons.svg_icon("edit", mid, 15))

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
        self._edit_btn.setChecked(False)

    def show_empty(self) -> None:
        """Clear the view when nothing is selected."""
        self._current = None
        self._title.clear()
        self._tags.clear()
        self._body.clear()
        self._meta.setText(t("detail.none"))
        self._edit_btn.setChecked(False)
        self._set_enabled(False)

    def _set_enabled(self, enabled: bool) -> None:
        for w in (self._title, self._tags, self._body, self._save_btn,
                  self._copy_btn, self._export_btn, self._edit_btn):
            w.setEnabled(enabled)

    def _set_editing(self, editing: bool) -> None:
        self._body.setReadOnly(not editing)
        self._title.setReadOnly(not editing)
        self._tags.setVisible(editing)
        self._save_btn.setVisible(editing)

    @staticmethod
    def _meta_text(transcript: Transcript) -> str:
        bits = [transcript.tags[0] if transcript.tags else None,
                transcript.created_at[:10] or None]
        if transcript.duration_seconds:
            m, s = divmod(int(transcript.duration_seconds), 60)
            bits.append(f"{m}:{s:02d}")
        if transcript.language:
            bits.append(transcript.language)
        return "  ·  ".join(b for b in bits if b)

    def _parse_tags(self) -> list[str]:
        return [tag.strip() for tag in self._tags.text().split(",") if tag.strip()]

    def _refresh_word_count(self) -> None:
        words = len(self._body.toPlainText().split())
        self._foot_words.setText(t("detail.words").format(n=words))

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
            self._edit_btn.setChecked(False)
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
        self._edit_btn.setText(t("detail.edit"))
        self._copy_btn.setToolTip(t("detail.copy"))
        self._export_btn.setToolTip(t("detail.export"))
        for i, key in enumerate(_TABS):
            self._tabs.setTabText(i, t(key))
        self._foot_insert.setText("⚡ " + t("detail.foot.insert"))
        self._foot_cleanup.setText("✓ " + t("detail.foot.cleanup"))
        self._refresh_word_count()
        if self._current is None:
            self._meta.setText(t("detail.none"))
