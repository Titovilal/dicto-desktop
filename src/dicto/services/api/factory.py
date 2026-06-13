"""Build the effectful transcribe callable the pure pipeline depends on.

The pipeline (``core/pipeline.py``) only knows a ``Callable[[str], str]`` that
turns a chunk path into text. This module is the seam where that callable is
built from settings + the httpx client, keeping the network out of core. It also
optionally trims silence with VAD before upload (best-effort).
"""

from __future__ import annotations

import wave
from collections.abc import Callable

from dicto.config.settings import Settings
from dicto.core import vad
from dicto.services.api import transcribe as transcribe_api
from dicto.services.api.client import ApiClient


def _read_wav_pcm(path: str) -> tuple[bytes, int]:
    with wave.open(path) as w:
        return w.readframes(w.getnframes()), w.getframerate()


def make_transcribe_chunk(
    client: ApiClient,
    settings: Settings,
    *,
    apply_vad: bool = False,
    prompt: str | None = None,
) -> Callable[[str], str]:
    """Return a ``chunk_path -> text`` callable for the pipeline.

    VAD trimming is opt-in and best-effort: a mono 16 kHz WAV is trimmed in
    place before upload; anything else (or any failure) uploads the chunk as-is.
    """
    stt = settings.transcription

    def transcribe_chunk(chunk_path: str) -> str:
        upload_path = chunk_path
        if apply_vad and settings.audio.channels == 1:
            try:
                pcm, rate = _read_wav_pcm(chunk_path)
                trimmed = vad.trim_silence(pcm, rate)
                if trimmed and len(trimmed) < len(pcm):
                    upload_path = chunk_path + ".vad.wav"
                    with wave.open(upload_path, "wb") as w:
                        w.setnchannels(1)
                        w.setsampwidth(2)
                        w.setframerate(rate)
                        w.writeframes(trimmed)
            except Exception:  # noqa: BLE001 — never block transcription on VAD
                upload_path = chunk_path
        return transcribe_api.transcribe_file(
            client,
            upload_path,
            model=stt.model,
            language=stt.language or None,
            prompt=prompt,
        )

    return transcribe_chunk
