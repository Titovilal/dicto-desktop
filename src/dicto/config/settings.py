"""Typed application settings (pydantic) persisted to ``config.yaml``.

Only *local* preferences live here — config is the one thing kept on the
machine besides transient audio and logs. The library, dictionary, transforms
and account live in the user's backend (see ``services/api``).

The model is grouped into nested sections mirroring the old YAML layout so
existing ``config.yaml`` files keep loading. New cross-cutting fields —
``theme`` and ``language`` — drive the ThemeManager and i18n from Phase 0.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

from dicto.config import defaults
from dicto.utils.platform import get_config_path

logger = logging.getLogger(__name__)

Theme = Literal["light", "dark", "system"]
RecordingMode = Literal["hold", "toggle"]


class HotkeySettings(BaseModel):
    modifiers: list[str] = Field(default_factory=lambda: list(defaults.DEFAULT_HOTKEY_MODIFIERS))
    key: str = defaults.DEFAULT_HOTKEY_KEY


class OverlaySettings(BaseModel):
    position: str = "top-right"
    size: int = 100
    opacity: float = 0.9
    # Last dragged position; None means use ``position`` anchor.
    x: int | None = None
    y: int | None = None


class TranscriptionSettings(BaseModel):
    api_key: str = ""
    language: str = defaults.DEFAULT_TRANSCRIBE_LANGUAGE
    model: str = defaults.DEFAULT_STT_MODEL


class AudioSettings(BaseModel):
    sample_rate: int = defaults.DEFAULT_SAMPLE_RATE
    channels: int = defaults.DEFAULT_CHANNELS
    max_duration: int = defaults.DEFAULT_MAX_DURATION_SECONDS
    input_device: int | None = None
    include_system_audio: bool = False


class BehaviorSettings(BaseModel):
    auto_paste: bool = False
    auto_enter: bool = False
    always_on_top: bool = False
    recording_mode: RecordingMode = defaults.DEFAULT_RECORDING_MODE
    cleanup_enabled: bool = defaults.DEFAULT_CLEANUP_ENABLED


class TransformSettings(BaseModel):
    model: str = defaults.DEFAULT_TRANSFORM_MODEL


class AppearanceSettings(BaseModel):
    theme: Theme = defaults.DEFAULT_THEME
    language: str = defaults.DEFAULT_LANGUAGE


class Settings(BaseModel):
    """Root settings document. Persisted as YAML."""

    hotkey: HotkeySettings = Field(default_factory=HotkeySettings)
    overlay: OverlaySettings = Field(default_factory=OverlaySettings)
    transcription: TranscriptionSettings = Field(default_factory=TranscriptionSettings)
    audio: AudioSettings = Field(default_factory=AudioSettings)
    behavior: BehaviorSettings = Field(default_factory=BehaviorSettings)
    transform: TransformSettings = Field(default_factory=TransformSettings)
    appearance: AppearanceSettings = Field(default_factory=AppearanceSettings)

    # Path is not persisted; tracked so save() knows where to write.
    _path: Path | None = None

    # ── load / save ───────────────────────────────────────────────────

    @classmethod
    def load(cls, path: str | os.PathLike[str] | None = None) -> Settings:
        """Load settings from ``path`` (default: ``%APPDATA%\\dicto\\config.yaml``).

        Missing or unreadable files fall back to defaults. Unknown keys in the
        YAML are ignored; missing keys use their defaults.
        """
        config_path = Path(path) if path is not None else get_config_path()
        data: dict = {}
        if config_path.exists():
            try:
                data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
            except Exception:  # noqa: BLE001 — corrupt config must not crash startup
                logger.warning("failed to read %s, using defaults", config_path, exc_info=True)
                data = {}

        try:
            settings = cls.model_validate(data)
        except Exception:  # noqa: BLE001 — invalid config must not crash startup
            logger.warning("invalid config at %s, using defaults", config_path, exc_info=True)
            settings = cls()

        settings._path = config_path
        settings._apply_env_overrides()
        return settings

    def _apply_env_overrides(self) -> None:
        """Env vars win over the file (handy for dev and CI)."""
        api_key = os.environ.get("DICTO_API_KEY")
        if api_key:
            self.transcription.api_key = api_key

    def save(self, path: str | os.PathLike[str] | None = None) -> bool:
        """Write settings back to YAML. Returns True on success."""
        target = Path(path) if path is not None else (self._path or get_config_path())
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                yaml.safe_dump(self.model_dump(mode="json"), default_flow_style=False),
                encoding="utf-8",
            )
            self._path = target
            logger.info("settings saved to %s", target)
            return True
        except Exception:  # noqa: BLE001
            logger.error("failed to save settings to %s", target, exc_info=True)
            return False


# ── module-level singleton ───────────────────────────────────────────────

_settings: Settings | None = None


def get_settings(path: str | os.PathLike[str] | None = None) -> Settings:
    """Return the process-wide Settings, loading it on first call."""
    global _settings
    if _settings is None:
        _settings = Settings.load(path)
    return _settings


def reset_settings() -> None:
    """Drop the cached singleton (tests)."""
    global _settings
    _settings = None
