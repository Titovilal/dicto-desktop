"""Turn the user's dictionary into a biasing prompt for transcription.

STT models spell unusual words better when given them up front as a hint. Pure:
``DictTerm`` list → the ``prompt`` string ``transcribe_file`` passes through.
"""

from __future__ import annotations

from dicto.core.models import DictTerm

# Caps keep a large dictionary a hint, not a payload that drowns the audio.
DEFAULT_MAX_TERMS = 100
DEFAULT_MAX_CHARS = 900


def build_bias_prompt(
    terms: list[DictTerm],
    *,
    max_terms: int = DEFAULT_MAX_TERMS,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> str | None:
    """Build a comma-separated biasing prompt from dictionary terms.

    Dedupe is case-insensitive and order-preserving (first spelling wins), capped
    by ``max_terms`` / ``max_chars``. Returns ``None`` when empty, so callers can
    pass the result straight to ``transcribe_file(prompt=...)``.
    """
    seen: set[str] = set()
    kept: list[str] = []
    for term in terms:
        text = term.text.strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        kept.append(text)
        if len(kept) >= max_terms:
            break

    if not kept:
        return None

    prompt = ", ".join(kept)
    if len(prompt) > max_chars:
        # Trim whole terms off the end rather than cutting one mid-word.
        while kept and len(", ".join(kept)) > max_chars:
            kept.pop()
        prompt = ", ".join(kept)
    return prompt or None
