"""Unit tests for the self-update service and version helpers."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

import src.services.updater as updater
from src.version import is_newer, parse_version, get_version


class TestVersionParsing:
    def test_parse_strips_v_prefix(self):
        assert parse_version("v2.6.0") == (2, 6, 0)

    def test_parse_drops_prerelease(self):
        assert parse_version("2.6.0-beta1") == (2, 6, 0)
        assert parse_version("2.6.0+build7") == (2, 6, 0)

    def test_parse_non_numeric_becomes_zero(self):
        assert parse_version("2.x.1") == (2, 0, 1)

    def test_is_newer(self):
        assert is_newer("v2.7.0", "2.6.0") is True
        assert is_newer("2.6.1", "2.6.0") is True
        assert is_newer("2.6.0", "2.6.0") is False
        assert is_newer("2.5.0", "2.6.0") is False

    def test_is_newer_differing_lengths(self):
        assert is_newer("2.6", "2.6.0") is False
        assert is_newer("2.6.0.1", "2.6.0") is True

    def test_get_version_non_empty(self):
        assert get_version() and get_version() != "0.0.0"


def _release_response(tag, with_exe=True):
    resp = MagicMock()
    assets = []
    if with_exe:
        assets.append(
            {
                "name": "Dicto-99.0.0-setup.exe",
                "browser_download_url": "https://example/Dicto-99.0.0-setup.exe",
            }
        )
    resp.json.return_value = {
        "tag_name": tag,
        "html_url": "https://example/releases/tag/" + tag,
        "assets": assets,
    }
    resp.raise_for_status = lambda: None
    return resp


class TestCheckForUpdate:
    def test_newer_release_is_available(self):
        with patch.object(
            updater.httpx, "get", return_value=_release_response("v99.0.0")
        ):
            info = updater.check_for_update()
        assert info.available is True
        assert info.latest_version == "99.0.0"
        # asset_url points at the Windows installer.
        assert info.asset_url and info.asset_url.endswith("setup.exe")
        assert info.asset_name == "Dicto-99.0.0-setup.exe"

    def test_same_version_not_available(self):
        tag = "v" + get_version()
        with patch.object(updater.httpx, "get", return_value=_release_response(tag)):
            info = updater.check_for_update()
        assert info.available is False

    def test_network_error_raises_update_error(self):
        with patch.object(updater.httpx, "get", side_effect=Exception("boom")):
            with pytest.raises(updater.UpdateError):
                updater.check_for_update()

    def test_missing_tag_raises(self):
        resp = MagicMock()
        resp.json.return_value = {"assets": []}
        resp.raise_for_status = lambda: None
        with patch.object(updater.httpx, "get", return_value=resp):
            with pytest.raises(updater.UpdateError):
                updater.check_for_update()


class TestCanSelfInstall:
    def test_not_frozen(self, monkeypatch):
        monkeypatch.setattr(sys, "frozen", False, raising=False)
        assert updater.can_self_install() is False

    def test_frozen(self, monkeypatch):
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        assert updater.can_self_install() is True


class TestInstallWindowsSetup:
    def test_missing_file_raises(self):
        with pytest.raises(updater.UpdateError):
            updater.install_windows_setup(Path("/nonexistent/setup.exe"))

    def test_launches_installer_silently_and_exits(self, tmp_path):
        setup = tmp_path / "Dicto-1.0-setup.exe"
        setup.write_bytes(b"x")
        with (
            patch.object(updater.subprocess, "Popen") as popen,
            patch.object(updater.os, "_exit", side_effect=SystemExit) as exit_,
        ):
            with pytest.raises(SystemExit):
                updater.install_windows_setup(setup)
        # The installer is launched with silent flags...
        args = popen.call_args.args[0]
        assert args[0] == str(setup)
        assert "/SILENT" in args
        # ...and we exit so the installer can replace locked files.
        exit_.assert_called_once_with(0)
