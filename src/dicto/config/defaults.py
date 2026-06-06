"""Default configuration values.

Kept separate from the Settings model so defaults are easy to see and override
in tests. Defaults follow the product brief: Spanish UI, cleanup on, fast model.
"""

from __future__ import annotations

from typing import Final

DEFAULT_LANGUAGE: Final = "es"
DEFAULT_THEME: Final = "system"  # one of: light | dark | system

# Speech-to-text
DEFAULT_STT_MODEL: Final = "v3-turbo"
DEFAULT_TRANSCRIBE_LANGUAGE: Final = "es"

# AI transform / edition
DEFAULT_TRANSFORM_MODEL: Final = "qwen/qwen3-32b"

# Audio capture
DEFAULT_SAMPLE_RATE: Final = 16000
DEFAULT_CHANNELS: Final = 1
DEFAULT_MAX_DURATION_SECONDS: Final = 7200  # 2 hours

# Recording behaviour
DEFAULT_RECORDING_MODE: Final = "hold"  # hold | toggle
DEFAULT_CLEANUP_ENABLED: Final = True  # remove filler words / fix punctuation

# Hotkey
DEFAULT_HOTKEY_MODIFIERS: Final = ("ctrl", "shift")
DEFAULT_HOTKEY_KEY: Final = "space"
