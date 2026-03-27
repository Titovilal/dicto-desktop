"""Unit tests for Settings configuration management."""

from __future__ import annotations

import yaml

from src.config.settings import Settings


class TestSettingsDefaults:
    """Settings should use sensible defaults when config is missing or empty."""

    def test_loads_defaults_when_no_file(self, tmp_path):
        path = tmp_path / "nonexistent.yaml"
        s = Settings(config_path=str(path))
        assert s.hotkey_key == "space"
        assert s.hotkey_modifiers == ["ctrl", "shift"]
        assert s.transcription_language == "es"
        assert s.transcription_model == "v3-turbo"
        assert s.auto_paste is False
        assert s.ui_language == "es"

    def test_loads_defaults_when_file_empty(self, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text("", encoding="utf-8")
        s = Settings(config_path=str(path))
        assert s.hotkey_key == "space"

    def test_loads_defaults_when_file_invalid_yaml(self, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text("{{{{not yaml at all", encoding="utf-8")
        s = Settings(config_path=str(path))
        assert s.hotkey_key == "space"


class TestSettingsLoading:
    """Settings should merge user config on top of defaults."""

    def test_partial_override(self, custom_config):
        path = custom_config({"hotkey": {"key": "f1"}})
        s = Settings(config_path=path)
        # Overridden value
        assert s.hotkey_key == "f1"
        # Default preserved via deep merge
        assert s.hotkey_modifiers == ["ctrl", "shift"]

    def test_extra_keys_ignored(self, custom_config):
        path = custom_config(
            {"hotkey": {"key": "space"}, "unknown_section": {"foo": 1}}
        )
        s = Settings(config_path=path)
        assert s.hotkey_key == "space"
        assert "unknown_section" in s.config  # preserved, not crash

    def test_flat_config_property(self, custom_config):
        path = custom_config({"ui_language": "en"})
        s = Settings(config_path=path)
        assert s.ui_language == "en"

    def test_nested_config_property_setter(self, default_settings):
        default_settings.hotkey_key = "f2"
        assert default_settings.hotkey_key == "f2"
        assert default_settings.config["hotkey"]["key"] == "f2"

    def test_flat_config_property_setter(self, default_settings):
        default_settings.ui_language = "de"
        assert default_settings.ui_language == "de"

    def test_setter_creates_section_if_missing(self, default_settings):
        # Remove a section entirely
        del default_settings.config["hotkey"]
        default_settings.hotkey_key = "tab"
        assert default_settings.hotkey_key == "tab"


class TestSettingsEnvOverride:
    """Environment variables should override config file values."""

    def test_api_key_from_env(self, tmp_path, monkeypatch):
        monkeypatch.setenv("DICTO_API_KEY", "sk-dicto-test123")
        path = tmp_path / "config.yaml"
        s = Settings(config_path=str(path))
        assert s.transcription_api_key == "sk-dicto-test123"

    def test_env_overrides_config_file(self, custom_config, monkeypatch):
        monkeypatch.setenv("DICTO_API_KEY", "sk-dicto-env")
        path = custom_config({"transcription": {"api_key": "sk-dicto-file"}})
        s = Settings(config_path=path)
        assert s.transcription_api_key == "sk-dicto-env"


class TestSettingsSave:
    """Settings.save() should persist to disk as valid YAML."""

    def test_save_creates_file(self, tmp_path):
        path = tmp_path / "config.yaml"
        s = Settings(config_path=str(path))
        s.hotkey_key = "f5"
        s.save()

        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert loaded["hotkey"]["key"] == "f5"

    def test_save_roundtrip(self, tmp_path):
        path = tmp_path / "config.yaml"
        s = Settings(config_path=str(path))
        s.auto_paste = True
        s.ui_language = "fr"
        s.save()

        s2 = Settings(config_path=str(path))
        assert s2.auto_paste is True
        assert s2.ui_language == "fr"

    def test_create_default_config(self, tmp_path):
        path = tmp_path / "config.yaml"
        s = Settings(config_path=str(path))
        s.create_default_config()
        assert path.exists()
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
        # Verify it wrote valid YAML with expected structure
        assert "hotkey" in loaded
        assert "key" in loaded["hotkey"]
