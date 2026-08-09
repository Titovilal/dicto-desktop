"""Which Qt platform plugin the app picks on a Wayland session.

Wayland gives a regular app no way to raise itself above other windows, so
`WindowStaysOnTopHint` is silently dropped there and the "always on top" /
"persistent overlay" toggles do nothing. XWayland still honors the hint, so the
app switches to the xcb plugin — but only when a toggle is actually enabled.
"""

from __future__ import annotations

import pytest
import yaml

import src.main as main_module


@pytest.fixture
def config_file(tmp_path, monkeypatch):
    """Point get_config_dir() at a throwaway config.yaml."""
    cfg_dir = tmp_path / "dicto"
    cfg_dir.mkdir(parents=True)
    monkeypatch.setattr(
        "src.config.settings.get_config_dir", lambda: cfg_dir, raising=True
    )
    return cfg_dir / "config.yaml"


def _write(config_file, **behavior):
    config_file.write_text(yaml.safe_dump({"behavior": behavior}), encoding="utf-8")


@pytest.fixture
def wayland(monkeypatch):
    monkeypatch.setattr(main_module.sys, "platform", "linux")
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.delenv("QT_QPA_PLATFORM", raising=False)


class TestForceXWaylandWhenPinned:
    def test_switches_to_xcb_when_always_on_top_is_set(
        self, config_file, wayland, monkeypatch
    ):
        _write(config_file, always_on_top=True)
        main_module._force_xwayland_if_pinned()
        assert main_module.os.environ.get("QT_QPA_PLATFORM") == "xcb"

    def test_switches_to_xcb_when_persistent_overlay_is_set(
        self, config_file, wayland
    ):
        _write(config_file, persistent_overlay=True)
        main_module._force_xwayland_if_pinned()
        assert main_module.os.environ.get("QT_QPA_PLATFORM") == "xcb"

    def test_stays_on_native_wayland_when_nothing_is_pinned(self, config_file, wayland):
        _write(config_file, always_on_top=False, persistent_overlay=False)
        main_module._force_xwayland_if_pinned()
        assert main_module.os.environ.get("QT_QPA_PLATFORM") is None

    def test_never_overrides_an_explicit_user_choice(
        self, config_file, wayland, monkeypatch
    ):
        _write(config_file, always_on_top=True)
        monkeypatch.setenv("QT_QPA_PLATFORM", "wayland")
        main_module._force_xwayland_if_pinned()
        assert main_module.os.environ.get("QT_QPA_PLATFORM") == "wayland"

    def test_ignores_a_missing_config(self, config_file, wayland):
        assert not config_file.exists()
        main_module._force_xwayland_if_pinned()
        assert main_module.os.environ.get("QT_QPA_PLATFORM") is None

    def test_a_corrupt_config_does_not_stop_startup(self, config_file, wayland):
        config_file.write_text("{{{ not yaml", encoding="utf-8")
        main_module._force_xwayland_if_pinned()
        assert main_module.os.environ.get("QT_QPA_PLATFORM") is None

    def test_left_alone_on_an_x11_session(self, config_file, monkeypatch):
        monkeypatch.setattr(main_module.sys, "platform", "linux")
        monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
        monkeypatch.delenv("QT_QPA_PLATFORM", raising=False)
        _write(config_file, always_on_top=True)
        main_module._force_xwayland_if_pinned()
        assert main_module.os.environ.get("QT_QPA_PLATFORM") is None

    def test_importing_main_does_not_touch_the_environment(self):
        """The switch must be driven from main(), never from import.

        Doing it at import time picked up whatever config.yaml sat in the CWD
        and forced xcb on anything that merely imported the module — which hung
        the test suite on a machine with no X server.
        """
        import os as _os
        import subprocess
        import sys as _sys

        env = {k: v for k, v in _os.environ.items() if k != "QT_QPA_PLATFORM"}
        env["XDG_SESSION_TYPE"] = "wayland"
        result = subprocess.run(
            [
                _sys.executable,
                "-c",
                "import os, src.main; "
                "print(repr(os.environ.get('QT_QPA_PLATFORM')))",
            ],
            capture_output=True,
            text=True,
            env=env,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "None"

    def test_left_alone_on_non_linux(self, config_file, monkeypatch):
        monkeypatch.setattr(main_module.sys, "platform", "win32")
        monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
        monkeypatch.delenv("QT_QPA_PLATFORM", raising=False)
        _write(config_file, always_on_top=True)
        main_module._force_xwayland_if_pinned()
        assert main_module.os.environ.get("QT_QPA_PLATFORM") is None
