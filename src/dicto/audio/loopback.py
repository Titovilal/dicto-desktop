"""WASAPI loopback capture — record system audio as a selectable source.

For recording a class streamed on the computer (video call, lecture player) the
*system output* is the source, not the mic. On Windows this is exposed as a
loopback input. Two backends, in order of preference:

1. ``soundcard`` — captures the default speaker's monitor via WASAPI loopback
   (the robust path).
2. Stereo Mix — a legacy loopback *input* device via ``sounddevice`` (fallback,
   only if the user enabled it in Windows).

Ported from the old ``recorder.py`` loopback helpers and exposed as a small
``LoopbackCapture`` with the same start/stop shape as :class:`AudioCapture`, so
the pipeline can treat it as just another source feeding a ``SessionWriter``.

All third-party audio imports are lazy: importing this module never requires
``soundcard`` or ``sounddevice``.
"""

from __future__ import annotations

import logging
import sys
import threading
from collections.abc import Callable
from pathlib import Path

import numpy as np

from dicto.audio.devices import find_wasapi_loopback
from dicto.audio.session_writer import SessionWriter
from dicto.core.chunking import ChunkPolicy

logger = logging.getLogger(__name__)

BlockCallback = Callable[[np.ndarray], None]
_BLOCKSIZE = 1024


def find_stereo_mix() -> tuple[int, int] | None:
    """Find a Stereo Mix / loopback *input* device. Returns ``(index, channels)``."""
    if sys.platform != "win32":
        return None
    try:
        import sounddevice as sd

        keywords = ("stereo mix", "mezcla estéreo", "mezcla estereo", "loopback")
        for i, dev in enumerate(sd.query_devices()):
            name = dev.get("name", "").lower()
            ch = dev.get("max_input_channels", 0)
            if ch > 0 and any(kw in name for kw in keywords):
                logger.info("Stereo Mix device: [%d] %s (%dch)", i, dev["name"], ch)
                return i, ch
    except Exception:  # noqa: BLE001
        logger.warning("failed to search for Stereo Mix device", exc_info=True)
    return None


def is_available() -> bool:
    """True when some loopback backend looks usable on this machine."""
    try:
        import soundcard  # noqa: F401

        return True
    except Exception:  # noqa: BLE001
        pass
    return find_wasapi_loopback() is not None or find_stereo_mix() is not None


class _SoundcardLoopbackStream:
    """``soundcard`` loopback capture behind a start/stop interface.

    Pushes int16 blocks to ``callback`` from a background thread. Captures the
    default speaker with ``include_loopback=True``.
    """

    def __init__(self, callback: BlockCallback, blocksize: int, samplerate: int, channels: int):
        import soundcard as sc

        self._callback = callback
        self._blocksize = blocksize
        self._samplerate = samplerate
        self._channels = channels
        self._running = False
        self._thread: threading.Thread | None = None

        speaker = sc.default_speaker()
        self._mic = sc.get_microphone(id=str(speaker.name), include_loopback=True)

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, name="dicto-loopback", daemon=True)
        self._thread.start()

    def _run(self) -> None:
        try:
            with self._mic.recorder(
                samplerate=self._samplerate, channels=self._channels, blocksize=self._blocksize
            ) as rec:
                while self._running:
                    data = rec.record(numframes=self._blocksize)
                    if not self._running:
                        break
                    int16 = np.clip(data * 32767.0, -32768, 32767).astype(np.int16)
                    try:
                        self._callback(int16)
                    except Exception:  # noqa: BLE001
                        logger.debug("loopback callback error", exc_info=True)
        except Exception:  # noqa: BLE001
            logger.warning("soundcard loopback stream error", exc_info=True)
            self._running = False

    def stop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None


