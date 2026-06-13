"""Transform contract — preset → ``/transform`` request. PURE.

A *preset* is a declarative recipe: an id, a label key (i18n), and the system
instructions the AI applies to a transcript. Turning a preset + a transcript
(and, for chat, a question) into the request payload is pure — no Qt, no
network — so the UI and tests agree on exactly what gets sent.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Preset:
    """A declarative AI transform recipe.

    ``id`` is the stable cache key and tab identity. ``label_key`` is the i18n
    key for the tab/menu text. ``instructions`` is the system prompt sent to the
    transform endpoint. ``is_chat`` marks the conversational preset whose
    instructions are combined with a user question.
    """

    id: str
    label_key: str
    instructions: str
    is_chat: bool = False


@dataclass(frozen=True)
class TransformRequest:
    """The payload POSTed to ``/api/v1/transform``."""

    text: str
    instructions: str
    model: str


def build_request(
    preset: Preset,
    transcript_text: str,
    *,
    model: str,
    question: str | None = None,
) -> TransformRequest:
    """Build the request for applying ``preset`` to ``transcript_text``.

    For a chat preset the user's ``question`` is appended to the instructions so
    the model answers it grounded in the transcript; for the rest ``question``
    is ignored.
    """
    instructions = preset.instructions
    if preset.is_chat and question:
        instructions = f"{instructions}\n\nQuestion: {question.strip()}"
    return TransformRequest(
        text=transcript_text,
        instructions=instructions,
        model=model,
    )
