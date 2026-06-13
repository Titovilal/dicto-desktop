"""Dictionary modal — the user's own terms, shown INSIDE the main window.

Styled per the design hand-off: 720×648 card with a header, an add-term row
(input + kind + button) and a table of terms (term · note · kind · delete).
Backed by :class:`DictionaryService` (mock store for now); ``core/dictionary``
already turns these terms into the STT biasing prompt.
"""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from dicto.core.models import DictTermKind
from dicto.i18n import on_language_changed, t
from dicto.services.api.dictionary import DictionaryService
from dicto.ui import icons
from dicto.ui.components.rounded import apply_rounded_mask
from dicto.ui.theme.manager import ThemeManager
from dicto.ui.theme.tokens import Token

_KINDS = (DictTermKind.TERM, DictTermKind.ACRONYM, DictTermKind.NAME)


class DictionaryModal(QDialog):
    """Frameless modal dialog: add, list and delete dictionary terms."""

    def __init__(
        self,
        service: DictionaryService,
        theme: ThemeManager,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._service = service
        self._theme = theme
        self._drag_offset: QPoint | None = None

        self.setObjectName("dictionaryModal")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        # Translucent so the card's rounded corners read as real transparency
        # on all four sides; the fill/border/radius live on the inner card.
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedSize(720, 648)

        # Outer layout holds a single rounded card; the dialog itself is clear.
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        card = QFrame()
        card.setObjectName("modalCard")
        outer.addWidget(card)
        self._card = card

        root = QVBoxLayout(card)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── header: title + close ────────────────────────────────────────
        head = QFrame()
        head.setObjectName("modalHead")
        head.setFixedHeight(56)
        head_l = QHBoxLayout(head)
        head_l.setContentsMargins(22, 0, 14, 0)
        self._title = QLabel()
        self._title.setProperty("heading", True)
        head_l.addWidget(self._title)
        head_l.addStretch(1)
        close_btn = QPushButton("✕")
        close_btn.setProperty("iconBtn", True)
        close_btn.setFixedSize(32, 32)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.close)
        head_l.addWidget(close_btn)
        root.addWidget(head)

        # ── body ─────────────────────────────────────────────────────────
        body = QVBoxLayout()
        body.setContentsMargins(22, 16, 22, 18)
        body.setSpacing(12)

        self._desc = QLabel()
        self._desc.setProperty("dim", True)
        self._desc.setWordWrap(True)
        body.addWidget(self._desc)

        # Add-term row: input + kind + button.
        add_row = QHBoxLayout()
        add_row.setSpacing(8)
        self._input = QLineEdit()
        self._input.returnPressed.connect(self._on_add)
        add_row.addWidget(self._input, 1)
        self._kind_combo = QComboBox()
        for kind in _KINDS:
            self._kind_combo.addItem("", kind)
        add_row.addWidget(self._kind_combo)
        self._add_btn = QPushButton()
        self._add_btn.setProperty("accent", True)
        self._add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._add_btn.clicked.connect(self._on_add)
        add_row.addWidget(self._add_btn)
        body.addLayout(add_row)

        # Column header row.
        header = QHBoxLayout()
        header.setContentsMargins(10, 0, 10, 0)
        self._col_term = QLabel()
        self._col_term.setProperty("tableHead", True)
        self._col_note = QLabel()
        self._col_note.setProperty("tableHead", True)
        self._col_kind = QLabel()
        self._col_kind.setProperty("tableHead", True)
        header.addWidget(self._col_term, 4)
        header.addWidget(self._col_note, 4)
        header.addWidget(self._col_kind, 3)
        header.addSpacing(28)
        body.addLayout(header)

        rule = QFrame()
        rule.setProperty("fieldRule", True)
        rule.setFixedHeight(1)
        body.addWidget(rule)

        # Scrollable term list.
        self._rows_host = QWidget()
        self._rows_layout = QVBoxLayout(self._rows_host)
        self._rows_layout.setContentsMargins(0, 0, 0, 0)
        self._rows_layout.setSpacing(0)
        self._rows_layout.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(self._rows_host)
        body.addWidget(scroll, 1)

        self._empty = QLabel()
        self._empty.setProperty("dim", True)
        self._empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body.addWidget(self._empty)

        root.addLayout(body, 1)

        self.refresh()
        self.retranslate()
        self._unsub_lang = on_language_changed(lambda _l: self.retranslate())

    # ── data ─────────────────────────────────────────────────────────────

    def refresh(self) -> None:
        """Rebuild the term rows from the service."""
        while self._rows_layout.count() > 1:  # keep the trailing stretch
            item = self._rows_layout.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()

        terms = self._service.list()
        self._empty.setVisible(not terms)
        for term in terms:
            self._rows_layout.insertWidget(self._rows_layout.count() - 1, self._build_row(term))
        self._update_count()

    def _build_row(self, term) -> QFrame:
        row = QFrame()
        row.setProperty("dictRow", True)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        text = QLabel(term.text)
        text.setProperty("dictTerm", True)
        layout.addWidget(text, 4)

        note = QLabel(term.note or "—")
        note.setProperty("dim", True)
        layout.addWidget(note, 4)

        kind = QLabel(t(f"dict.kind.{term.kind.value}"))
        kind.setProperty("dim", True)
        layout.addWidget(kind, 3)

        delete = QPushButton()
        delete.setProperty("iconBtn", True)
        delete.setFixedSize(28, 28)
        delete.setCursor(Qt.CursorShape.PointingHandCursor)
        delete.setIcon(icons.svg_icon("trash", self._theme.color(Token.TEXT_DIM), 15))
        delete.setToolTip(t("dict.delete"))
        delete.clicked.connect(lambda _=False, tid=term.id: self._on_delete(tid))
        layout.addWidget(delete)
        return row

    def _on_add(self) -> None:
        text = self._input.text().strip()
        if not text:
            return
        self._service.create(text, kind=self._kind_combo.currentData())
        self._input.clear()
        self.refresh()

    def _on_delete(self, term_id: str) -> None:
        self._service.delete(term_id)
        self.refresh()

    # ── i18n ─────────────────────────────────────────────────────────────

    def retranslate(self) -> None:
        self.setWindowTitle(t("dict.title"))
        self._title.setText(t("dict.title"))
        self._input.setPlaceholderText(t("dict.add_placeholder"))
        self._add_btn.setText(t("dict.add"))
        for i, kind in enumerate(_KINDS):
            self._kind_combo.setItemText(i, t(f"dict.kind.{kind.value}"))
        self._col_term.setText(t("dict.col.term").upper())
        self._col_note.setText(t("dict.col.note").upper())
        self._col_kind.setText(t("dict.col.kind").upper())
        self._empty.setText(t("dict.empty"))
        self._update_count()
        # Kind labels in the rows are baked-in text; rebuild them.
        self.refresh()

    def _update_count(self) -> None:
        count = len(self._service.list())
        self._desc.setText(f"{t('dict.description')} {t('dict.count').format(n=count)}")

    # ── dragging (frameless) ─────────────────────────────────────────────

    def showEvent(self, event) -> None:  # noqa: N802, ANN001 — Qt override
        super().showEvent(event)
        # Clip the card so opaque panes follow the card's rounded corners.
        apply_rounded_mask(self._card, 16)

    def mousePressEvent(self, event) -> None:  # noqa: N802, ANN001 — Qt override
        if event.button() == Qt.MouseButton.LeftButton and event.position().y() < 56:
            self._drag_offset = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802, ANN001 — Qt override
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802, ANN001 — Qt override
        self._drag_offset = None
        super().mouseReleaseEvent(event)

    # ── lifecycle ────────────────────────────────────────────────────────

    def open_centered(self) -> None:
        """Show centred over the parent window, with fresh data."""
        self.refresh()
        parent = self.parentWidget()
        if parent is not None:
            geo = parent.frameGeometry()
            self.move(
                geo.x() + (geo.width() - self.width()) // 2,
                geo.y() + (geo.height() - self.height()) // 2,
            )
        self.show()
        self.raise_()
        self.activateWindow()
        self._input.setFocus()
