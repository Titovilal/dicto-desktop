"""Live microphone monitor for the mic-test panel (effects: PortAudio, threads).

Opens an input stream purely to surface the live RMS level (0..1) via callback —
writes nothing to disk. Shares the level math with ``capture.py`` so the test
meter matches what's seen while recording.
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable

import numpy as np

from dicto.audio import devices

logger = logging.getLogger(__name__)

LevelCallback = Callable[[float], None]

_BLOCKSIZE = 1024
# Matches capture.py so the test meter and the recording meter agree.
_RMS_FULL_SCALE = 400.0


class AudioMonitor:
    """Streams a microphone's live level without persisting any audio."""

    def __init__(
        self,
        *,
        sample_rate: int = 16000,
        channels: int = 1,
        input_device: int | None = None,
        level_callback: LevelCallback | None = None,
    ) -> None:
        self.sample_rate = sample_rate
        self.channels = channels
        self.input_device = input_device
        self._level_callback = level_callback

        self._thread: threading.Thread | None = None
        self._running = False
        self._error: str | None = None

    @property
    def error(self) -> str | None:
        return self._error

    @property
    def is_running(self) -> bool:
        return self._running

    def set_level_callback(self, cb: LevelCallback | None) -> None:
        self._level_callback = cb

    def start(self) -> bool:
        """Open the monitoring stream. Returns False on failure (no device etc.)."""
        if self._running:
            return True
        self._error = None
        self._running = True
        self._thread = threading.Thread(target=self._run, name="dicto-monitor", daemon=True)
        self._thread.start()
        return True

    def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    # ── monitor thread ─────────────────────────────────────────────────

    def _run(self) -> None:
        try:
            import sounddevice as sd  # noqa: PLC0415 — lazy, headless-safe
        except Exception as exc:  # noqa: BLE001
            self._error = f"audio backend unavailable: {exc}"
            logger.error(self._error)
            self._running = False
            return
        try:
            if self.input_device is None and not devices.has_input_device():
                raise RuntimeError("no input audio device available")
            rate = devices.negotiate_samplerate(
                self.input_device, self.channels, self.sample_rate
            )
            stream = sd.InputStream(
                samplerate=rate,
                channels=self.channels,
                dtype="int16",
                blocksize=_BLOCKSIZE,
                callback=self._on_block,
                device=self.input_device,
            )
            with stream:
                while self._running:
                    time.sleep(0.05)
        except Exception as exc:  # noqa: BLE001
            self._error = str(exc)
            logger.error("monitor thread aborted: %s", exc, exc_info=True)
        finally:
            self._running = False
            # Drop the meter to silence when monitoring ends.
            self._emit(0.0)

    def _on_block(self, indata, frames, time_info, status) -> None:  # noqa: ANN001
        if status:
            logger.debug("monitor stream status: %s", status)
        if not self._running or self._level_callback is None:
            return
        try:
            block = np.asarray(indata, dtype=np.int16).astype(np.float32)
            rms = float(np.sqrt(np.mean(block**2))) if block.size else 0.0
            self._emit(min(1.0, rms / _RMS_FULL_SCALE))
        except Exception:  # noqa: BLE001 — a bad block must not kill the stream
            logger.debug("error handling monitor block", exc_info=True)

    def _emit(self, level: float) -> None:
        cb = self._level_callback
        if cb is None:
            return
        try:
            cb(level)
        except Exception:  # noqa: BLE001
            pass
