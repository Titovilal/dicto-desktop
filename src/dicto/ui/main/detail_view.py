"""DetailView — the right zone: view/edit one transcript, copy, export.

Styled per the design hand-off: a large title row with actions (edit / copy /
export), a meta row (tag · date · duration · language), a tab bar (Transcript
plus AI transform tabs — summary/key-points/flashcards/rewrite, each generated
on demand and cached; the Ask tab routes to the chat view) and a footer with
delivery/cleanup hints and a live word count. The export content is pure
(``core/export.build_export``); this widget only drives the dialog and clipboard.
"""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QTabBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from dicto.config.settings import Settings, get_settings
from dicto.core import export
from dicto.core.models import Transcript
from dicto.i18n import on_language_changed, t
from dicto.services.api.library import LibraryService
from dicto.services.api.transform import TransformService
from dicto.services.clipboard import Clipboard
from dicto.transform import presets as preset_lib
from dicto.ui import icons
from dicto.ui.main.transform_render import render_result
from dicto.ui.main.transform_worker import run_transform
from dicto.ui.theme.manager import ThemeManager
from dicto.ui.theme.tokens import Token

# Tab order per the design: transcript, then the transform presets, then Ask.
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
    askRequested = Signal(str)  # transcript id — switch to the chat view

    def __init__(
        self,
        library: LibraryService,
        clipboard: Clipboard | None = None,
        theme: ThemeManager | None = None,
        transform: TransformService | None = None,
        settings: Settings | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._library = library
        self._clipboard = clipboard or Clipboard()
        self._theme = theme
        self._transform = transform or TransformService()
        self._settings = settings or get_settings()
        self._current: Transcript | None = None
        self._busy = False

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
        # Bottom -1 pulls the bar onto the rule below so the selected tab's 2px
        # underline overlaps the 1px divider into one continuous baseline.
        tabs_wrap.setContentsMargins(24, 8, 24, -1)
        self._tabs = QTabBar()
        self._tabs.setExpanding(False)
        self._tabs.setDrawBase(False)
        for _key in _TABS:
            self._tabs.addTab("")
        self._tabs.currentChanged.connect(self._on_tab_changed)
        tabs_wrap.addWidget(self._tabs)
        tabs_wrap.addStretch(1)
        root.addLayout(tabs_wrap)

        rule = QFrame()
        rule.setObjectName("tabsRule")
        rule.setFixedHeight(1)
        root.addWidget(rule)

        # ── body: a stack of [transcript editor | transform result] ────────
        self._stack = QStackedWidget()

        body_page = QWidget()
        body_wrap = QVBoxLayout(body_page)
        body_wrap.setContentsMargins(24, 16, 24, 16)
        self._body = QTextEdit()
        self._body.setProperty("bare", True)
        self._body.setAcceptRichText(False)
        self._body.setReadOnly(True)
        self._body.textChanged.connect(self._refresh_word_count)
        body_wrap.addWidget(self._body, 1)
        self._stack.addWidget(body_page)

        # Transform result page: a header ("✦ Resumen" + cached chip + a small
        # Generate/Regenerate) over a scroll area that holds the rendered result.
        xform_page = QWidget()
        xform_wrap = QVBoxLayout(xform_page)
        xform_wrap.setContentsMargins(24, 16, 24, 16)
        xform_wrap.setSpacing(12)

        head = QHBoxLayout()
        head.setSpacing(8)
        self._xform_icon = QLabel()
        self._xform_head = QLabel()
        self._xform_head.setObjectName("xformHead")
        self._xform_cache = QLabel()
        self._xform_cache.setObjectName("cacheChip")
        self._xform_gen = QPushButton()
        self._xform_gen.setObjectName("xformGen")
        self._xform_gen.clicked.connect(self._on_generate)
        head.addWidget(self._xform_icon)
        head.addWidget(self._xform_head)
        head.addStretch(1)
        head.addWidget(self._xform_cache)
        head.addWidget(self._xform_gen)
        xform_wrap.addLayout(head)

        self._xform_scroll = QScrollArea()
        self._xform_scroll.setObjectName("xformScroll")
        self._xform_scroll.setWidgetResizable(True)
        self._xform_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._xform_empty = QLabel()
        self._xform_empty.setObjectName("xformEmpty")
        self._xform_empty.setWordWrap(True)
        self._xform_empty.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._xform_scroll.setWidget(self._xform_empty)
        xform_wrap.addWidget(self._xform_scroll, 1)
        self._stack.addWidget(xform_page)

        root.addWidget(self._stack, 1)

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
        self._foot_prompt = QLabel()
        self._foot_prompt.setProperty("dim", True)
        foot.addWidget(self._foot_prompt)
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
        self._refresh_xform_icon()

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
        self._tabs.setCurrentIndex(0)  # always land on the transcript
        self._on_tab_changed(0)

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

    # ── transform tabs ─────────────────────────────────────────────────────

    def _preset_for_tab(self, index: int):
        """The preset behind tab ``index`` (1..4), or ``None`` for transcript/ask."""
        # _TABS[0] is the transcript; [1..4] are TAB_PRESETS; [5] is ask (chat).
        if 1 <= index <= len(preset_lib.TAB_PRESETS):
            return preset_lib.TAB_PRESETS[index - 1]
        return None

    def _on_tab_changed(self, index: int) -> None:
        # The "Ask" tab routes to the chat view rather than rendering inline.
        if index == len(_TABS) - 1 and self._current is not None:
            self.askRequested.emit(self._current.id)
            # Snap back to the transcript so re-selecting Ask fires again.
            self._tabs.blockSignals(True)
            self._tabs.setCurrentIndex(0)
            self._tabs.blockSignals(False)
            self._stack.setCurrentIndex(0)
            return

        preset = self._preset_for_tab(index)
        if preset is None:  # transcript tab
            self._stack.setCurrentIndex(0)
            return

        self._stack.setCurrentIndex(1)
        if self._current is None:
            self._render_transform(preset, None)
            return
        cached = self._transform.cached(self._current.id, preset.id)
        self._render_transform(preset, cached.text if cached else None, cached=bool(cached))

    def _set_xform_content(self, widget: QWidget) -> None:
        """Swap the scroll area's content widget (deletes the previous one)."""
        old = self._xform_scroll.takeWidget()
        if old is not None and old is not self._xform_empty:
            old.deleteLater()
        widget.setParent(None)
        self._xform_scroll.setWidget(widget)

    def _render_transform(self, preset, text: str | None, *, cached: bool = False) -> None:
        self._active_preset = preset
        self._xform_head.setText(t(preset.label_key))
        if text is None:
            self._xform_empty.setText(t("detail.transform.empty"))
            self._set_xform_content(self._xform_empty)
            self._xform_cache.setText("")
            self._xform_gen.setText(t("detail.transform.generate"))
        else:
            self._set_xform_content(render_result(preset.id, text))
            self._xform_cache.setText(
                "↺ " + t("detail.transform.cached") if cached else ""
            )
            self._xform_gen.setText(t("detail.transform.regenerate"))
        self._xform_gen.setEnabled(self._current is not None and not self._busy)
        self._refresh_xform_icon()

    def _on_generate(self) -> None:
        preset = getattr(self, "_active_preset", None)
        if preset is None or self._current is None or self._busy:
            return
        transcript_id = self._current.id
        text = self._current.text
        settings = self._settings
        force = bool(self._transform.cached(transcript_id, preset.id))
        self._busy = True
        self._xform_gen.setEnabled(False)
        self._xform_cache.setText(t("detail.transform.generating"))

        run_transform(
            lambda: self._transform.apply(
                transcript_id, text, preset, settings, force=force
            ).text,
            lambda result: self._on_generate_done(transcript_id, preset, result),
            lambda err: self._on_generate_failed(err),
        )

    def _on_generate_done(self, transcript_id: str, preset, result: str) -> None:
        self._busy = False
        # Only paint if the user is still on this transcript + preset.
        if self._current is not None and self._current.id == transcript_id \
                and getattr(self, "_active_preset", None) is preset:
            self._render_transform(preset, result)

    def _on_generate_failed(self, err: str) -> None:
        self._busy = False
        self._xform_cache.setText(t("detail.transform.failed"))
        self._xform_gen.setEnabled(self._current is not None)

    def _refresh_xform_icon(self) -> None:
        if self._theme is None:
            return
        self._xform_icon.setPixmap(
            icons.svg_icon("sparkles", self._theme.color(Token.TEXT_MUTED), 15).pixmap(15, 15)
        )

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
        self._flash_copied()

    def _flash_copied(self) -> None:
        """Briefly swap the copy icon for a green check, then restore it.

        Confirmation lives on the button itself rather than a status toast, so
        no footer message is raised for a copy.
        """
        if self._theme is not None:
            self._copy_btn.setIcon(
                icons.svg_icon("check", self._theme.color(Token.STATUS_SUCCESS), 16)
            )
        QTimer.singleShot(1500, self._refresh_icons)

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
        self._foot_prompt.setText("✦ " + t("detail.foot.prompt"))
        self._refresh_word_count()
        # Re-render the active transform tab so its button/placeholder follow.
        self._on_tab_changed(self._tabs.currentIndex())
        if self._current is None:
            self._meta.setText(t("detail.none"))
