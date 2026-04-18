"""
Audio recording service using sounddevice.
"""

import logging
import sys
import sounddevice as sd
import soundfile as sf
import numpy as np
import threading
import tempfile
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def list_input_devices() -> list[dict]:
    """Return available input devices as [{id, name, channels, is_default}].

    On Windows, PortAudio exposes each physical device once per host API
    (MME, DirectSound, WASAPI, WDM-KS), which produces many duplicate
    entries. We filter to the system's default host API to show a single
    entry per device.
    """
    devices = []
    try:
        raw = sd.query_devices()
        try:
            default_in = sd.default.device[0]
        except Exception:
            default_in = None
        try:
            default_hostapi = sd.default.hostapi
        except Exception:
            default_hostapi = None
        if default_hostapi is None and default_in is not None:
            default_hostapi = raw[default_in].get("hostapi")
        for i, dev in enumerate(raw):
            if dev.get("max_input_channels", 0) <= 0:
                continue
            if default_hostapi is not None and dev.get("hostapi") != default_hostapi:
                continue
            devices.append(
                {
                    "id": i,
                    "name": dev["name"],
                    "channels": dev["max_input_channels"],
                    "is_default": i == default_in,
                }
            )
    except Exception as e:
        logger.warning(f"Failed to list audio devices: {e}")
    return devices


def _find_stereo_mix_device() -> tuple[int, int] | None:
    """Find a Stereo Mix (or similar loopback) input device.

    Returns (device_index, max_input_channels) or None.
    """
    if sys.platform != "win32":
        return None
    try:
        keywords = ("stereo mix", "mezcla estéreo", "mezcla estereo", "loopback")
        for i, dev in enumerate(sd.query_devices()):
            name = dev.get("name", "").lower()
            ch = dev.get("max_input_channels", 0)
            if ch > 0 and any(kw in name for kw in keywords):
                logger.info(f"Stereo Mix device found: [{i}] {dev['name']} ({ch}ch)")
                return i, ch
    except Exception as e:
        logger.warning(f"Failed to search for Stereo Mix device: {e}")
    return None


