"""Integration test for the Phase 1 reliability story.

Exercises the full pipeline with a fake capturer (writing real WAV chunks to
disk via SessionWriter) and a fake transcriber that can be made to fail like a
flaky network. Asserts the three Phase 1 guarantees:

1. A long recording is split into many on-disk chunks (bounded RAM).
2. Killing the network mid-transcription does not lose audio — the chunk stays
   on disk and a retry transcribes it.
3. Progress events carry partial results as chunks complete.
"""

from __future__ import annotations

import wave


from dicto.audio.session_writer import SessionWriter
from dicto.core import events
from dicto.core.chunking import ChunkPolicy
from dicto.core.pipeline import Pipeline
from dicto.services.api import errors

SR = 16000


class FakeCapturer:
    """Writes ``total_seconds`` of dummy audio to disk in 1s blocks, rotating chunks."""

    def __init__(self, session_dir, total_seconds: float, chunk_seconds: float = 5.0):
        self._dir = session_dir
        self._total = total_seconds
        self._policy = ChunkPolicy(
            sample_rate=SR, channels=1, max_seconds=chunk_seconds, max_bytes=10**12
        )
        self._writer: SessionWriter | None = None
        self.error = None
        self.recorded_seconds = 0.0
        self._paused = False

    def start(self) -> bool:
        self._writer = SessionWriter(self._dir, sample_rate=SR, channels=1, policy=self._policy)
        block = b"\x01\x00" * SR  # 1 second of int16
        seconds = 0
        while seconds < self._total:
            self._writer.write(block)
            seconds += 1
        self.recorded_seconds = float(seconds)
        return True

    def set_paused(self, paused: bool) -> None:
        self._paused = paused

    def stop(self) -> list[str]:
        return self._writer.close() if self._writer else []

    @property
    def chunk_paths(self) -> list[str]:
        return self._writer.chunk_paths if self._writer else []


class FlakyTranscriber:
    """Returns the chunk's frame count as text; fails the chosen chunk N times first."""

    def __init__(self, fail_chunk: str | None = None, fail_times: int = 0, error=None):
        self.fail_chunk = fail_chunk
        self.fail_times = fail_times
        self.error = error or errors.NetworkError("connection reset")
        self.calls: list[str] = []

    def __call__(self, chunk_path: str) -> str:
        self.calls.append(chunk_path)
        if chunk_path.endswith(self.fail_chunk or "\0") and self.fail_times > 0:
            self.fail_times -= 1
            raise self.error
        with wave.open(chunk_path) as wav:
            return f"frames={wav.getnframes()}"


def _collect(bus: events.EventBus, event_type):
    seen = []
    bus.subscribe(event_type, seen.append)
    return seen


def test_long_recording_splits_into_chunks(tmp_path):
    cap = FakeCapturer(tmp_path, total_seconds=63 * 60, chunk_seconds=300)  # 63 min, 5-min chunks
    bus = events.EventBus()
    pipe = Pipeline("sess", cap, FlakyTranscriber(), bus, sleep=lambda _: None)
    pipe.start()
    paths = pipe.stop()
    # 63 min / 5 min ≈ 13 chunks; never one giant file.
    assert len(paths) >= 12
    for p in paths:
        with wave.open(p) as wav:
            assert wav.getnframes() <= 300 * SR


def test_network_failure_then_retry_recovers_audio(tmp_path):
    cap = FakeCapturer(tmp_path, total_seconds=15, chunk_seconds=5)  # 3 chunks
    bus = events.EventBus()
    cap.start_dir = tmp_path
    pipe = Pipeline("sess", cap, FlakyTranscriber(), bus, sleep=lambda _: None)
    pipe.start()
    paths = pipe.stop()
    assert len(paths) == 3

    # Make the middle chunk fail more times than the per-chunk retry budget.
    middle = paths[1]
    flaky = FlakyTranscriber(fail_chunk=middle.split("\\")[-1].split("/")[-1], fail_times=99)
    errors_seen = _collect(bus, events.ErrorOccurred)
    pipe.transcribe_chunk = flaky
    pipe.transcribe()

    assert pipe.has_failures
    assert any(e.code == "partial" for e in errors_seen)
    # Audio for the failed chunk is still on disk — nothing was deleted.
    assert all(__import__("pathlib").Path(p).exists() for p in paths)

    # Network recovers: retry only the failed chunk, from disk.
    pipe.transcribe_chunk = FlakyTranscriber()  # healthy
    done = _collect(bus, events.TranscriptionDone)
    final = pipe.retry_failed()
    assert not pipe.has_failures
    assert "frames=" in final
    assert done and done[-1].text == final


def test_transient_failure_retries_within_budget(tmp_path):
    cap = FakeCapturer(tmp_path, total_seconds=5, chunk_seconds=5)  # 1 chunk
    bus = events.EventBus()
    pipe = Pipeline("sess", cap, FlakyTranscriber(), bus, sleep=lambda _: None)
    pipe.start()
    paths = pipe.stop()
    chunk_name = paths[0].replace("\\", "/").split("/")[-1]
    # Fail twice, succeed on the third attempt (budget is 3).
    flaky = FlakyTranscriber(fail_chunk=chunk_name, fail_times=2)
    pipe.transcribe_chunk = flaky
    final = pipe.transcribe()
    assert not pipe.has_failures
    assert "frames=" in final
    assert len(flaky.calls) == 3


def test_progress_events_carry_partial_results(tmp_path):
    cap = FakeCapturer(tmp_path, total_seconds=15, chunk_seconds=5)  # 3 chunks
    bus = events.EventBus()
    progress = _collect(bus, events.TranscriptionProgress)
    pipe = Pipeline("sess", cap, FlakyTranscriber(), bus, sleep=lambda _: None)
    pipe.start()
    pipe.stop()
    pipe.transcribe()

    assert len(progress) == 3
    assert [p.done for p in progress] == [1, 2, 3]
    assert all(p.total == 3 for p in progress)
    # Text grows monotonically as chunks complete.
    assert len(progress[0].text) <= len(progress[1].text) <= len(progress[2].text)


def test_non_retryable_error_fails_fast(tmp_path):
    cap = FakeCapturer(tmp_path, total_seconds=5, chunk_seconds=5)
    bus = events.EventBus()
    pipe = Pipeline("sess", cap, FlakyTranscriber(), bus, sleep=lambda _: None)
    pipe.start()
    paths = pipe.stop()
    chunk_name = paths[0].replace("\\", "/").split("/")[-1]
    flaky = FlakyTranscriber(
        fail_chunk=chunk_name, fail_times=99, error=errors.AuthError("bad key")
    )
    pipe.transcribe_chunk = flaky
    pipe.transcribe()
    # Auth is non-retryable: exactly one attempt, then permanent failure.
    assert len(flaky.calls) == 1
    assert pipe.has_failures
