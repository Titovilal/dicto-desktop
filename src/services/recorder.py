"""
Audio recording service using sounddevice.
"""

import logging
import sounddevice as sd
import soundfile as sf
import numpy as np
import threading
import tempfile
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class AudioRecorder:
    """Records audio from the microphone."""

    def __init__(
        self, sample_rate: int = 16000, channels: int = 1, max_duration: int = 120
    ):
        """
        Initialize audio recorder.

        Args:
            sample_rate: Sample rate in Hz (default: 16000 for speech)
            channels: Number of channels, 1 for mono, 2 for stereo
            max_duration: Maximum recording duration in seconds
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.max_duration = max_duration
        self.chunk_size = 1024  # Number of frames per buffer

        self.frames = []
        self.is_recording = False
        self.recording_thread = None
        self.temp_file_path = None
        self.stream = None

    def start_recording(self) -> bool:
        """
        Start recording audio.

        Returns:
            True if recording started successfully, False otherwise
        """
        if self.is_recording:
            logger.warning("Recording already in progress")
            return False

        try:
            self.frames = []
            self.is_recording = True

            # Start recording in a separate thread
            self.recording_thread = threading.Thread(
                target=self._record_audio, daemon=True
            )
            self.recording_thread.start()

            logger.info(f"Recording started (max {self.max_duration}s)")
            return True

        except Exception as e:
            logger.error(f"Error starting recording: {e}")
            self.is_recording = False
            return False

    def stop_recording(self) -> Optional[str]:
        """
        Stop recording and save to a temporary file.

        Returns:
            Path to the temporary audio file, or None if recording failed
        """
        if not self.is_recording:
            logger.warning("No recording in progress")
            return None

        # Signal recording to stop
        self.is_recording = False

        # Wait for recording thread to finish
        if self.recording_thread:
            self.recording_thread.join(timeout=2.0)

        # Save to temporary file
        if len(self.frames) == 0:
            logger.warning("No audio data recorded")
            return None

        try:
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(
                suffix=".wav", delete=False, prefix="voice_recording_"
            )
            self.temp_file_path = temp_file.name
            temp_file.close()

            # Concatenate all frames and write WAV file
            audio_data = np.concatenate(self.frames, axis=0)
            sf.write(self.temp_file_path, audio_data, self.sample_rate)

            duration = len(audio_data) / self.sample_rate
            logger.info(f"Recording saved: {self.temp_file_path} ({duration:.1f}s)")

            # Clear frames to free memory
            self.frames = []

            return self.temp_file_path

        except Exception as e:
            logger.error(f"Error saving recording: {e}")
            self.frames = []  # Clear frames to free memory even on error
            return None

    def _record_audio(self):
        """Internal method that records audio in a loop until stopped or max duration reached."""
        start_time = time.time()

        def callback(indata, frames, time_info, status):
            if status:
                logger.warning(f"Audio stream status: {status}")
            if self.is_recording:
                self.frames.append(indata.copy())

        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="int16",
                blocksize=self.chunk_size,
                callback=callback,
            ):
                while self.is_recording:
                    elapsed = time.time() - start_time
                    if elapsed > self.max_duration:
                        logger.info(f"Max recording duration ({self.max_duration}s) reached")
                        break
                    time.sleep(0.1)

        except Exception as e:
            logger.error(f"Error in recording thread: {e}")
        finally:
            self.is_recording = False

    def cleanup_temp_file(self):
        """Delete the temporary audio file."""
        if self.temp_file_path and Path(self.temp_file_path).exists():
            try:
                Path(self.temp_file_path).unlink()
                logger.debug(f"Temporary file deleted: {self.temp_file_path}")
                self.temp_file_path = None
            except Exception as e:
                logger.error(f"Error deleting temporary file: {e}")

    def get_recording_duration(self) -> float:
        """
        Get current recording duration in seconds.

        Returns:
            Duration in seconds
        """
        if not self.frames:
            return 0.0
        total_frames = sum(len(f) for f in self.frames)
        return total_frames / self.sample_rate

    def list_audio_devices(self):
        """List all available audio input devices."""
        logger.info("Available audio input devices:")
        devices = sd.query_devices()
        for i, dev in enumerate(devices):
            if dev["max_input_channels"] > 0:
                logger.info(f"  [{i}] {dev['name']} (channels: {dev['max_input_channels']})")

    def close(self):
        """Clean up resources."""
        if self.is_recording:
            self.stop_recording()
        self.cleanup_temp_file()

    def __del__(self):
        """Destructor to ensure cleanup."""
        self.close()
