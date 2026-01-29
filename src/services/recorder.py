"""
Audio recording service using pyaudio.
"""
import pyaudio
import wave
import threading
import tempfile
import time
from pathlib import Path
from typing import Optional


class AudioRecorder:
    """Records audio from the microphone."""

    def __init__(self, sample_rate: int = 16000, channels: int = 1, max_duration: int = 120):
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

        self.audio = None
        self.stream = None
        self.frames = []
        self.is_recording = False
        self.recording_thread = None
        self.temp_file_path = None

        # Initialize PyAudio
        try:
            self.audio = pyaudio.PyAudio()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize audio system: {e}")

    def start_recording(self) -> bool:
        """
        Start recording audio.

        Returns:
            True if recording started successfully, False otherwise
        """
        if self.is_recording:
            print("Warning: Recording already in progress")
            return False

        try:
            # Open audio stream
            self.stream = self.audio.open(
                format=pyaudio.paInt16,  # 16-bit audio
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )

            self.frames = []
            self.is_recording = True

            # Start recording in a separate thread
            self.recording_thread = threading.Thread(target=self._record_audio, daemon=True)
            self.recording_thread.start()

            print(f"Recording started (max {self.max_duration}s)")
            return True

        except Exception as e:
            print(f"Error starting recording: {e}")
            self.is_recording = False
            if self.stream:
                self.stream.close()
                self.stream = None
            return False

    def stop_recording(self) -> Optional[str]:
        """
        Stop recording and save to a temporary file.

        Returns:
            Path to the temporary audio file, or None if recording failed
        """
        if not self.is_recording:
            print("Warning: No recording in progress")
            return None

        # Signal recording to stop
        self.is_recording = False

        # Wait for recording thread to finish
        if self.recording_thread:
            self.recording_thread.join(timeout=2.0)

        # Close stream
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

        # Save to temporary file
        if len(self.frames) == 0:
            print("Warning: No audio data recorded")
            return None

        try:
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(
                suffix=".wav",
                delete=False,
                prefix="voice_recording_"
            )
            self.temp_file_path = temp_file.name
            temp_file.close()

            # Write WAV file
            with wave.open(self.temp_file_path, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
                wf.setframerate(self.sample_rate)
                wf.writeframes(b''.join(self.frames))

            duration = len(self.frames) * self.chunk_size / self.sample_rate
            print(f"Recording saved: {self.temp_file_path} ({duration:.1f}s)")
            return self.temp_file_path

        except Exception as e:
            print(f"Error saving recording: {e}")
            return None

    def _record_audio(self):
        """Internal method that records audio in a loop until stopped or max duration reached."""
        start_time = time.time()

        try:
            while self.is_recording:
                # Check if max duration exceeded
                elapsed = time.time() - start_time
                if elapsed > self.max_duration:
                    print(f"Max recording duration ({self.max_duration}s) reached")
                    break

                # Read audio data
                try:
                    data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                    self.frames.append(data)
                except Exception as e:
                    print(f"Error reading audio stream: {e}")
                    break

        except Exception as e:
            print(f"Error in recording thread: {e}")
        finally:
            self.is_recording = False

    def cleanup_temp_file(self):
        """Delete the temporary audio file."""
        if self.temp_file_path and Path(self.temp_file_path).exists():
            try:
                Path(self.temp_file_path).unlink()
                print(f"Temporary file deleted: {self.temp_file_path}")
                self.temp_file_path = None
            except Exception as e:
                print(f"Error deleting temporary file: {e}")

    def get_recording_duration(self) -> float:
        """
        Get current recording duration in seconds.

        Returns:
            Duration in seconds
        """
        if not self.frames:
            return 0.0
        return len(self.frames) * self.chunk_size / self.sample_rate

    def list_audio_devices(self):
        """List all available audio input devices."""
        print("\nAvailable audio input devices:")
        for i in range(self.audio.get_device_count()):
            dev_info = self.audio.get_device_info_by_index(i)
            if dev_info['maxInputChannels'] > 0:
                print(f"  [{i}] {dev_info['name']} (channels: {dev_info['maxInputChannels']})")

    def close(self):
        """Clean up resources."""
        if self.is_recording:
            self.stop_recording()

        if self.stream:
            self.stream.close()
            self.stream = None

        if self.audio:
            self.audio.terminate()
            self.audio = None

        self.cleanup_temp_file()

    def __del__(self):
        """Destructor to ensure cleanup."""
        self.close()
