"""Unit tests for the chunk rotation policy (pure logic)."""

from __future__ import annotations

import pytest

from dicto.core.chunking import ChunkPolicy, bytes_per_second


def test_bytes_per_second():
    assert bytes_per_second(16000, 1) == 32000
    assert bytes_per_second(48000, 2) == 192000


def test_rotates_on_seconds():
    p = ChunkPolicy(sample_rate=16000, channels=1, max_seconds=1.0, max_bytes=10**9)
    p.add(8000)  # 0.5s
    assert not p.should_rotate()
    p.add(8000)  # 1.0s
    assert p.should_rotate()


def test_rotates_on_bytes():
    # 1000 bytes max => 500 int16 mono samples.
    p = ChunkPolicy(sample_rate=16000, channels=1, max_seconds=10**6, max_bytes=1000)
    p.add(499)
    assert not p.should_rotate()
    p.add(1)
    assert p.should_rotate()


def test_reset_starts_fresh_chunk():
    p = ChunkPolicy(sample_rate=16000, channels=1, max_seconds=1.0)
    p.add(16000)
    assert p.should_rotate()
    p.reset()
    assert p.current_seconds == 0.0
    assert not p.should_rotate()


def test_empty_chunk_never_rotates():
    p = ChunkPolicy(sample_rate=16000, channels=1, max_seconds=0.001)
    assert not p.should_rotate()


def test_current_metrics_track_channels():
    p = ChunkPolicy(sample_rate=16000, channels=2, max_seconds=10, max_bytes=10**9)
    p.add(16000)  # 1 second of stereo
    assert p.current_seconds == pytest.approx(1.0)
    assert p.current_bytes == 16000 * 2 * 2


def test_invalid_config_rejected():
    with pytest.raises(ValueError):
        ChunkPolicy(sample_rate=0)
    with pytest.raises(ValueError):
        ChunkPolicy(channels=0)
    with pytest.raises(ValueError):
        ChunkPolicy(max_seconds=0)
    with pytest.raises(ValueError):
        ChunkPolicy(max_bytes=0)


def test_negative_frames_rejected():
    p = ChunkPolicy()
    with pytest.raises(ValueError):
        p.add(-1)
