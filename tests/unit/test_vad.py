"""Unit tests for silence trimming.

webrtcvad is a hard signal detector, so we feed it real-ish PCM: silence is
zeros, "speech" is a loud sine wave. The tests assert behaviour (silence
shrinks, speech survives, errors never drop audio) rather than exact lengths.
"""

from __future__ import annotations

import math
import struct

import pytest

from dicto.core import vad

SR = 16000
FRAME_MS = 30


def _silence(seconds: float) -> bytes:
    n = int(SR * seconds)
    return struct.pack("<%dh" % n, *([0] * n))


def _tone(seconds: float, freq: int = 160, amp: int = 12000) -> bytes:
    """A voiced-speech-like signal: a fundamental plus harmonics.

    A pure sine is not reliably flagged as speech by webrtcvad (it keys on the
    spectral shape of voiced sound), so we stack the first few harmonics to
    look like a vowel.
    """
    n = int(SR * seconds)
    samples = []
    for i in range(n):
        t = i / SR
        v = (
            math.sin(2 * math.pi * freq * t)
            + 0.5 * math.sin(2 * math.pi * 2 * freq * t)
            + 0.3 * math.sin(2 * math.pi * 3 * freq * t)
        )
        samples.append(int(amp * v))
    return struct.pack("<%dh" % n, *samples)


requires_vad = pytest.mark.skipif(not vad.is_available(), reason="webrtcvad not installed")


def test_empty_input_returned_as_is():
    assert vad.trim_silence(b"", SR) == b""


def test_unsupported_samplerate_is_passthrough():
    pcm = _tone(0.1)
    assert vad.trim_silence(pcm, 12345) == pcm


def test_unsupported_frame_ms_is_passthrough():
    pcm = _tone(0.1)
    assert vad.trim_silence(pcm, SR, frame_ms=17) == pcm


@requires_vad
def test_pure_silence_kept_when_no_speech():
    # No speech at all → return original rather than emit nothing.
    pcm = _silence(1.0)
    out = vad.trim_silence(pcm, SR)
    assert out == pcm


@requires_vad
def test_trims_leading_and_trailing_silence():
    pcm = _silence(1.0) + _tone(1.0) + _silence(1.0)
    out = vad.trim_silence(pcm, SR, padding_ms=90)
    # Speech survives, but the 3s clip shrinks meaningfully.
    assert 0 < len(out) < len(pcm)
    assert len(out) >= len(_tone(0.5))  # the speech region is retained


@requires_vad
def test_all_speech_is_mostly_kept():
    # A clip that is entirely voiced should be largely retained (some boundary
    # frames may be dropped, but the bulk survives).
    pcm = _tone(1.0)
    out = vad.trim_silence(pcm, SR)
    assert len(out) >= int(len(pcm) * 0.5)


@requires_vad
def test_speech_with_gaps_shrinks_but_keeps_speech():
    pcm = _tone(0.6) + _silence(1.5) + _tone(0.6)
    out = vad.trim_silence(pcm, SR, padding_ms=90)
    assert 0 < len(out) < len(pcm)
