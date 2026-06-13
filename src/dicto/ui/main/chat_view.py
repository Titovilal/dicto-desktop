"""ChatView — "ask your notes": a Q&A panel grounded in one transcript.

The user picks a transcript, types a question, and the ``ask`` preset answers
using only that transcript as context (see ``transform/presets.ASK``). Answers
are conversational, so unlike the other transforms they are *not* cached — the
result depends on the question. The network call runs off the GUI thread via
``transform_worker``. The conversation renders as chat bubbles (user right,
AI left) per the design hand-off (``theme.css`` ``.dx-bubble``).
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from dicto.config.settings import Settings, get_settings
from dicto.core.models import Transcript
from dicto.i18n import on_language_changed, t
from dicto.services.api.library import LibraryService
from dicto.services.api.transform import TransformService
from dicto.transform import presets as preset_lib
from dicto.ui.main.transform_worker import run_transform


class ChatView(QWidget):
    """Ask questions about a single transcript and read the AI's answers."""

    statusMessage = Signal(str)

    def __init__(
        self,
        library: LibraryService,
        transform: TransformService | None = None,
        settings: Settings | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._library = library
        self._transform = transform or TransformService()
        self._settings = settings or get_settings()
        self._current: Transcript | None = None
        self._busy = False

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 18, 24, 16)
        root.setSpacing(12)

        self._heading = QLabel()
        self._heading.setObjectName("chatHead")
        root.addWidget(self._heading)

        # Conversation: a scroll area holding a column of bubbles.
        self._scroll = QScrollArea()
        self._scroll.setObjectName("chatScroll")
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._log = QWidget()
        self._log_layout = QVBoxLayout(self._log)
        self._log_layout.setContentsMargins(0, 0, 0, 0)
        self._log_layout.setSpacing(14)
        self._empty = QLabel()
        self._empty.setObjectName("chatEmpty")
        self._empty.setWordWrap(True)
        self._empty.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._log_layout.addWidget(self._empty)
        self._log_layout.addStretch(1)
        self._scroll.setWidget(self._log)
        root.addWidget(self._scroll, 1)

        ask_row = QHBoxLayout()
        ask_row.setSpacing(8)
        self._input = QLineEdit()
        self._input.returnPressed.connect(self._on_ask)
        ask_row.addWidget(self._input, 1)
        self._send = QPushButton()
        self._send.setProperty("accent", True)
        self._send.clicked.connect(self._on_ask)
        ask_row.addWidget(self._send)
        root.addLayout(ask_row)

        self.retranslate()
        self.show_empty()
        self._unsub_lang = on_language_changed(lambda _l: self.retranslate())

    # ── load / clear ─────────────────────────────────────────────────────

    def load(self, transcript_id: str) -> None:
        transcript = self._library.get(transcript_id)
        if transcript is None:
            self.show_empty()
            return
        # Reset the conversation when switching transcripts.
        if self._current is None or transcript.id != self._current.id:
            self._clear_bubbles()
        self._current = transcript
        self._empty.hide()
        self._set_enabled(True)
        self._input.setFocus()

    def show_empty(self) -> None:
        self._current = None
        self._clear_bubbles()
        self._empty.setText(t("chat.empty"))
        self._empty.show()
        self._input.clear()
        self._set_enabled(False)

    def _clear_bubbles(self) -> None:
        # Remove every bubble row, keeping the empty label and the trailing stretch.
        for i in reversed(range(self._log_layout.count())):
            item = self._log_layout.itemAt(i)
            w = item.widget() if item is not None else None
            if w is not None and w is not self._empty:
                w.deleteLater()
                self._log_layout.takeAt(i)

    def _set_enabled(self, enabled: bool) -> None:
        self._input.setEnabled(enabled)
        self._send.setEnabled(enabled and not self._busy)

    # ── ask ────────────────────────────────────────────────────────────────

    def _on_ask(self) -> None:
        question = self._input.text().strip()
        if not question or self._current is None or self._busy:
            return
        self._add_bubble(question, user=True)
        self._input.clear()
        transcript_id = self._current.id
        text = self._current.text
        settings = self._settings
        self._busy = True
        self._send.setEnabled(False)
        self.statusMessage.emit(t("chat.thinking"))

        run_transform(
            lambda: self._transform.apply(
                transcript_id, text, preset_lib.ASK, settings, question=question
            ).text,
            self._on_answer,
            self._on_failed,
        )

    def _on_answer(self, answer: str) -> None:
        self._busy = False
        self._send.setEnabled(self._current is not None)
        self._add_bubble(answer, user=False)

    def _on_failed(self, _err: str) -> None:
        self._busy = False
        self._send.setEnabled(self._current is not None)
        self._add_bubble(t("chat.failed"), user=False)

    def _add_bubble(self, message: str, *, user: bool) -> None:
        self._empty.hide()
        bubble = QLabel(message)
        bubble.setObjectName("bubbleUser" if user else "bubbleAi")
        bubble.setWordWrap(True)
        bubble.setMaximumWidth(560)
        bubble.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        row = QHBoxLayout()
        if user:
            row.addStretch(1)
            row.addWidget(bubble)
        else:
            row.addWidget(bubble)
            row.addStretch(1)
        wrap = QWidget()
        wrap.setLayout(row)
        row.setContentsMargins(0, 0, 0, 0)
        # Insert just before the trailing stretch (last item).
        self._log_layout.insertWidget(self._log_layout.count() - 1, wrap)
        self._scroll_to_bottom()

    def _scroll_to_bottom(self) -> None:
        bar = self._scroll.verticalScrollBar()
        bar.setValue(bar.maximum())

    # ── i18n ────────────────────────────────────────────────────────────────

    def retranslate(self) -> None:
        self._heading.setText(t("chat.title"))
        self._input.setPlaceholderText(t("chat.placeholder"))
        self._send.setText(t("chat.send"))
        if self._current is None:
            self._empty.setText(t("chat.empty"))