def open_loopback_stream(
    callback: BlockCallback, blocksize: int = _BLOCKSIZE
) -> tuple[object, int, int] | None:
    """Open a loopback stream feeding ``callback``. Returns ``(stream, rate, channels)``.

    The returned ``stream`` exposes ``start()``/``stop()``. ``None`` if no
    backend is available. Caller owns start/stop.
    """
    # Primary: soundcard (WASAPI loopback of the default speaker).
    try:
        import soundcard  # noqa: F401

        rate, channels = 48000, 2
        stream = _SoundcardLoopbackStream(callback, blocksize, rate, channels)
        logger.info("loopback via soundcard (%dch @ %dHz)", channels, rate)
        return stream, rate, channels
    except Exception:  # noqa: BLE001
        logger.debug("soundcard loopback unavailable", exc_info=True)

    if sys.platform != "win32":
        return None

    # Fallback: Stereo Mix via sounddevice.
    result = find_stereo_mix()
    if result is None:
        logger.warning("no loopback device available (no Stereo Mix found)")
        return None
    try:
        import sounddevice as sd

        device, channels = result
        rate = int(sd.query_devices(device).get("default_samplerate", 48000))

        def _sd_callback(indata, frames, time_info, status):  # noqa: ANN001
            callback(np.asarray(indata, dtype=np.int16))

        stream = sd.InputStream(
            samplerate=rate,
            channels=channels,
            dtype="int16",
            blocksize=blocksize,
            callback=_sd_callback,
            device=device,
        )
        return stream, rate, channels
    except Exception:  # noqa: BLE001
        logger.warning("failed to open Stereo Mix fallback", exc_info=True)
        return None


class LoopbackCapture:
    """Captures system audio to disk chunks, mirroring :class:`AudioCapture`.

    Downmixes to mono and resamples to ``sample_rate`` so its chunks match the
    mic's format. Used when the user selects "system audio" as the source.
    """

    def __init__(
        self,
        session_dir: str | Path,
        *,
        sample_rate: int,
        policy: ChunkPolicy | None = None,
    ) -> None:
        self.session_dir = Path(session_dir)
        self.sample_rate = sample_rate
        self._policy = policy
        self._writer: SessionWriter | None = None
        self._stream: object | None = None
        self._native_rate = sample_rate
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def chunk_paths(self) -> list[str]:
        return self._writer.chunk_paths if self._writer else []

    def start(self) -> bool:
        if self._running:
            return False
        result = open_loopback_stream(self._on_block)
        if result is None:
            return False
        self._stream, self._native_rate, _ = result
        self._writer = SessionWriter(
            self.session_dir, sample_rate=self.sample_rate, channels=1, policy=self._policy
        )
        self._running = True
        try:
            self._stream.start()  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001
            logger.warning("failed to start loopback stream", exc_info=True)
            self._running = False
            return False
        return True

    def stop(self) -> list[str]:
        self._running = False
        if self._stream is not None:
            try:
                self._stream.stop()  # type: ignore[attr-defined]
                close = getattr(self._stream, "close", None)
                if callable(close):
                    close()
            except Exception:  # noqa: BLE001
                logger.debug("error closing loopback stream", exc_info=True)
            self._stream = None
        return self._writer.close() if self._writer else []

    def _on_block(self, block: np.ndarray) -> None:
        if not self._running or self._writer is None:
            return
        try:
            mono = block.mean(axis=1).astype(np.int16) if block.ndim > 1 else block.reshape(-1)
            if self._native_rate != self.sample_rate:
                n_out = int(round(len(mono) * self.sample_rate / self._native_rate))
                if n_out <= 0:
                    return
                x_old = np.linspace(0, 1, len(mono), endpoint=False, dtype=np.float32)
                x_new = np.linspace(0, 1, n_out, endpoint=False, dtype=np.float32)
                mono = np.interp(x_new, x_old, mono.astype(np.float32)).astype(np.int16)
            self._writer.write(mono.tobytes())
        except Exception:  # noqa: BLE001
            logger.debug("error handling loopback block", exc_info=True)
