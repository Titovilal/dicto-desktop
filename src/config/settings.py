"""
Configuration management for Dicto application.
"""

from __future__ import annotations

import os
import sys
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def get_app_dir() -> Path:
    """Get the directory where the application is located.

    When running as a PyInstaller executable, returns the directory containing the .exe.
    When running as a script, returns the project root directory.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    else:
        return Path(__file__).parent.parent.parent


def _config_property(section: str, key: str, default=None):
    """Create a property that reads/writes from a nested config dict.

    Handles both flat keys (section=key, key=None) and nested keys (section.key).
    Setters auto-create the section dict if missing.
    """

    def getter(self):
        if section in self.config and isinstance(self.config[section], dict):
            return self.config[section].get(key, default)
        return default

    def setter(self, value):
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value

    return property(getter, setter)


def _flat_config_property(key: str, default=None):
    """Property for top-level config keys."""

    def getter(self):
        return self.config.get(key, default)

    def setter(self, value):
        self.config[key] = value

    return property(getter, setter)


class Settings:
    """Manages application configuration from config.yaml and environment variables."""

    DEFAULT_CONFIG = {
        "hotkey": {"modifiers": ["ctrl", "shift"], "key": "space"},
        "overlay": {"position": "top-right", "size": 100, "opacity": 0.9},
        "transcription": {"api_key": "", "language": "es", "model": "v3-turbo"},
        "audio": {"sample_rate": 16000, "max_duration": 120, "channels": 1},
        "behavior": {
            "auto_paste": False,
            "auto_enter": False,
            "always_on_top": False,
            "persistent_overlay": False,
        },
        "edit_hotkey": {"modifiers": ["ctrl", "alt"], "key": "space"},
        "edit": {"auto_paste": True, "auto_enter": False},
        "transformation": {"model": "qwen/qwen3-32b"},
        "edition": {"model": "qwen/qwen3-32b"},
        "ui_language": "es",
    }

    config_path: Path
    config: Dict[str, Any]

    def __init__(self, config_path: str | None = None):
        if config_path is None:
            self.config_path = get_app_dir() / "config.yaml"
        else:
            self.config_path = Path(config_path)
        self.config = self._load_config()
        self._apply_env_overrides()

    def _load_config(self) -> Dict[str, Any]:
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    loaded_config = yaml.safe_load(f) or {}
                config = self.DEFAULT_CONFIG.copy()
                self._deep_merge(config, loaded_config)
                return config
            except Exception as e:
                logger.warning(f"Failed to load config from {self.config_path}: {e}")
                logger.warning("Using default configuration.")
                return self.DEFAULT_CONFIG.copy()
        else:
            logger.info(f"Config file not found at {self.config_path}. Using defaults.")
            return self.DEFAULT_CONFIG.copy()

    def _deep_merge(self, base: Dict, override: Dict) -> None:
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def _apply_env_overrides(self) -> None:
        api_key_env = os.environ.get("DICTO_API_KEY")
        if api_key_env:
            self.config["transcription"]["api_key"] = api_key_env

    # ── Hotkey settings ──────────────────────────────────────

    hotkey_modifiers: List[str] = _config_property(
        "hotkey", "modifiers", ["ctrl", "shift"]
    )
    hotkey_key: str = _config_property("hotkey", "key", "space")

    # ── Overlay settings ─────────────────────────────────────

    overlay_position: str = _config_property("overlay", "position", "top-right")
    overlay_size: int = _config_property("overlay", "size", 100)
    overlay_opacity: float = _config_property("overlay", "opacity", 0.9)

    # ── Transcription settings ───────────────────────────────

    transcription_api_key: str = _config_property("transcription", "api_key", "")
    transcription_language: str = _config_property("transcription", "language", "es")
    transcription_model: str = _config_property("transcription", "model", "v3-turbo")

    # ── Audio settings ───────────────────────────────────────

    audio_sample_rate: int = _config_property("audio", "sample_rate", 16000)
    audio_max_duration: int = _config_property("audio", "max_duration", 120)
    audio_channels: int = _config_property("audio", "channels", 1)

    # ── Behavior settings ────────────────────────────────────

    auto_paste: bool = _config_property("behavior", "auto_paste", False)
    auto_enter: bool = _config_property("behavior", "auto_enter", False)
    always_on_top: bool = _config_property("behavior", "always_on_top", False)
    persistent_overlay: bool = _config_property("behavior", "persistent_overlay", False)

    # ── Edit hotkey settings ─────────────────────────────────

    edit_hotkey_modifiers: List[str] = _config_property(
        "edit_hotkey", "modifiers", ["ctrl", "alt"]
    )
    edit_hotkey_key: str = _config_property("edit_hotkey", "key", "space")

    # ── Edit behavior settings ───────────────────────────────

    edit_auto_paste: bool = _config_property("edit", "auto_paste", True)
    edit_auto_enter: bool = _config_property("edit", "auto_enter", False)

    # ── Transformation model ──────────────────────────────────

    transformation_model: str = _config_property(
        "transformation", "model", "qwen/qwen3-32b"
    )

    # ── Edition model ─────────────────────────────────────────

    edition_model: str = _config_property("edition", "model", "qwen/qwen3-32b")

    # ── UI settings ──────────────────────────────────────────

    ui_language: str = _flat_config_property("ui_language", "es")

    # ── Persistence ──────────────────────────────────────────

    def save(self) -> None:
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(self.config, f, default_flow_style=False)
            logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")

    def create_default_config(self) -> None:
        if not self.config_path.exists():
            self.config = self.DEFAULT_CONFIG.copy()
            self.save()
            logger.info(f"Created default configuration at {self.config_path}")


# Global settings instance
_settings_instance = None


def get_settings(config_path: str | None = None) -> Settings:
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings(config_path)
    return _settings_instance
