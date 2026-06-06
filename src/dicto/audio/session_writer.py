"""Stream captured audio to disk as bounded WAV chunks.

This is the embodiment of "audio is the sacred datum": every block of samples
handed to :meth:`SessionWriter.write` is appended to the chunk file on disk
*immediately*, and the chunk is rotated (closed, a fresh one opened) whenever
:class:`~dicto.core.chunking.ChunkPolicy` says it is full. Nothing accumulates
unboundedly in RAM — a 60-minute recording costs only the OS write buffer plus
one block at a time.

Each chunk is a standalone, valid WAV file, so a failed transcription can be
retried from the chunk on disk, and a crash mid-recording still leaves every
completed chunk playable.

Only the stdlib :mod:`wave` module is used (mono/stereo int16 PCM), so this
layer has no third-party audio dependency and is fully unit-testable by feeding
it ``bytes``.
"""

from __future__ import annotations

import logging
import wave
from pathlib import Path

from dicto.core.chunking import ChunkPolicy

logger = logging.getLogger(__name__)

_BYTES_PER_SAMPLE = 2  # int16


class SessionWriter:
    """Writes int16 PCM to rotating WAV chunks under one session directory.

    Args:
        session_dir: directory that holds this session's chunk files.
        sample_rate: PCM sample rate (Hz).
        channels: number of interleaved channels.
        policy: rotation policy; one is created from sample_rate/channels if
            omitted.

    Usage::

        w = SessionWriter(session_dir, sample_rate=16000, channels=1)
        w.write(pcm_bytes)        # call repeatedly from the capture callback
        paths = w.close()         # finalise; returns every chunk path written
    """

    def __init__(
        self,
        session_dir: str | Path,
        *,
        sample_rate: int,
        channels: int,
        policy: ChunkPolicy | None = None,
    ) -> None:
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.sample_rate = sample_rate
        self.channels = channels
        self.policy = policy or ChunkPolicy(sample_rate=sample_rate, channels=channels)

        self._chunk_index = 0
        self._chunk_paths: list[str] = []
        self._wav: wave.Wave_write | None = None
        self._current_path: Path | None = None
        self._closed = False
        self._total_samples = 0  # frames per channel across all chunks

    # ── chunk lifecycle ────────────────────────────────────────────────

    def _chunk_path(self, index: int) -> Path:
        return self.session_dir / f"chunk_{index:04d}.wav"

    def _open_chunk(self) -> None:
        path = self._chunk_path(self._chunk_index)
        wav = wave.open(str(path), "wb")
        wav.setnchannels(self.channels)
        wav.setsampwidth(_BYTES_PER_SAMPLE)
        wav.setframerate(self.sample_rate)
        self._wav = wav
        self._current_path = path
        logger.debug("opened chunk %s", path)

    def _close_chunk(self) -> None:
        if self._wav is None:
            return
        try:
            self._wav.close()
        finally:
            self._wav = None
        if self._current_path is not None:
            self._chunk_paths.append(str(self._current_path))
            logger.debug("flushed chunk %s", self._current_path)
        self._current_path = None
        self._chunk_index += 1
        self.policy.reset()

    # ── writing ────────────────────────────────────────────────────────

    def write(self, pcm: bytes) -> None:
        """Append a block of int16 PCM, rotating the chunk if the policy says so.

        ``pcm`` is interleaved little-endian int16 for ``channels`` channels.
        """
        if self._closed:
            raise RuntimeError("cannot write to a closed SessionWriter")
        if not pcm:
            return
        if self._wav is None:
            self._open_chunk()

        assert self._wav is not None
        self._wav.writeframes(pcm)

        frames = len(pcm) // (_BYTES_PER_SAMPLE * self.channels)
        self.policy.add(frames)
        self._total_samples += frames

        if self.policy.should_rotate():
            self._close_chunk()

    @property
    def recorded_seconds(self) -> float:
        """Total seconds written across all chunks (live, while recording)."""
        return self._total_samples / self.sample_rate if self.sample_rate else 0.0

    @property
    def chunk_paths(self) -> list[str]:
        """Paths of chunks already flushed to disk (excludes the open one)."""
        return list(self._chunk_paths)

    def close(self) -> list[str]:
        """Finalise the open chunk and return every chunk path written.

        Idempotent. An empty trailing chunk (no frames) is removed so callers
        never see a zero-length WAV.
        """
        if self._closed:
            return list(self._chunk_paths)
        # Drop an empty open chunk rather than emit a 0-frame WAV.
        if self._wav is not None and self.policy.current_seconds == 0.0:
            path = self._current_path
            try:
                self._wav.close()
            finally:
                self._wav = None
            if path is not None and path.exists():
                try:
                    path.unlink()
                except OSError:
                    logger.debug("could not remove empty chunk %s", path, exc_info=True)
            self._current_path = None
        else:
            self._close_chunk()
        self._closed = True
        return list(self._chunk_paths)
