"""Unit tests for SessionWriter — chunks land on disk and rotate by policy."""

from __future__ import annotations

import wave

import pytest

from dicto.audio.session_writer import SessionWriter
from dicto.core.chunking import ChunkPolicy

SR = 16000


def _pcm(n_samples: int) -> bytes:
    return b"\x01\x00" * n_samples  # int16 value 1


def test_writes_single_chunk(tmp_path):
    w = SessionWriter(tmp_path, sample_rate=SR, channels=1)
    w.write(_pcm(SR))  # 1 second
    paths = w.close()
    assert len(paths) == 1
    with wave.open(paths[0]) as wav:
        assert wav.getframerate() == SR
        assert wav.getnchannels() == 1
        assert wav.getnframes() == SR


def test_rotates_into_multiple_chunks(tmp_path):
    policy = ChunkPolicy(sample_rate=SR, channels=1, max_seconds=1.0, max_bytes=10**9)
    w = SessionWriter(tmp_path, sample_rate=SR, channels=1, policy=policy)
    # Write 3.5 seconds in half-second blocks.
    for _ in range(7):
        w.write(_pcm(SR // 2))
    paths = w.close()
    # 3 full 1s chunks + a 0.5s remainder = 4 chunks.
    assert len(paths) == 4
    total = 0
    for p in paths:
        with wave.open(p) as wav:
            total += wav.getnframes()
    assert total == SR * 7 // 2


def test_chunk_paths_excludes_open_chunk(tmp_path):
    policy = ChunkPolicy(sample_rate=SR, channels=1, max_seconds=1.0)
    w = SessionWriter(tmp_path, sample_rate=SR, channels=1, policy=policy)
    w.write(_pcm(SR))  # fills and rotates one chunk
    w.write(_pcm(SR // 2))  # half of the next, still open
    assert len(w.chunk_paths) == 1
    w.close()
    assert len(w.chunk_paths) == 2


def test_recorded_seconds_tracks_total(tmp_path):
    w = SessionWriter(tmp_path, sample_rate=SR, channels=1)
    w.write(_pcm(SR * 2))
    assert w.recorded_seconds == pytest.approx(2.0)


def test_close_is_idempotent_and_drops_empty_chunk(tmp_path):
    w = SessionWriter(tmp_path, sample_rate=SR, channels=1)
    assert w.close() == []
    assert w.close() == []
    # No stray zero-length wav left behind.
    assert list(tmp_path.glob("*.wav")) == []


def test_write_after_close_raises(tmp_path):
    w = SessionWriter(tmp_path, sample_rate=SR, channels=1)
    w.close()
    with pytest.raises(RuntimeError):
        w.write(_pcm(10))
