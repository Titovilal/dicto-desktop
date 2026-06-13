"""LibraryView — the left zone: a searchable, sortable list of transcripts.

Styled per the design hand-off: a heading row with a count, a search box, a
row of tag chips plus a sort button, and two-line list items (title + meta:
tag dot · duration · date) painted by a delegate. The query semantics are pure
(``services/api/library.query_transcripts``); this widget only renders and
selects.
"""

from __future__ import annotations

from PySide6.QtCore import QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QStyle,
    QStyledItemDelegate,
    QVBoxLayout,
    QWidget,
)

from dicto.core.models import Transcript
from dicto.i18n import on_language_changed, t
from dicto.services.api.library import LibraryQuery, LibraryService, SortKey
from dicto.ui import icons
from dicto.ui.components.flow import FlowLayout
from dicto.ui.theme.manager import ThemeManager
from dicto.ui.theme.tokens import Token

# Sort cycle for the toolbar button: (key, i18n key).
_SORTS: tuple[tuple[SortKey, str], ...] = (
    ("created_desc", "library.sort.newest"),
    ("created_asc", "library.sort.oldest"),
    ("title", "library.sort.title"),
)

_ID_ROLE = Qt.ItemDataRole.UserRole
_META_ROLE = Qt.ItemDataRole.UserRole + 1  # (tag, duration, date) display strings

# A small stable palette for tag dots — index by hash so a tag keeps its colour.
_TAG_DOT_COLORS = ("#60a5fa", "#34d399", "#fbbf24", "#f472b6", "#a78bfa", "#fb923c")


def _preview(transcript: Transcript) -> str:
    """A one-line label for a transcript: its title, or a trimmed body."""
    title = (transcript.title or "").strip()
    if title:
        return title
    body = " ".join(transcript.text.split())
    return (body[:80] + "…") if len(body) > 80 else (body or "—")


def _format_duration(seconds: float) -> str:
    total = int(seconds)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def _format_date(created_at: str) -> str:
    # ISO-8601 from the backend; the date part is enough for the list.
    return created_at[:10] if created_at else ""


def tag_dot_color(tag: str) -> str:
    return _TAG_DOT_COLORS[hash(tag) % len(_TAG_DOT_COLORS)]


class _ItemDelegate(QStyledItemDelegate):
    """Two-line card: title, then `• tag · duration · date` in dim text."""

    _PAD_X = 12
    _PAD_Y = 10

    def __init__(self, theme: ThemeManager | None, parent=None) -> None:
        super().__init__(parent)
        self._theme = theme

    def _color(self, token: Token, fallback: str) -> QColor:
        return QColor(self._theme.color(token)) if self._theme else QColor(fallback)

    def sizeHint(self, option, index) -> QSize:  # noqa: N802 — Qt override
        return QSize(option.rect.width(), 58)

    def paint(self, painter: QPainter, option, index) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = option.rect.adjusted(self._PAD_X, self._PAD_Y, -self._PAD_X, -self._PAD_Y)
        selected = bool(option.state & QStyle.StateFlag.State_Selected)

        title_font = QFont(option.font)
        title_font.setPointSizeF(option.font.pointSizeF() + 0.5)
        title_font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(title_font)
        painter.setPen(self._color(Token.TEXT if selected else Token.TEXT_MUTED, "#a1a1aa"))
        fm = QFontMetrics(title_font)
        title = fm.elidedText(index.data() or "", Qt.TextElideMode.ElideRight, rect.width())
        painter.drawText(rect, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, title)

        meta = index.data(_META_ROLE) or ("", "", "")
        tag, duration, date = meta
        meta_font = QFont(option.font)
        meta_font.setPointSizeF(option.font.pointSizeF() - 1.0)
        painter.setFont(meta_font)
        dim = self._color(Token.TEXT_DIM, "#71717a")
        painter.setPen(dim)

        x = float(rect.left())
        y_line = rect.top() + fm.height() + 8
        mfm = QFontMetrics(meta_font)
        baseline = y_line + mfm.ascent()

        if tag:
            dot = QColor(tag_dot_color(tag))
            painter.setBrush(dot)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(x, y_line + (mfm.height() - 7) / 2, 7, 7))
            x += 12
            painter.setPen(self._color(Token.TEXT_MUTED, "#a1a1aa"))
            painter.drawText(int(x), baseline, tag)
            x += mfm.horizontalAdvance(tag) + 8
            painter.setPen(dim)

        for part in (p for p in (duration, date) if p):
            painter.drawText(int(x), baseline, f"·  {part}")
            x += mfm.horizontalAdvance(f"·  {part}") + 8

        painter.restore()


