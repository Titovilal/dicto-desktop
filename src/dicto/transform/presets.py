"""Declarative AI presets for students.

These are the transforms surfaced as tabs in the detail view (summary, key
points, flashcards, rewrite) plus the conversational ``ask`` preset behind the
chat view. They are plain data — the instructions are the only behaviour — so
adding or tuning a preset never touches the service or the UI.

The ``id`` of each preset matches the detail-view tab key suffix
(``detail.tab.<id>``) so the UI maps a tab to its preset directly.
"""

from __future__ import annotations

from dicto.transform.schema import Preset

SUMMARY = Preset(
    id="summary",
    label_key="detail.tab.summary",
    instructions=(
        "You are a study assistant. Summarise the following transcript into a "
        "clear, concise summary that captures the main ideas. Use the same "
        "language as the transcript. Do not add information that is not present."
    ),
)

KEYPOINTS = Preset(
    id="keypoints",
    label_key="detail.tab.keypoints",
    instructions=(
        "You are a study assistant. Extract the key points from the following "
        "transcript as a short bulleted list. Each bullet is one idea, in the "
        "transcript's language. Keep it faithful to the source."
    ),
)

FLASHCARDS = Preset(
    id="flashcards",
    label_key="detail.tab.flashcards",
    instructions=(
        "You are a study assistant. Turn the following transcript into study "
        "flashcards. Output question/answer pairs, one per line as "
        "'Q: ... / A: ...', in the transcript's language. Cover the important "
        "concepts only."
    ),
)

REWRITE = Preset(
    id="rewrite",
    label_key="detail.tab.rewrite",
    instructions=(
        "You are an editor. Rewrite the following transcript as clean, "
        "well-structured prose: fix grammar, punctuation and flow without "
        "changing the meaning. Keep the transcript's language."
    ),
)

ASK = Preset(
    id="ask",
    label_key="detail.tab.ask",
    instructions=(
        "You are a study assistant. Answer the user's question using only the "
        "following notes as context. If the answer is not in the notes, say so. "
        "Reply in the question's language."
    ),
    is_chat=True,
)

# Ordered for the detail-view transform tabs (chat is handled separately).
TAB_PRESETS: tuple[Preset, ...] = (SUMMARY, KEYPOINTS, FLASHCARDS, REWRITE)

ALL_PRESETS: tuple[Preset, ...] = (*TAB_PRESETS, ASK)

_BY_ID = {p.id: p for p in ALL_PRESETS}


def get_preset(preset_id: str) -> Preset | None:
    """Return the preset with this id, or ``None`` if unknown."""
    return _BY_ID.get(preset_id)
