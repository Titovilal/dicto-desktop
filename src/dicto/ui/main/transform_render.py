"""Render a transform result into a structured widget, per the design.

Each preset has its own shape in the design hand-off (see ``theme.css``):
summary/rewrite are prose, key points are a numbered list, flashcards are a
two-column grid of cards. The model returns plain text, so we parse it
leniently (a malformed answer still shows as prose) and build the matching
widget. The widget is read-only; styling comes from object names in the theme.
"""

from __future__ import annotations

import re

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

# "Q: ... / A: ..." (the format ASKed of the flashcards preset), tolerant of
# leading bullets/numbers and an optional uppercase tag before the question.
_FLASHCARD = re.compile(
    r"(?:Q|P)\s*:\s*(?P<q>.+?)\s*(?:/|\n)\s*(?:A|R)\s*:\s*(?P<a>.+)",
    re.IGNORECASE | re.DOTALL,
)
_BULLET = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s+")


def render_result(preset_id: str, text: str) -> QWidget:
    """Build the widget for a transform ``text`` under ``preset_id``."""
    if preset_id == "flashcards":
        cards = _parse_flashcards(text)
        if cards:
            return _flashcards_widget(cards)
    if preset_id == "keypoints":
        points = _parse_points(text)
        if points:
            return _keypoints_widget(points)
    return _prose_widget(text)


# ── parsing ─────────────────────────────────────────────────────────────────


def _parse_flashcards(text: str) -> list[tuple[str, str]]:
    cards: list[tuple[str, str]] = []
    # Split on blank lines first; fall back to one card per non-empty line.
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
    if len(blocks) <= 1:
        blocks = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for block in blocks:
        m = _FLASHCARD.search(block)
        if m:
            cards.append((m.group("q").strip(), m.group("a").strip()))
    return cards


def _parse_points(text: str) -> list[str]:
    points: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if _BULLET.match(line):
            points.append(_BULLET.sub("", line).strip())
    return points


# ── widgets ─────────────────────────────────────────────────────────────────


def _prose_widget(text: str) -> QWidget:
    label = QLabel(text.strip())
    label.setObjectName("prose")
    label.setWordWrap(True)
    label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    label.setAlignment(Qt.AlignmentFlag.AlignTop)
    return label


def _keypoints_widget(points: list[str]) -> QWidget:
    holder = QWidget()
    layout = QVBoxLayout(holder)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(12)
    for i, point in enumerate(points, 1):
        row = QHBoxLayout()
        row.setSpacing(12)
        num = QLabel(str(i))
        num.setObjectName("kpNum")
        num.setFixedSize(24, 24)
        num.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row.addWidget(num, 0, Qt.AlignmentFlag.AlignTop)
        body = QLabel(point)
        body.setObjectName("kpText")
        body.setWordWrap(True)
        body.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        row.addWidget(body, 1)
        layout.addLayout(row)
    layout.addStretch(1)
    return holder


def _flashcards_widget(cards: list[tuple[str, str]]) -> QWidget:
    holder = QWidget()
    grid = QGridLayout(holder)
    grid.setContentsMargins(0, 0, 0, 0)
    grid.setHorizontalSpacing(12)
    grid.setVerticalSpacing(12)
    for idx, (question, answer) in enumerate(cards):
        grid.addWidget(_card(idx + 1, question, answer), idx // 2, idx % 2)
    grid.setColumnStretch(0, 1)
    grid.setColumnStretch(1, 1)
    # Push the cards up if there's spare height.
    grid.setRowStretch(grid.rowCount(), 1)
    return holder


def _card(n: int, question: str, answer: str) -> QFrame:
    card = QFrame()
    card.setObjectName("xformCard")
    box = QVBoxLayout(card)
    box.setContentsMargins(16, 14, 16, 14)
    box.setSpacing(9)
    tag = QLabel(f"TARJETA {n}")
    tag.setObjectName("cardTag")
    box.addWidget(tag)
    q = QLabel(question)
    q.setObjectName("cardQ")
    q.setWordWrap(True)
    box.addWidget(q)
    a = QLabel(answer)
    a.setObjectName("cardA")
    a.setWordWrap(True)
    a.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    box.addWidget(a)
    return card
