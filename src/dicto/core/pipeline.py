"""Transcription pipeline — capture → persist → (vad) → transcribe as jobs.

This is the spine of Phase 1 reliability. It coordinates a recording session and
turns its on-disk chunks into text without ever holding the whole recording in
RAM and without losing audio when the network fails.

Design constraints (REBUILD_PLAN, principles 1 & 2):

* **Core stays pure.** This module imports no Qt, no httpx, no PortAudio. The
  effectful pieces are injected as small callables:

  - ``capturer``: an object with ``start() -> bool``, ``stop() -> list[str]``,
    ``chunk_paths`` and ``recorded_seconds`` (satisfied by
    :class:`dicto.audio.capture.AudioCapture`).
  - ``transcribe_chunk``: ``Callable[[str], str]`` mapping a chunk path to its
    text (wired in ``app.py`` to ``services.api.transcribe``).

  Both can be faked in tests, so the whole reliability story — retries, partial
  results, no audio loss — is unit-testable headless.

* **Audio is sacred.** Each chunk is a :class:`~dicto.core.models.Job` over a
  file already on disk. A failed transcription is retried *from that file*, not
  re-recorded. Chunks are never deleted by the pipeline until the caller says so
  (``cleanup``), so a crash leaves every chunk recoverable.

* **Progress is visible.** As each chunk transcribes, a
  :class:`~dicto.core.events.TranscriptionProgress` event carries the text so far
  and ``done/total`` — long recordings show partial results instead of a frozen
  spinner.

The pipeline runs transcription synchronously in :meth:`transcribe`; ``app.py``
calls it on a worker thread so the UI stays responsive.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Protocol

from dicto.core import events
from dicto.core.models import Job, JobStatus

logger = logging.getLogger(__name__)


class Capturer(Protocol):
    """The capture surface the pipeline needs (see ``audio/capture.py``)."""

    def start(self) -> bool: ...
    def stop(self) -> list[str]: ...
    def set_paused(self, paused: bool) -> None: ...
    @property
    def chunk_paths(self) -> list[str]: ...
    @property
    def recorded_seconds(self) -> float: ...
    @property
    def error(self) -> str | None: ...


TranscribeChunk = Callable[[str], str]


class Pipeline:
    """Owns one recording session end to end and its retry queue.

    Args:
        session_id: id of the recording (matches the on-disk folder).
        capturer: effectful capture device, injected.
        transcribe_chunk: maps a chunk path to text, injected.
        bus: domain event bus; progress and errors are published here.
        max_attempts: per-chunk retry budget before the job is marked failed.
        retry_backoff: seconds before the first retry, doubled each attempt.
        sleep: injectable sleep (tests pass a no-op).
    """

    def __init__(
        self,
        session_id: str,
        capturer: Capturer,
        transcribe_chunk: TranscribeChunk,
        bus: events.EventBus,
        *,
        max_attempts: int = 3,
        retry_backoff: float = 1.0,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.session_id = session_id
        self.capturer = capturer
        self.transcribe_chunk = transcribe_chunk
        self.bus = bus
        self.max_attempts = max_attempts
        self.retry_backoff = retry_backoff
        self._sleep = sleep
        self._jobs: list[Job] = []
        self._recording = False

    # ── capture lifecycle ──────────────────────────────────────────────

    def start(self) -> bool:
        """Begin capturing. Publishes ``RecordingStarted`` or ``ErrorOccurred``."""
        if not self.capturer.start():
            msg = self.capturer.error or "failed to start recording"
            self.bus.publish(events.ErrorOccurred(message=msg, code="capture"))
            return False
        self._recording = True
        self.bus.publish(events.RecordingStarted(session_id=self.session_id))
        return True

    def pause(self) -> None:
        self.capturer.set_paused(True)
        self.bus.publish(events.RecordingPaused(session_id=self.session_id))

    def resume(self) -> None:
        self.capturer.set_paused(False)
        self.bus.publish(events.RecordingResumed(session_id=self.session_id))

    def stop(self) -> list[str]:
        """Stop capture, finalise chunks, build one job per chunk.

        Returns the chunk paths. Publishes ``RecordingStopped``.
        """
        chunk_paths = self.capturer.stop()
        self._recording = False
        self._jobs = [
            Job(job_id=f"{self.session_id}:{i}", session_id=self.session_id, chunk_paths=[path])
            for i, path in enumerate(chunk_paths)
        ]
        self.bus.publish(
            events.RecordingStopped(
                session_id=self.session_id, chunk_paths=tuple(chunk_paths)
            )
        )
        return chunk_paths

    # ── transcription ──────────────────────────────────────────────────

    @property
    def jobs(self) -> list[Job]:
        return list(self._jobs)

    def transcribe(self) -> str:
        """Transcribe every chunk in order, retrying failures from disk.

        Emits a ``TranscriptionProgress`` after each chunk (with text so far)
        and a final ``TranscriptionDone``. A chunk that exhausts its retries is
        marked failed and skipped; its audio remains on disk for a later retry
        via :meth:`retry_failed`. Returns the stitched transcript.
        """
        parts: list[str] = []
        total = len(self._jobs)
        for done, job in enumerate(self._jobs, start=1):
            text = self._run_job(job)
            if text:
                parts.append(text)
            joined = " ".join(parts).strip()
            self.bus.publish(
                events.TranscriptionProgress(
                    session_id=self.session_id, text=joined, done=done, total=total
                )
            )

        final = " ".join(parts).strip()
        if any(j.status is JobStatus.FAILED for j in self._jobs):
            failed = [j.job_id for j in self._jobs if j.status is JobStatus.FAILED]
            logger.warning("%d chunk(s) failed: %s", len(failed), failed)
            self.bus.publish(
                events.ErrorOccurred(
                    message=f"{len(failed)} chunk(s) could not be transcribed",
                    code="partial",
                )
            )
        self.bus.publish(events.TranscriptionDone(session_id=self.session_id, text=final))
        return final

    def retry_failed(self) -> str:
        """Re-run only the failed jobs (from audio still on disk), then re-stitch."""
        for job in self._jobs:
            if job.status is JobStatus.FAILED:
                job.status = JobStatus.PENDING
                job.attempts = 0
        return self.transcribe()

    def _run_job(self, job: Job) -> str:
        """Transcribe one chunk with bounded retries. Empty string if it fails."""
        chunk = job.chunk_paths[0]
        for attempt in range(self.max_attempts):
            job.mark_running()
            try:
                text = self.transcribe_chunk(chunk)
                job.mark_done()
                return text
            except Exception as exc:  # noqa: BLE001 — classify via retryable flag
                retryable = getattr(exc, "retryable", True)
                job.mark_failed(str(exc))
                if not retryable or attempt >= self.max_attempts - 1:
                    logger.warning("chunk %s failed permanently: %s", chunk, exc)
                    break
                delay = self.retry_backoff * (2**attempt)
                logger.info("chunk %s failed (%s); retry %d in %.0fs", chunk, exc, attempt + 1, delay)
                self._sleep(delay)
        return ""

    @property
    def has_failures(self) -> bool:
        return any(j.status is JobStatus.FAILED for j in self._jobs)
