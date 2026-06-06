"""Voice-activity detection — trim leading/trailing/inner silence before upload.

A class recording is mostly speech with gaps; long silences waste upload
bandwidth, transcription minutes and model attention. This module runs
``webrtcvad`` over int16 PCM and returns a trimmed copy keeping only the speech
regions (plus a small padding so words are never clipped).

It is *pure* in the sense that it touches no Qt, no network and no disk — it
takes a bytes buffer of PCM and returns a bytes buffer of PCM. ``numpy`` is
allowed here (it is a data dependency, not an effect), matching the audio layer.

webrtcvad constraints we must respect:

* sample rate ∈ {8000, 16000, 32000, 48000}
* frame duration ∈ {10, 20, 30} ms
* mono int16 little-endian

Silence trimming is best-effort: if ``webrtcvad`` is unavailable or the input is
malformed, the original audio is returned unchanged. Audio is sacred — we never
drop it on a VAD error.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_VALID_SAMPLE_RATES = (8000, 16000, 32000, 48000)
_VALID_FRAME_MS = (10, 20, 30)
_BYTES_PER_SAMPLE = 2  # int16 mono


def is_available() -> bool:
    """True when the ``webrtcvad`` backend can be imported."""
    try:
        import webrtcvad  # noqa: F401
    except Exception:  # noqa: BLE001
        return False
    return True


def _iter_frames(pcm: bytes, frame_bytes: int):
    """Yield fixed-size frames; a trailing partial frame is dropped (VAD needs full frames)."""
    for start in range(0, len(pcm) - frame_bytes + 1, frame_bytes):
        yield start, pcm[start : start + frame_bytes]


def trim_silence(
    pcm: bytes,
    sample_rate: int = 16000,
    *,
    aggressiveness: int = 2,
    frame_ms: int = 30,
    padding_ms: int = 300,
) -> bytes:
    """Return ``pcm`` with non-speech regions removed.

    Args:
        pcm: mono int16 little-endian audio bytes.
        sample_rate: must be one of webrtcvad's accepted rates.
        aggressiveness: 0 (least) .. 3 (most aggressive filtering).
        frame_ms: analysis frame size; one of 10/20/30.
        padding_ms: speech kept this many ms before/after each detected region,
            so onsets and tails of words are never clipped.

    On any error or unsupported config the input is returned unchanged.
    """
    if not pcm:
        return pcm
    if sample_rate not in _VALID_SAMPLE_RATES:
        logger.debug("VAD skipped: unsupported sample rate %s", sample_rate)
        return pcm
    if frame_ms not in _VALID_FRAME_MS:
        logger.debug("VAD skipped: unsupported frame_ms %s", frame_ms)
        return pcm
    if not 0 <= aggressiveness <= 3:
        aggressiveness = max(0, min(3, aggressiveness))

    try:
        import webrtcvad
    except Exception:  # noqa: BLE001
        logger.debug("VAD skipped: webrtcvad unavailable")
        return pcm

    frame_bytes = int(sample_rate * (frame_ms / 1000.0)) * _BYTES_PER_SAMPLE
    if frame_bytes <= 0 or len(pcm) < frame_bytes:
        return pcm

    try:
        vad = webrtcvad.Vad(aggressiveness)
        flags: list[tuple[int, bool]] = []
        for start, frame in _iter_frames(pcm, frame_bytes):
            flags.append((start, vad.is_speech(frame, sample_rate)))
    except Exception:  # noqa: BLE001 — never drop audio on a VAD failure
        logger.warning("VAD failed; keeping original audio", exc_info=True)
        return pcm

    if not any(speech for _, speech in flags):
        # No speech detected at all — keep the original rather than emit silence.
        return pcm

    pad_frames = max(0, round(padding_ms / frame_ms))
    keep = [False] * len(flags)
    for i, (_, speech) in enumerate(flags):
        if speech:
            lo = max(0, i - pad_frames)
            hi = min(len(flags), i + pad_frames + 1)
            for j in range(lo, hi):
                keep[j] = True

    out = bytearray()
    for i, (start, _) in enumerate(flags):
        if keep[i]:
            out += pcm[start : start + frame_bytes]
    # Append any trailing partial frame only if the last full frame was kept,
    # so we don't lose the final fragment of speech.
    tail_start = len(flags) * frame_bytes
    if tail_start < len(pcm) and keep and keep[-1]:
        out += pcm[tail_start:]
    return bytes(out)
