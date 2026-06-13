"""Library read endpoint: GET ``/api/v1/library`` → the user's transcripts.

The library lives in the user's backend (dicto-web). This module is the stateless
GET that fetches it; parsing the response into :class:`Transcript` keeps the shape
the rest of the app already expects (mirrors ``transcribe.py`` / ``transform.py``).
Writes (create on dictation, edits) stay local in the :class:`MockStore` for now —
this only powers the *reading* of previously saved transcripts.
"""

from __future__ import annotations

import logging

from dicto.core.models import Transcript
from dicto.services.api import routes
from dicto.services.api.client import ApiClient

logger = logging.getLogger(__name__)


def _to_transcript(item: dict) -> Transcript:
    return Transcript(
        id=str(item.get("id", "")),
        text=item.get("text") or "",
        created_at=item.get("created_at") or "",
        duration_seconds=float(item.get("duration_seconds") or 0.0),
        language=item.get("language") or "es",
        tags=[str(t) for t in (item.get("tags") or [])],
        subject=item.get("subject"),
        title=item.get("title"),
    )


def fetch_library(client: ApiClient, *, limit: int = 200) -> list[Transcript]:
    """GET the user's transcripts. Raises a typed ``APIError`` on failure."""
    response = client.request("GET", routes.library(), params={"limit": limit})
    body = response.json()
    items = body.get("transcripts") if isinstance(body, dict) else None
    if not isinstance(items, list):
        logger.warning("library response missing 'transcripts' list")
        return []
    return [_to_transcript(it) for it in items if isinstance(it, dict)]
