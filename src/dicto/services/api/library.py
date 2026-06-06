"""Library service — CRUD + search over stored transcripts (mocked).

Every dictated transcript is saved here so nothing is lost (Phase 4). The library
lives in the user's backend; this is the typed seam in front of it, backed by the
in-memory :class:`MockStore` for now. Search/sort/filter live in the pure
``query_transcripts`` so the UI and tests agree on what "search" means.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal

from dicto.core.models import Transcript
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
    """CRUD + search for transcripts, backed by the mock store for now."""

    def __init__(self, store: MockStore | None = None) -> None:
        self._store = store or get_mock_store()

    def list(self, query: LibraryQuery | None = None) -> List[Transcript]:
        items = self._store.list_transcripts()
        return query_transcripts(items, query or LibraryQuery())

    def get(self, transcript_id: str) -> Transcript | None:
        return self._store.get_transcript(transcript_id)

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
        for t in self._store.list_transcripts():
            seen.update(t.tags)
        return sorted(seen)