class LibraryView(QWidget):
    """List + search + sort + tag-chip filter over the user's transcripts."""

    transcriptSelected = Signal(str)  # transcript id
    emptied = Signal()  # nothing left / nothing selected

    def __init__(
        self,
        library: LibraryService,
        theme: ThemeManager | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._library = library
        self._theme = theme
        self._sort_index = 0

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 8, 10)
        root.setSpacing(12)

        # Heading row: title + count.
        head = QHBoxLayout()
        self._heading = QLabel()
        self._heading.setProperty("heading", True)
        head.addWidget(self._heading)
        head.addStretch(1)
        self._count = QLabel()
        self._count.setProperty("dim", True)
        head.addWidget(self._count)
        root.addLayout(head)

        self._search = QLineEdit()
        self._search.setClearButtonEnabled(True)
        self._search.textChanged.connect(self._reload)
        root.addWidget(self._search)

        # Tag chips (wrapping) + sort button.
        toolrow = QHBoxLayout()
        toolrow.setSpacing(6)
        chips_host = QWidget()
        self._chips_box = FlowLayout(chips_host)
        # Honour the flow layout's height-for-width so the row grows when
        # chips wrap (otherwise the area is never repainted properly).
        policy = chips_host.sizePolicy()
        policy.setHeightForWidth(True)
        chips_host.setSizePolicy(policy)
        self._chip_group = QButtonGroup(self)
        self._chip_group.setExclusive(True)
        toolrow.addWidget(chips_host, 1)
        self._sort_btn = QPushButton()
        self._sort_btn.setProperty("iconBtn", True)
        self._sort_btn.setFixedSize(32, 32)
        self._sort_btn.clicked.connect(self._cycle_sort)
        toolrow.addWidget(self._sort_btn, 0, Qt.AlignmentFlag.AlignTop)
        root.addLayout(toolrow)

        self._list = QListWidget()
        self._list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._list.setItemDelegate(_ItemDelegate(theme, self._list))
        self._list.currentItemChanged.connect(self._on_current_changed)
        root.addWidget(self._list, 1)

        self._empty = QLabel()
        self._empty.setProperty("dim", True)
        self._empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty.setWordWrap(True)
        root.addWidget(self._empty, 1)

        self.retranslate()
        self._refresh_icons()
        if theme is not None:
            theme.themeChanged.connect(lambda _e: self._refresh_icons())
        # No initial refresh here: the owner calls refresh() once its signal
        # connections exist, so the initial selection isn't emitted into a void.
        self._unsub_lang = on_language_changed(lambda _l: self.retranslate())

    # ── data ─────────────────────────────────────────────────────────────

    def _current_query(self) -> LibraryQuery:
        sort_key = _SORTS[self._sort_index][0]
        checked = self._chip_group.checkedButton()
        tag = checked.property("tagValue") if checked is not None else None
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
            tag = transcript.tags[0] if transcript.tags else ""
            duration = (
                _format_duration(transcript.duration_seconds)
                if transcript.duration_seconds
                else ""
            )
            row.setData(_META_ROLE, (tag, duration, _format_date(transcript.created_at)))
            self._list.addItem(row)
            if transcript.id == previous:
                self._list.setCurrentItem(row)
        self._list.blockSignals(False)

        total = self._list.count()
        self._count.setText(t("library.count").format(n=total))

        has_items = total > 0
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
        """Rebuild the tag chips, keeping the current choice if still present."""
        checked = self._chip_group.checkedButton()
        current = checked.property("tagValue") if checked is not None else None

        while self._chips_box.count():
            item = self._chips_box.takeAt(0)
            widget = item.widget()
            if widget is not None:
                self._chip_group.removeButton(widget)
                widget.setParent(None)  # vanish now; deleteLater needs the loop
                widget.deleteLater()

        def add_chip(label: str, value: str | None) -> QPushButton:
            chip = QPushButton(label)
            chip.setProperty("chip", True)
            chip.setProperty("tagValue", value)
            chip.setCheckable(True)
            chip.setCursor(Qt.CursorShape.PointingHandCursor)
            chip.toggled.connect(lambda on: on and self._reload())
            self._chip_group.addButton(chip)
            self._chips_box.addWidget(chip)
            return chip

        all_chip = add_chip(t("library.tag.all"), None)
        restored = False
        for tag in self._library.all_tags():
            chip = add_chip(tag, tag)
            if tag == current:
                chip.setChecked(True)
                restored = True
        if not restored:
            all_chip.setChecked(True)

    def refresh(self) -> None:
        """Reload tags then rows — call after a transcript is added/edited."""
        self._reload_tags()
        self._reload()

    # ── sort ─────────────────────────────────────────────────────────────

    def _cycle_sort(self) -> None:
        self._sort_index = (self._sort_index + 1) % len(_SORTS)
        self._sort_btn.setToolTip(t(_SORTS[self._sort_index][1]))
        self._reload()

    def _refresh_icons(self) -> None:
        if self._theme is not None:
            self._sort_btn.setIcon(icons.svg_icon("sort", self._theme.color(Token.TEXT_DIM), 17))

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
        self._sort_btn.setToolTip(t(_SORTS[self._sort_index][1]))
        self._count.setText(t("library.count").format(n=self._list.count()))
        # The "all" chip is index 0; tag chips keep their literal names.
        first = self._chips_box.itemAt(0)
        if first is not None and first.widget() is not None:
            first.widget().setText(t("library.tag.all"))
