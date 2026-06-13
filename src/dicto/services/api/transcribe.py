"""Transcribe endpoint: POST one audio file → text.

Phase 1 reliability lives here together with the pipeline: a transcription is a
job over *one chunk already on disk*. This module turns a chunk path into text
(or a typed error) and stays stateless — retries, ordering and stitching are the
pipeline's concern. Local size guards fail fast before wasting an upload.
"""

from __future__ import annotations

import logging
from pathlib import Path

from dicto.services.api import errors, routes
from dicto.services.api.client import ApiClient

logger = logging.getLogger(__name__)

_MAX_UPLOAD_MB = 25.0
_MIN_UPLOAD_MB = 0.001

_MIME_BY_SUFFIX = {
    ".wav": "audio/wav",
    ".mp3": "audio/mpeg",
    ".webm": "audio/webm",
    ".m4a": "audio/m4a",
    ".ogg": "audio/ogg",
}


def transcribe_file(
    client: ApiClient,
    audio_path: str | Path,
    *,
    model: str = "v3-turbo",
    language: str | None = None,
    prompt: str | None = None,
) -> str:
    """Transcribe one audio file and return its text.

    Args:
        client: an authenticated :class:`ApiClient` (owns retries).
        audio_path: path to a chunk on disk.
        model: STT model id.
        language: optional language hint.
        prompt: optional biasing prompt (e.g. from the user dictionary).

    Raises a typed :class:`~dicto.services.api.errors.APIError` on failure.
    """
    path = Path(audio_path)
    if not path.exists():
        raise errors.APIError(f"audio file not found: {path}", code="missing_file")

    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > _MAX_UPLOAD_MB:
        raise errors.AudioTooLongError(f"audio too large: {size_mb:.1f}MB (max {_MAX_UPLOAD_MB})")
    if size_mb < _MIN_UPLOAD_MB:
        raise errors.AudioTooShortError("audio too small (likely no audio recorded)")

    data: dict[str, str] = {"source": "mic_app", "model": model}
    if language:
        data["language"] = language
    if prompt:
        data["prompt"] = prompt

    mime = _MIME_BY_SUFFIX.get(path.suffix.lower(), "audio/wav")
    with open(path, "rb") as fh:
        files = {"file": (path.name, fh, mime)}
        response = client.request("POST", routes.transcribe(), files=files, data=data)

    body = response.json()
    text = (body.get("text") or "").strip()
    if not text:
        raise errors.APIError("API returned empty transcription", code="empty")
    logger.info("transcribed %s (%.2fMB)", path.name, size_mb)
    return text
