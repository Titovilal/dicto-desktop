"""
Configuration management for Dicto application.
"""

import os
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, List, cast

logger = logging.getLogger(__name__)


class Settings:
    """Manages application configuration from config.yaml and environment variables."""

    DEFAULT_CONFIG = {
        "hotkey": {"modifiers": ["ctrl", "shift"], "key": "space"},
        "overlay": {"position": "top-right", "size": 100, "opacity": 0.9},
        "transcription": {"provider": "groq", "api_key": "", "language": "auto"},
        "audio": {"sample_rate": 16000, "max_duration": 120, "channels": 1},
        "behavior": {"auto_paste": False, "auto_enter": False},
    }

    config_path: Path
    config: Dict[str, Any]

    def __init__(self, config_path: str | None = None):
        """
        Initialize settings.

        Args:
            config_path: Path to config.yaml file. If None, looks in current directory.
        """
        if config_path is None:
            self.config_path = Path.cwd() / "config.yaml"
        else:
            self.config_path = Path(config_path)
        self.config = self._load_config()
        self._apply_env_overrides()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from yaml file or use defaults."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    loaded_config = yaml.safe_load(f) or {}

                # Merge with defaults
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
        """Recursively merge override dict into base dict."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides."""
        # API key from environment (check provider-specific key first, then generic)
        provider = self.config["transcription"]["provider"]

        if provider == "groq":
            api_key_env = os.environ.get("GROQ_API_KEY")
        elif provider == "openai":
            api_key_env = os.environ.get("OPENAI_API_KEY")
        else:
            api_key_env = None

        if api_key_env:
            self.config["transcription"]["api_key"] = api_key_env

    # Hotkey settings
    @property
    def hotkey_modifiers(self) -> List[str]:
        """Get hotkey modifiers (e.g., ['ctrl', 'shift'])."""
        return cast(List[str], self.config["hotkey"]["modifiers"])

    @property
    def hotkey_key(self) -> str:
        """Get hotkey key (e.g., 'space')."""
        return cast(str, self.config["hotkey"]["key"])

    # Overlay settings
    @property
    def overlay_position(self) -> str:
        """Get overlay position on screen."""
        return cast(str, self.config["overlay"]["position"])

    @property
    def overlay_size(self) -> int:
        """Get overlay size in pixels."""
        return cast(int, self.config["overlay"]["size"])

    @property
    def overlay_opacity(self) -> float:
        """Get overlay opacity (0.0 to 1.0)."""
        return cast(float, self.config["overlay"]["opacity"])

    # Transcription settings
    @property
    def transcription_provider(self) -> str:
        """Get transcription provider (e.g., 'openai')."""
        return cast(str, self.config["transcription"]["provider"])

    @property
    def transcription_api_key(self) -> str:
        """Get transcription API key."""
        return cast(str, self.config["transcription"]["api_key"])

    @transcription_api_key.setter
    def transcription_api_key(self, value: str) -> None:
        """Set transcription API key."""
        self.config["transcription"]["api_key"] = value

    @property
    def transcription_language(self) -> str:
        """Get transcription language (e.g., 'auto', 'es', 'en')."""
        return cast(str, self.config["transcription"]["language"])

    @transcription_language.setter
    def transcription_language(self, value: str) -> None:
        """Set transcription language."""
        self.config["transcription"]["language"] = value

    # Audio settings
    @property
    def audio_sample_rate(self) -> int:
        """Get audio sample rate in Hz."""
        return cast(int, self.config["audio"]["sample_rate"])

    @property
    def audio_max_duration(self) -> int:
        """Get maximum recording duration in seconds."""
        return cast(int, self.config["audio"]["max_duration"])

    @property
    def audio_channels(self) -> int:
        """Get number of audio channels (1 for mono, 2 for stereo)."""
        return cast(int, self.config["audio"]["channels"])

    # Behavior settings
    @property
    def auto_paste(self) -> bool:
        """Get auto-paste setting (Ctrl+V after copy)."""
        return cast(bool, self.config.get("behavior", {}).get("auto_paste", False))

    @auto_paste.setter
    def auto_paste(self, value: bool) -> None:
        """Set auto-paste setting."""
        if "behavior" not in self.config:
            self.config["behavior"] = {}
        self.config["behavior"]["auto_paste"] = value

    @property
    def auto_enter(self) -> bool:
        """Get auto-enter setting (press Enter after paste)."""
        return cast(bool, self.config.get("behavior", {}).get("auto_enter", False))

    @auto_enter.setter
    def auto_enter(self, value: bool) -> None:
        """Set auto-enter setting."""
        if "behavior" not in self.config:
            self.config["behavior"] = {}
        self.config["behavior"]["auto_enter"] = value

    def save(self) -> None:
        """Save current configuration to yaml file."""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(self.config, f, default_flow_style=False)
            logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")

    def create_default_config(self) -> None:
        """Create a default config.yaml file if it doesn't exist."""
        if not self.config_path.exists():
            self.config = self.DEFAULT_CONFIG.copy()
            self.save()
            logger.info(f"Created default configuration at {self.config_path}")


# Global settings instance
_settings_instance = None


def get_settings(config_path: str | None = None) -> Settings:
    """
    Get the global settings instance.

    Args:
        config_path: Path to config file. Only used on first call.

    Returns:
        Settings instance
    """
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings(config_path)
    return _settings_instance
