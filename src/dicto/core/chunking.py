"""Chunk rotation policy — pure logic, no Qt, no I/O.

Audio is the sacred datum: a long recording is never held whole in RAM, it is
streamed to disk as a sequence of bounded *chunks*. This module owns the policy
that decides *when* the current chunk is full and a new one must start. The
actual writing lives in ``audio/session_writer.py``; this stays a pure function
of counters so it can be unit tested without touching disk or audio hardware.

A chunk rotates when **either** bound is hit:

* it has accumulated ``max_seconds`` of audio, or
* its on-disk size would exceed ``max_bytes``.

Keeping chunks bounded means a 60+ minute recording costs a bounded amount of
RAM (one chunk's worth of frames buffered before flush) and each chunk is small
enough to upload and retry independently — the heart of Phase 1 reliability.
"""

from __future__ import annotations

from dataclasses import dataclass

from dicto.config import defaults

# Defaults chosen so a chunk is a comfortable upload unit. At 16 kHz mono int16
# (32 kB/s) a 5-minute chunk is ~9.6 MB, well under the 25 MB transcribe limit.
DEFAULT_MAX_CHUNK_SECONDS: float = 300.0  # 5 minutes
DEFAULT_MAX_CHUNK_BYTES: int = 20 * 1024 * 1024  # 20 MB, headroom under API's 25 MB


def bytes_per_second(sample_rate: int, channels: int, bytes_per_sample: int = 2) -> int:
    """Raw PCM byte rate for the given format (int16 = 2 bytes/sample)."""
    return sample_rate * channels * bytes_per_sample


@dataclass
class ChunkPolicy:
    """Decides when the in-progress chunk is full and must rotate.

    The caller feeds it samples as they are captured (``add``) and asks
    ``should_rotate`` before each write; on rotation it calls ``reset``. All
    state is plain counters — no frames are held here.
    """

    sample_rate: int = defaults.DEFAULT_SAMPLE_RATE
    channels: int = defaults.DEFAULT_CHANNELS
    bytes_per_sample: int = 2
    max_seconds: float = DEFAULT_MAX_CHUNK_SECONDS
    max_bytes: int = DEFAULT_MAX_CHUNK_BYTES

    # Mutable counters for the chunk currently being filled.
    _samples: int = 0  # frames (per channel) accumulated in this chunk

    def __post_init__(self) -> None:
        if self.sample_rate <= 0:
            raise ValueError("sample_rate must be positive")
        if self.channels <= 0:
            raise ValueError("channels must be positive")
        if self.max_seconds <= 0:
            raise ValueError("max_seconds must be positive")
        if self.max_bytes <= 0:
            raise ValueError("max_bytes must be positive")

    @property
    def current_seconds(self) -> float:
        """Seconds of audio buffered in the current chunk."""
        return self._samples / self.sample_rate

    @property
    def current_bytes(self) -> int:
        """On-disk PCM size the current chunk would occupy."""
        return self._samples * self.channels * self.bytes_per_sample

    def add(self, frames: int) -> None:
        """Account for ``frames`` newly captured samples (per channel)."""
        if frames < 0:
            raise ValueError("frames must be non-negative")
        self._samples += frames

    def should_rotate(self) -> bool:
        """True when the current chunk has hit either the time or size bound."""
        if self._samples == 0:
            return False
        return self.current_seconds >= self.max_seconds or self.current_bytes >= self.max_bytes

    def reset(self) -> None:
        """Start a fresh chunk after a flush."""
        self._samples = 0
