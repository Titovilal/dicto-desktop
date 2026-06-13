"""Domain models — plain dataclasses shared across layers.

These mirror the API contract (see the endpoints in REBUILD_PLAN.md). They are
pure data: no Qt, no network, no persistence logic. Services in
``services/api/`` build and consume these; the UI renders them.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field


class JobStatus(enum.Enum):
    """Lifecycle of a transcription/transform job in the retry queue."""

    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


@dataclass
class Job:
    """A retryable unit of work over audio already persisted to disk.

    Audio is the sacred datum: a job references chunk paths, so a failed
    transcription can be retried from disk without re-recording.
    """

    job_id: str
    session_id: str
    chunk_paths: list[str]
    status: JobStatus = JobStatus.PENDING
    attempts: int = 0
    last_error: str | None = None

    def mark_running(self) -> None:
        self.status = JobStatus.RUNNING
        self.attempts += 1

    def mark_done(self) -> None:
        self.status = JobStatus.DONE
        self.last_error = None

    def mark_failed(self, error: str) -> None:
        self.status = JobStatus.FAILED
        self.last_error = error


@dataclass
class Transcript:
    """A stored transcription. Lives in the user's backend, not locally."""

    id: str
    text: str
    created_at: str  # ISO-8601 timestamp from the backend
    duration_seconds: float = 0.0
    language: str = "es"
    tags: list[str] = field(default_factory=list)
    subject: str | None = None
    title: str | None = None


@dataclass
class TransformResult:
    """The output of applying an AI preset to a transcript."""

    transcript_id: str
    preset: str
    text: str
    created_at: str


class DictTermKind(enum.Enum):
    TERM = "term"
    ACRONYM = "acronym"
    NAME = "name"


@dataclass
class DictTerm:
    """A user dictionary entry that biases the speech-to-text model."""

    id: str
    text: str
    kind: DictTermKind = DictTermKind.TERM
    note: str | None = None


@dataclass
class Plan:
    """The user's subscription plan and included usage."""

    name: str
    included_minutes: int
    price_label: str | None = None


@dataclass
class Account:
    """The user's account, plan and usage. Sourced from the backend."""

    email: str
    plan: Plan
    used_minutes: float = 0.0
    active: bool = True

    @property
    def remaining_minutes(self) -> float:
        return max(0.0, self.plan.included_minutes - self.used_minutes)
