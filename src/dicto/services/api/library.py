"""Library service — CRUD + search over stored transcripts (mocked).

Every dictated transcript is saved here so nothing is lost (Phase 4). The library
lives in the user's backend; this is the typed seam in front of it, backed by the
in-memory :class:`MockStore` for now. Search/sort/filter live in the pure
``query_transcripts`` so the UI and tests agree on what "search" means.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Literal

logger = logging.getLogger(__name__)

from dicto.core.models import Transcript
from dicto.services.api import errors
from dicto.services.api.client import ApiClient
from dicto.services.api.library_remote import fetch_library
from dicto.services.api.mocks import MockStore, get_mock_store

SortKey = Literal["created_desc", "created_asc", "title"]


@dataclass(frozen=True)
class LibraryQuery:
    """A library search: free-text, an optional tag/subject filter, and a sort."""

    text: str = ""
    tag: str | None = None
    subject: str | None = None
    sort: SortKey = "created_desc"


def _matches(transcript: Transcript, query: LibraryQuery) -> bool:
    if query.tag is not None and query.tag not in transcript.tags:
        return False
    if query.subject is not None and transcript.subject != query.subject:
        return False
    needle = query.text.strip().lower()
    if not needle:
        return True
    haystacks = [transcript.text, transcript.title or "", transcript.subject or "", *transcript.tags]
    return any(needle in h.lower() for h in haystacks)


def _sort_key(sort: SortKey):
    if sort == "created_asc":
        return (lambda t: t.created_at, False)
    if sort == "title":
        return (lambda t: (t.title or "").lower(), False)
    # Default: newest first.
    return (lambda t: t.created_at, True)


def query_transcripts(items: list[Transcript], query: LibraryQuery) -> list[Transcript]:
    """Filter + sort transcripts for a query. Pure — easy to unit-test."""
    filtered = [t for t in items if _matches(t, query)]
    key, reverse = _sort_key(query.sort)
    return sorted(filtered, key=key, reverse=reverse)


class LibraryService:
    """CRUD + search for transcripts.

    Reads come from the user's backend (``GET /api/v1/library``) merged with the
    in-process store, which holds transcripts dictated this session before they
    round-trip to the server. Writes stay in the store for now. ``client`` is
    optional so the service can be built before the API key is known; if no key
    is configured, reads fall back to the store alone (e.g. headless tests).
    """

    def __init__(
        self,
        store: MockStore | None = None,
        *,
        client: ApiClient | None = None,
        api_key: str | None = None,
    ) -> None:
        self._store = store or get_mock_store()
        self._client = client
        self._api_key = api_key
        self._remote: list[Transcript] | None = None  # cached fetch

    def _resolve_client(self) -> ApiClient | None:
        """Return the client, building one from the API key on first use.

        Returns ``None`` when no key is available — callers degrade to the store.
        """
        if self._client is None and self._api_key:
            self._client = ApiClient(self._api_key)
        return self._client

    def _fetch_remote(self, *, force: bool = False) -> list[Transcript]:
        """Fetch transcripts from the backend, cached so search is cheap."""
        if self._remote is not None and not force:
            return self._remote
        client = self._resolve_client()
        if client is None:
            self._remote = []
            return self._remote
        try:
            self._remote = fetch_library(client)
        except errors.APIError:
            logger.warning("could not load library from backend", exc_info=True)
            self._remote = []
        return self._remote

    def _all(self) -> list[Transcript]:
        """Remote transcripts merged with local ones (local id wins on clash)."""
        local = self._store.list_transcripts()
        local_ids = {t.id for t in local}
        remote = [t for t in self._fetch_remote() if t.id not in local_ids]
        return local + remote

    def list(self, query: LibraryQuery | None = None) -> List[Transcript]:
        return query_transcripts(self._all(), query or LibraryQuery())

    def get(self, transcript_id: str) -> Transcript | None:
        local = self._store.get_transcript(transcript_id)
        if local is not None:
            return local
        return next((t for t in self._fetch_remote() if t.id == transcript_id), None)

    def reload(self) -> None:
        """Drop the cached remote fetch so the next read hits the backend."""
        self._remote = None

    def create(
        self,
        text: str,
        *,
        duration_seconds: float = 0.0,
        language: str = "es",
        tags: List[str] | None = None,
        subject: str | None = None,
        title: str | None = None,
    ) -> Transcript:
        return self._store.create_transcript(
            text,
            duration_seconds=duration_seconds,
            language=language,
            tags=tags,
            subject=subject,
            title=title,
        )

    def update(
        self,
        transcript_id: str,
        *,
        text: str | None = None,
        tags: List[str] | None = None,
        subject: str | None = None,
        title: str | None = None,
    ) -> Transcript | None:
        return self._store.update_transcript(
            transcript_id,
            text=text,
            tags=tags,
            subject=subject,
            title=title,
        )

    def delete(self, transcript_id: str) -> bool:
        return self._store.delete_transcript(transcript_id)

    def all_tags(self) -> List[str]:
        """Distinct tags across the library, sorted (for filter chips)."""
        seen: set[str] = set()
        for t in self._all():
            seen.update(t.tags)
        return sorted(seen)
