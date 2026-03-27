"""Shared fixtures for Dicto tests."""
from __future__ import annotations


import pytest
import yaml

from src.config.settings import Settings


@pytest.fixture
def tmp_config(tmp_path):
    """Create a temporary config.yaml and return its path."""
    config_file = tmp_path / "config.yaml"
    return config_file


@pytest.fixture
def default_settings(tmp_config):
    """Settings instance loaded from a non-existent config (uses defaults)."""
    return Settings(config_path=str(tmp_config))


@pytest.fixture
def custom_config(tmp_config):
    """Write a custom config.yaml and return the path."""
    def _write(data: dict):
        with open(tmp_config, "w", encoding="utf-8") as f:
            yaml.dump(data, f)
        return str(tmp_config)
    return _write


@pytest.fixture
def sample_audio_file(tmp_path):
    """Create a small valid WAV file for testing."""
    import struct
    wav_path = tmp_path / "test.wav"
    # Minimal WAV: 16-bit mono, 16kHz, 0.1s of silence
    sample_rate = 16000
    num_samples = 1600
    data_size = num_samples * 2  # 16-bit = 2 bytes per sample
    with open(wav_path, "wb") as f:
        # RIFF header
        f.write(b"RIFF")
        f.write(struct.pack("<I", 36 + data_size))
        f.write(b"WAVE")
        # fmt chunk
        f.write(b"fmt ")
        f.write(struct.pack("<I", 16))       # chunk size
        f.write(struct.pack("<H", 1))        # PCM
        f.write(struct.pack("<H", 1))        # mono
        f.write(struct.pack("<I", sample_rate))
        f.write(struct.pack("<I", sample_rate * 2))  # byte rate
        f.write(struct.pack("<H", 2))        # block align
        f.write(struct.pack("<H", 16))       # bits per sample
        # data chunk
        f.write(b"data")
        f.write(struct.pack("<I", data_size))
        f.write(b"\x00" * data_size)
    return str(wav_path)
