"""Microphone capture that streams straight to disk (effects: PortAudio, threads).

``AudioCapture`` opens a ``sounddevice`` input stream on a background thread and
pushes every block into a :class:`~dicto.audio.session_writer.SessionWriter`,
which writes it to disk as bounded chunks. No frames are buffered in Python
beyond the block currently in flight — this is what lets a 60+ minute recording
run without growing RAM.

The device may not support the target sample rate (16 kHz); in that case the
stream opens at the device's native rate and each block is linearly resampled to
the target before being written, so on-disk chunks are always at one known rate.

A ``level_callback`` receives the live RMS level (0..1) per block for the
overlay meter / waveform; it must be cheap and non-blocking.
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from pathlib import Path

import numpy as np

from dicto.audio import devices
from dicto.audio.session_writer import SessionWriter
from dicto.core.chunking import ChunkPolicy

logger = logging.getLogger(__name__)

LevelCallback = Callable[[float], None]

_BLOCKSIZE = 1024
# RMS of int16 is divided by this to map a normal speaking level to ~1.0.
_RMS_FULL_SCALE = 400.0


class AudioCapture:
    """Captures the microphone to disk chunks on a background thread."""

    def __init__(
        self,
        session_dir: str | Path,
        *,
        sample_rate: int,
        channels: int,
        input_device: int | None = None,
        max_duration: int | None = None,
        policy: ChunkPolicy | None = None,
        level_callback: LevelCallback | None = None,
    ) -> None:
        self.session_dir = Path(session_dir)
        self.sample_rate = sample_rate
        self.channels = channels
        self.input_device = input_device
        self.max_duration = max_duration
        self._policy = policy
        self._level_callback = level_callback

        self._writer: SessionWriter | None = None
        self._thread: threading.Thread | None = None
        self._running = False
        self._capture_rate = sample_rate
        self._error: str | None = None
        # Set True while paused: the stream stays open but blocks are discarded,
        # so duration does not advance across a class break.
        self._paused = False

    # ── public API ─────────────────────────────────────────────────────

    @property
    def error(self) -> str | None:
        """Error from the most recent aborted capture, if any."""
        return self._error

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def recorded_seconds(self) -> float:
        return self._writer.recorded_seconds if self._writer else 0.0

    @property
    def chunk_paths(self) -> list[str]:
        return self._writer.chunk_paths if self._writer else []

    def set_paused(self, paused: bool) -> None:
        """Pause/resume: keeps the stream open but stops writing while paused."""
        self._paused = paused

    def start(self) -> bool:
        """Open the stream and begin writing chunks. Returns False on failure."""
        if self._running:
            logger.warning("capture already running")
            return False
        self._error = None
        self._paused = False
        self._writer = SessionWriter(
            self.session_dir,
            sample_rate=self.sample_rate,
            channels=self.channels,
            policy=self._policy,
        )
        self._running = True
        self._thread = threading.Thread(target=self._run, name="dicto-capture", daemon=True)
        self._thread.start()
        return True

    def stop(self) -> list[str]:
        """Stop capture and finalise chunks. Returns every chunk path written."""
        if not self._running and self._writer is None:
            return []
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=3.0)
            self._thread = None
        paths = self._writer.close() if self._writer else []
        return paths

    # ── capture thread ─────────────────────────────────────────────────

    def _run(self) -> None:
        try:
            import sounddevice as sd
        except Exception as exc:  # noqa: BLE001
            self._error = f"audio backend unavailable: {exc}"
            logger.error(self._error)
            self._running = False
            return

        try:
            if self.input_device is None and not devices.has_input_device():
                raise RuntimeError(
                    "no input audio device available (check microphone permissions)"
                )
            self._capture_rate = devices.negotiate_samplerate(
                self.input_device, self.channels, self.sample_rate
            )
            stream = sd.InputStream(
                samplerate=self._capture_rate,
                channels=self.channels,
                dtype="int16",
                blocksize=_BLOCKSIZE,
                callback=self._on_block,
                device=self.input_device,
            )
            start_time = time.time()
            with stream:
                while self._running:
                    if self.max_duration is not None and (
                        time.time() - start_time > self.max_duration
                    ):
                        logger.info("max recording duration (%ss) reached", self.max_duration)
                        break
                    time.sleep(0.05)
        except Exception as exc:  # noqa: BLE001
            self._error = str(exc)
            logger.error("capture thread aborted: %s", exc, exc_info=True)
        finally:
            self._running = False

    def _on_block(self, indata, frames, time_info, status) -> None:  # noqa: ANN001
        if status:
            logger.debug("audio stream status: %s", status)
        if not self._running or self._paused:
            return
        try:
            block = np.asarray(indata, dtype=np.int16)
            self._emit_level(block)
            block = self._resample(block)
            if self._writer is not None and block.size:
                self._writer.write(block.tobytes())
        except Exception:  # noqa: BLE001 — a bad block must not kill the stream
            logger.debug("error handling audio block", exc_info=True)

    def _emit_level(self, block: np.ndarray) -> None:
        if self._level_callback is None:
            return
        try:
            rms = float(np.sqrt(np.mean(block.astype(np.float32) ** 2)))
            self._level_callback(min(1.0, rms / _RMS_FULL_SCALE))
        except Exception:  # noqa: BLE001
            pass

    def _resample(self, block: np.ndarray) -> np.ndarray:
        """Linearly resample one block from the capture rate to the target rate."""
        if self._capture_rate == self.sample_rate:
            return block
        flat = block.reshape(-1, self.channels) if self.channels > 1 else block.reshape(-1)
        n_in = flat.shape[0]
        n_out = int(round(n_in * self.sample_rate / self._capture_rate))
        if n_out <= 0:
            return np.empty(0, dtype=np.int16)
        x_old = np.linspace(0, 1, n_in, endpoint=False, dtype=np.float32)
        x_new = np.linspace(0, 1, n_out, endpoint=False, dtype=np.float32)
        if self.channels > 1:
            out = np.empty((n_out, self.channels), dtype=np.int16)
            for ch in range(self.channels):
                out[:, ch] = np.interp(
                    x_new, x_old, flat[:, ch].astype(np.float32)
                ).astype(np.int16)
            return out
        return np.interp(x_new, x_old, flat.astype(np.float32)).astype(np.int16)
