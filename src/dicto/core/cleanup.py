"""Dictation cleanup — pure text tidying for spoken input.

When dictating (as opposed to reading a written note aloud), people produce
filler words ("um", "eh", "o sea"), double spaces, and odd spacing around
punctuation. This module turns that raw transcript into something you'd be happy
to drop straight into a chat box or a document.

It is **pure**: no Qt, no network, no SO. ``clean_dictation`` takes text in,
gives text out, and is driven by per-language word lists so es/en (and friends)
behave the same way. Cleanup is enabled by default for dictation
(see ``defaults.DEFAULT_CLEANUP_ENABLED``) but the caller decides when to apply
it — a stored library transcript may want the raw text preserved.

Design notes:
- We never *delete* content we're unsure about. Filler removal only touches a
  curated, conservative list of standalone words/phrases, matched on word
  boundaries, so "humo" is never mistaken for the filler "um".
- Whitespace and punctuation fixes are language-agnostic and always safe.
"""

from __future__ import annotations

import re

# ── Filler words / phrases per language ────────────────────────────────────
#
# Conservative on purpose: only sounds that are almost never meaningful content
# when dictating. Multi-word phrases come first so they match before their
# single-word fragments. Matching is case-insensitive and on word boundaries.

_FILLERS: dict[str, tuple[str, ...]] = {
    "es": (
        "o sea",
        "eh",
        "em",
        "este…",
        "digamos",
        "como que",
    ),
    "en": (
        "you know",
        "i mean",
        "um",
        "uh",
        "uhm",
        "er",
        "erm",
        "hmm",
    ),
}

# Fillers shared by every language (vocalised hesitations).
_COMMON_FILLERS: tuple[str, ...] = ("ehh", "ehm", "mmm", "ah", "aha")


def _filler_pattern(lang: str) -> re.Pattern[str]:
    words = _FILLERS.get(lang, ()) + _COMMON_FILLERS
    # Longest first so "o sea" wins over a hypothetical "o".
    ordered = sorted(set(words), key=len, reverse=True)
    alternation = "|".join(re.escape(w) for w in ordered)
    # Surround with word boundaries; allow a trailing comma the speaker's pause
    # often becomes ("um, so" → "so"). \b doesn't fire next to "…", so we also
    # eat an optional trailing ellipsis/comma.
    return re.compile(rf"\b(?:{alternation})\b[\s,…]*", flags=re.IGNORECASE)


# Pre-compile for the languages we ship; others fall back to common fillers.
_PATTERNS: dict[str, re.Pattern[str]] = {
    lang: _filler_pattern(lang) for lang in (*_FILLERS.keys(), "_default")
}


def remove_fillers(text: str, lang: str = "es") -> str:
    """Drop standalone filler words/phrases for ``lang`` (conservative)."""
    pattern = _PATTERNS.get(lang, _PATTERNS["_default"])
    return pattern.sub("", text)


# ── Whitespace & punctuation (language-agnostic, always safe) ──────────────

# Space(s) sitting *before* punctuation that should hug the previous word.
_SPACE_BEFORE_PUNCT = re.compile(r"\s+([,.;:!?…])")
# Missing space *after* sentence punctuation when a letter follows directly.
_NO_SPACE_AFTER_PUNCT = re.compile(r"([,.;:!?])(?=[^\s\d])")
# Collapse runs of spaces/tabs (but not newlines).
_MULTISPACE = re.compile(r"[ \t]{2,}")
# Repeated punctuation like "?!?!" or ".." → keep the first.
_REPEAT_PUNCT = re.compile(r"([,.;:])\1+")


def fix_whitespace(text: str) -> str:
    """Normalise spacing around punctuation and collapse double spaces."""
    text = _SPACE_BEFORE_PUNCT.sub(r"\1", text)
    # Collapse repeats ("wait.." → "wait.") *before* spacing, so the dots are
    # still adjacent when this rule runs.
    text = _REPEAT_PUNCT.sub(r"\1", text)
    text = _NO_SPACE_AFTER_PUNCT.sub(r"\1 ", text)
    text = _MULTISPACE.sub(" ", text)
    # Trim trailing spaces on each line, and the whole thing.
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    return text.strip()


def capitalize_sentences(text: str) -> str:
    """Upper-case the first letter of the text and of each sentence."""
    if not text:
        return text

    def _upper(match: re.Match[str]) -> str:
        return match.group(0).upper()

    # First non-space character of the whole text.
    text = re.sub(r"^(\s*)([a-záéíóúñü])", lambda m: m.group(1) + m.group(2).upper(), text)
    # First letter after a sentence terminator + space.
    text = re.sub(r"([.!?]\s+)([a-záéíóúñü])", lambda m: m.group(1) + m.group(2).upper(), text)
    return text


def clean_dictation(text: str, lang: str = "es", *, capitalize: bool = True) -> str:
    """Tidy a raw dictation transcript.

    Order matters: remove fillers first (they leave stray spaces/commas), then
    normalise whitespace, then re-capitalise sentences whose leading filler we
    just removed.

    Args:
        text: Raw transcript text.
        lang: Language code selecting the filler list (``es``/``en``; others use
            the common hesitation list only).
        capitalize: When True, re-capitalise sentence starts. Off for content
            where the original casing matters.

    Returns:
        Cleaned text. Empty/whitespace-only input returns ``""``.
    """
    if not text or not text.strip():
        return ""
    text = remove_fillers(text, lang)
    text = fix_whitespace(text)
    if capitalize:
        text = capitalize_sentences(text)
    return text