class AudioRecorder:
    """Records audio from the microphone, optionally mixing system audio (Windows)."""

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        max_duration: int = 120,
        input_device: int | None = None,
        include_system_audio: bool = False,
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.max_duration = max_duration
        self.input_device = input_device
        self.include_system_audio = include_system_audio
        self.chunk_size = 1024

        self.frames = []
        self.is_recording = False
        self.recording_thread = None
        self.temp_file_path = None
        self._audio_level_callback = None
        self._loopback_frames: list[np.ndarray] = []
        self._loopback_lock = threading.Lock()

    # ── Configuration updates ─────────────────────────────────

    def set_input_device(self, device_id: int | None):
        self.input_device = device_id

    def set_include_system_audio(self, enabled: bool):
        self.include_system_audio = enabled

    def set_audio_level_callback(self, callback):
        """Set a callback that receives audio level (0.0-1.0) for each chunk."""
        self._audio_level_callback = callback

    # ── Recording lifecycle ──────────────────────────────────

    def start_recording(self) -> bool:
        if self.is_recording:
            logger.warning("Recording already in progress")
            return False
        try:
            self.frames = []
            self._loopback_frames = []
            self.is_recording = True
            self.recording_thread = threading.Thread(
                target=self._record_audio, daemon=True
            )
            self.recording_thread.start()
            logger.info(
                f"Recording started (device={self.input_device}, "
                f"system_audio={self.include_system_audio}, max {self.max_duration}s)"
            )
            return True
        except Exception as e:
            logger.error(f"Error starting recording: {e}")
            self.is_recording = False
            return False

    def stop_recording(self) -> Optional[str]:
        if not self.is_recording:
            logger.warning("No recording in progress")
            return None

        self.is_recording = False
        if self.recording_thread:
            self.recording_thread.join(timeout=2.0)

        if len(self.frames) == 0:
            logger.warning("No audio data recorded")
            return None

        try:
            temp_file = tempfile.NamedTemporaryFile(
                suffix=".wav", delete=False, prefix="voice_recording_"
            )
            self.temp_file_path = temp_file.name
            temp_file.close()

            audio_data = np.concatenate(self.frames, axis=0)

            if self.include_system_audio and self._loopback_frames:
                mixed = self._mix_with_loopback(audio_data)
                sf.write(self.temp_file_path, mixed, self.sample_rate)
            else:
                sf.write(self.temp_file_path, audio_data, self.sample_rate)

            duration = len(audio_data) / self.sample_rate
            logger.info(f"Recording saved: {self.temp_file_path} ({duration:.1f}s)")

            self.frames = []
            self._loopback_frames = []
            return self.temp_file_path

        except Exception as e:
            logger.error(f"Error saving recording: {e}")
            self.frames = []
            self._loopback_frames = []
            return None

    def _mix_with_loopback(self, mic_int16: np.ndarray) -> np.ndarray:
        """Sum mic and loopback buffers as int16, clipping to avoid overflow."""
        try:
            with self._loopback_lock:
                loopback = (
                    np.concatenate(self._loopback_frames, axis=0)
                    if self._loopback_frames
                    else None
                )
            if loopback is None:
                return mic_int16

            if loopback.ndim > 1 and loopback.shape[1] > 1:
                loopback = loopback.mean(axis=1).astype(np.int16)
            else:
                loopback = loopback.reshape(-1).astype(np.int16)

            length = min(len(mic_int16.reshape(-1)), len(loopback))
            mic_flat = mic_int16.reshape(-1)[:length].astype(np.int32)
            loopback = loopback[:length].astype(np.int32)
            mixed = np.clip(mic_flat + loopback, -32768, 32767).astype(np.int16)
            return mixed.reshape(-1, 1) if self.channels == 1 else mixed
        except Exception as e:
            logger.warning(f"Failed to mix loopback audio: {e}")
            return mic_int16

    def _record_audio(self):
        """Records audio in a loop until stopped or max duration reached."""
        start_time = time.time()

        def mic_callback(indata, frames, time_info, status):
            if status:
                logger.warning(f"Audio stream status: {status}")
            if self.is_recording:
                self.frames.append(indata.copy())
                if self._audio_level_callback is not None:
                    rms = np.sqrt(np.mean(indata.astype(np.float32) ** 2))
                    level = min(1.0, rms / 400.0)
                    self._audio_level_callback(level)

        def loopback_callback(indata, frames, time_info, status):
            if status:
                logger.debug(f"Loopback stream status: {status}")
            if self.is_recording:
                with self._loopback_lock:
                    self._loopback_frames.append(indata.copy())

        loopback_stream = None
        try:
            mic_stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="int16",
                blocksize=self.chunk_size,
                callback=mic_callback,
                device=self.input_device,
            )

            if self.include_system_audio:
                loopback_stream = self._open_loopback_stream(loopback_callback)

            with mic_stream:
                if loopback_stream is not None:
                    loopback_stream.start()
                while self.is_recording:
                    elapsed = time.time() - start_time
                    if elapsed > self.max_duration:
                        logger.info(
                            f"Max recording duration ({self.max_duration}s) reached"
                        )
                        break
                    time.sleep(0.1)
        except Exception as e:
            logger.error(f"Error in recording thread: {e}")
        finally:
            if loopback_stream is not None:
                try:
                    loopback_stream.stop()
                    loopback_stream.close()
                except Exception as e:
                    logger.debug(f"Error closing loopback stream: {e}")
            self.is_recording = False

    def _open_loopback_stream(self, callback):
        """Open a Stereo Mix input stream on Windows for system audio capture."""
        if sys.platform != "win32":
            logger.warning("System audio capture is only supported on Windows")
            return None
        try:
            result = _find_stereo_mix_device()
            if result is None:
                logger.warning(
                    "No Stereo Mix device found. Enable it in Sound → Recording."
                )
                return None
            device, channels = result
            return sd.InputStream(
                samplerate=self.sample_rate,
                channels=channels,
                dtype="int16",
                blocksize=self.chunk_size,
                callback=callback,
                device=device,
            )
        except Exception as e:
            logger.warning(f"Failed to open loopback stream: {e}")
            return None

    def cleanup_temp_file(self):
        if self.temp_file_path and Path(self.temp_file_path).exists():
            try:
                Path(self.temp_file_path).unlink()
                logger.debug(f"Temporary file deleted: {self.temp_file_path}")
                self.temp_file_path = None
            except Exception as e:
                logger.error(f"Error deleting temporary file: {e}")

    def get_recording_duration(self) -> float:
        if not self.frames:
            return 0.0
        total_frames = sum(len(f) for f in self.frames)
        return total_frames / self.sample_rate

    def close(self):
        if self.is_recording:
            self.stop_recording()
        self.cleanup_temp_file()

    def __del__(self):
        self.close()


class AudioMonitor:
    """Live mic level monitor: captures input device samples and reports RMS levels via callback.

    Does not play audio back to the speakers — just reports a 0.0-1.0 level so the UI
    can show a waveform to confirm the selected mic is picking up sound.
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        input_device: int | None = None,
        include_system_audio: bool = False,  # kept for signature compatibility, ignored
    ):
        self.sample_rate = sample_rate
        self.input_device = input_device
        self._mic_stream: sd.InputStream | None = None
        self._running = False
        self._level_callback = None

    def set_level_callback(self, callback):
        """Set a callback that receives audio level (0.0-1.0) for each chunk."""
        self._level_callback = callback

    def start(self) -> bool:
        if self._running:
            return True
        try:
            self._mic_stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype="int16",
                blocksize=1024,
                callback=self._mic_callback,
                device=self.input_device,
            )
            self._mic_stream.start()
            self._running = True
            return True
        except Exception as e:
            logger.error(f"Error starting audio monitor: {e}")
            self.stop()
            return False

    def stop(self):
        self._running = False
        if self._mic_stream is not None:
            try:
                self._mic_stream.stop()
                self._mic_stream.close()
            except Exception:
                pass
        self._mic_stream = None

    @property
    def is_running(self) -> bool:
        return self._running

    def _mic_callback(self, indata, frames, time_info, status):
        if self._level_callback is None:
            return
        try:
            rms = np.sqrt(np.mean(indata.astype(np.float32) ** 2))
            level = min(1.0, rms / 400.0)
            self._level_callback(level)
        except Exception:
            pass
