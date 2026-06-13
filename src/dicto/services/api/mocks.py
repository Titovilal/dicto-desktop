"""In-memory mock backend for the library and dictionary endpoints.

The library and dictionary live in the *user's* backend (see REBUILD_PLAN.md);
this repo ships typed mocks so the UI can be built and tested without a server.
Ids and the clock are injectable so tests stay deterministic.
"""

from __future__ import annotations

import copy
import itertools
import threading
from collections.abc import Callable, Iterator

from dicto.core.models import DictTerm, DictTermKind, Transcript, TransformResult


def _counter(prefix: str) -> Callable[[], str]:
    seq: Iterator[int] = itertools.count(1)

    def next_id() -> str:
        return f"{prefix}_{next(seq):06d}"

    return next_id


class MockStore:
    """Deterministic in-memory stand-in for the user's backend.

    Thread-safe: the orchestrator's worker thread saves while the UI reads.
    """

    def __init__(self, *, clock: Callable[[], str] | None = None) -> None:
        self._transcripts: dict[str, Transcript] = {}
        self._terms: dict[str, DictTerm] = {}
        # Transform cache keyed by (transcript_id, preset).
        self._transforms: dict[tuple[str, str], TransformResult] = {}
        self._next_trx = _counter("trx")
        self._next_trm = _counter("trm")
        self._clock = clock or (lambda: "1970-01-01T00:00:00Z")
        self._lock = threading.RLock()

    def now(self) -> str:
        """The store's current timestamp (same clock used for created_at)."""
        return self._clock()

    # ── library ──────────────────────────────────────────────────────────

    def list_transcripts(self) -> list[Transcript]:
        with self._lock:
            return [copy.deepcopy(t) for t in self._transcripts.values()]

    def get_transcript(self, transcript_id: str) -> Transcript | None:
        with self._lock:
            t = self._transcripts.get(transcript_id)
            return copy.deepcopy(t) if t is not None else None

    def create_transcript(
        self,
        text: str,
        *,
        duration_seconds: float = 0.0,
        language: str = "es",
        tags: list[str] | None = None,
        subject: str | None = None,
        title: str | None = None,
    ) -> Transcript:
        with self._lock:
            transcript = Transcript(
                id=self._next_trx(),
                text=text,
                created_at=self._clock(),
                duration_seconds=duration_seconds,
                language=language,
                tags=list(tags or []),
                subject=subject,
                title=title,
            )
            self._transcripts[transcript.id] = transcript
            return copy.deepcopy(transcript)

    def update_transcript(self, transcript_id: str, **changes: object) -> Transcript | None:
        """Patch the given fields of a stored transcript; returns the new value."""
        with self._lock:
            stored = self._transcripts.get(transcript_id)
            if stored is None:
                return None
            for key, value in changes.items():
                if value is not None and hasattr(stored, key):
                    setattr(stored, key, value)
            return copy.deepcopy(stored)

    def delete_transcript(self, transcript_id: str) -> bool:
        with self._lock:
            return self._transcripts.pop(transcript_id, None) is not None

    # ── transforms (cache) ─────────────────────────────────────────────────

    def get_transform(self, transcript_id: str, preset: str) -> TransformResult | None:
        with self._lock:
            cached = self._transforms.get((transcript_id, preset))
            return copy.deepcopy(cached) if cached is not None else None

    def list_transforms(self, transcript_id: str) -> list[TransformResult]:
        with self._lock:
            return [
                copy.deepcopy(r)
                for (tid, _), r in self._transforms.items()
                if tid == transcript_id
            ]

    def save_transform(self, transcript_id: str, preset: str, text: str) -> TransformResult:
        with self._lock:
            result = TransformResult(
                transcript_id=transcript_id,
                preset=preset,
                text=text,
                created_at=self._clock(),
            )
            self._transforms[(transcript_id, preset)] = result
            return copy.deepcopy(result)

    # ── dictionary ───────────────────────────────────────────────────────

    def list_terms(self) -> list[DictTerm]:
        with self._lock:
            return [copy.deepcopy(t) for t in self._terms.values()]

    def create_term(
        self,
        text: str,
        *,
        kind: DictTermKind = DictTermKind.TERM,
        note: str | None = None,
    ) -> DictTerm:
        with self._lock:
            term = DictTerm(id=self._next_trm(), text=text, kind=kind, note=note)
            self._terms[term.id] = term
            return copy.deepcopy(term)

    def delete_term(self, term_id: str) -> bool:
        with self._lock:
            return self._terms.pop(term_id, None) is not None


# ── process-wide default store ────────────────────────────────────────────

_store: MockStore | None = None


def get_mock_store() -> MockStore:
    """Return the process-wide mock store, creating it on first use."""
    global _store
    if _store is None:
        _store = MockStore()
    return _store


def set_mock_store(store: MockStore | None) -> None:
    """Replace the process-wide store (the app injects one with a real clock)."""
    global _store
    _store = store


def reset_mock_store() -> None:
    """Drop the cached store (tests)."""
    global _store
    _store = None
