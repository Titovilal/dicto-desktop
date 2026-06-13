"""Export a transcript to plain text or Markdown.

The detail view (Phase 4) lets the user export a stored transcript. The *what to
write* — building the file's text from a ``Transcript`` — is pure and lives here
so it's unit-testable without touching the disk. The thin *where to write it*
(opening a file) is a one-liner the UI calls with a user-chosen path.

Markdown gets a title heading and a small metadata block (date, language,
subject, tags); plain text is just the body, since that's what people paste into
other tools.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dicto.core.models import Transcript

ExportFormat = str  # "txt" | "md"


@dataclass(frozen=True)
class ExportPayload:
    """A ready-to-write export: the file body and a suggested filename."""

    content: str
    filename: str


def _safe_stem(transcript: Transcript) -> str:
    """A filesystem-safe filename stem from the title (or the id)."""
    raw = (transcript.title or "").strip() or f"dicto-{transcript.id}"
    # Keep it boring and portable: letters, digits, space, dash, underscore.
    cleaned = "".join(c if (c.isalnum() or c in " -_") else "-" for c in raw)
    cleaned = "-".join(cleaned.split())  # collapse whitespace to single dashes
    # Collapse runs of dashes and trim them from the ends ("Bio!" → "Bio").
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    cleaned = cleaned.strip("-")[:80].strip("-")
    return cleaned or f"dicto-{transcript.id}"


def to_txt(transcript: Transcript) -> str:
    """Plain-text export: the body, exactly as stored."""
    return transcript.text.rstrip() + "\n"


def to_markdown(transcript: Transcript) -> str:
    """Markdown export: title heading + metadata block + body."""
    title = (transcript.title or "").strip() or "Dicto transcript"
    lines: list[str] = [f"# {title}", ""]

    meta: list[str] = []
    if transcript.created_at:
        meta.append(f"- **Date:** {transcript.created_at}")
    if transcript.language:
        meta.append(f"- **Language:** {transcript.language}")
    if transcript.subject:
        meta.append(f"- **Subject:** {transcript.subject}")
    if transcript.tags:
        meta.append(f"- **Tags:** {', '.join(transcript.tags)}")
    if meta:
        lines.extend(meta)
        lines.append("")

    lines.append(transcript.text.rstrip())
    lines.append("")
    return "\n".join(lines)


def build_export(transcript: Transcript, fmt: ExportFormat = "txt") -> ExportPayload:
    """Build the export content and a suggested filename for ``fmt``.

    Raises:
        ValueError: if ``fmt`` is not ``"txt"`` or ``"md"``.
    """
    fmt = fmt.lower()
    if fmt == "txt":
        content = to_txt(transcript)
    elif fmt in ("md", "markdown"):
        content = to_markdown(transcript)
        fmt = "md"
    else:
        raise ValueError(f"unsupported export format: {fmt!r}")
    return ExportPayload(content=content, filename=f"{_safe_stem(transcript)}.{fmt}")


def write_export(transcript: Transcript, path: str | Path, fmt: ExportFormat | None = None) -> Path:
    """Write an export of ``transcript`` to ``path``.

    The format defaults to the file extension of ``path`` (``.md`` → markdown,
    anything else → txt) unless ``fmt`` is given explicitly. UTF-8, the only
    sane choice for transcripts that may carry accents/emoji.

    Returns the path written.
    """
    target = Path(path)
    if fmt is None:
        fmt = "md" if target.suffix.lower() in (".md", ".markdown") else "txt"
    payload = build_export(transcript, fmt)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(payload.content, encoding="utf-8")
    return target
