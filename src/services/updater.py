"""Self-update support for the desktop app.

Checks the project's GitHub Releases for a newer version and, on frozen builds,
installs it in place: the ``*-setup.exe`` (Inno Setup) launched silently.

Best-effort: failures surface as :class:`UpdateError`, never raised to the UI.
"""

from __future__ import annotations

import os
import sys
import logging
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import httpx

from src.version import get_version, is_newer

logger = logging.getLogger(__name__)

# GitHub repo that publishes the releases (see .github/workflows/build.yml).
GITHUB_REPO = os.environ.get("DICTO_UPDATE_REPO", "Titovilal/dicto-desktop")
_RELEASES_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


class UpdateError(Exception):
    """Raised when an update check or installation fails."""


@dataclass
class UpdateInfo:
    """Result of an update check."""

    available: bool
    current_version: str
    latest_version: str
    release_url: str
    # Windows installer (*-setup.exe).
    asset_url: str | None
    asset_name: str | None


def check_for_update(timeout: float = 15.0) -> UpdateInfo:
    """Query GitHub for the latest release and compare against the running version.

    Raises :class:`UpdateError` on network / parsing failures.
    """
    current = get_version()
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        resp = httpx.get(_RELEASES_API, headers=headers, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:  # noqa: BLE001 - surface a uniform error type
        raise UpdateError(f"Could not reach update server: {exc}") from exc

    latest = str(data.get("tag_name") or data.get("name") or "").strip()
    if not latest:
        raise UpdateError("Release metadata did not include a version tag")

    release_url = data.get("html_url", f"https://github.com/{GITHUB_REPO}/releases")

    asset_url: str | None = None
    asset_name: str | None = None
    for asset in data.get("assets", []):
        name = asset.get("name", "")
        # Windows installer published by Inno Setup, e.g. "Dicto-2.7.3-setup.exe".
        if name.endswith(".exe") and "setup" in name.lower() and asset_url is None:
            asset_url = asset.get("browser_download_url")
            asset_name = name

    return UpdateInfo(
        available=is_newer(latest, current),
        current_version=current,
        latest_version=latest.lstrip("vV"),
        release_url=release_url,
        asset_url=asset_url,
        asset_name=asset_name,
    )


def can_self_install() -> bool:
    """True if this build can install an update in place.

    Any frozen bundle qualifies (the Inno Setup installer handles files + UAC).
    """
    return bool(getattr(sys, "frozen", False))


def download_asset(asset_url: str, asset_name: str, timeout: float = 120.0) -> Path:
    """Download a release asset to a temp file and return its path."""
    tmp_dir = Path(tempfile.gettempdir()) / "dicto-update"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    dest = tmp_dir / asset_name

    try:
        with httpx.stream("GET", asset_url, timeout=timeout, follow_redirects=True) as r:
            r.raise_for_status()
            with open(dest, "wb") as fh:
                for chunk in r.iter_bytes(chunk_size=64 * 1024):
                    fh.write(chunk)
    except Exception as exc:  # noqa: BLE001
        raise UpdateError(f"Failed to download update: {exc}") from exc

    logger.info("Downloaded update package to %s", dest)
    return dest


def install_windows_setup(exe_path: Path) -> None:
    """Launch the Inno Setup installer silently and exit so it can replace files.

    The running exe locks its own files, so we hand off to the installer and exit;
    Inno upgrades in place and relaunches the app via its [Run] section. Does not
    return — it terminates the process.
    """
    if not exe_path.is_file():
        raise UpdateError(f"Update installer not found: {exe_path}")

    # /SILENT: progress window, no wizard. /CLOSEAPPLICATIONS: shut us down
    # cleanly. /NORESTART: don't reboot Windows. [Run] relaunches Dicto after.
    cmd = [
        str(exe_path),
        "/SILENT",
        "/CLOSEAPPLICATIONS",
        "/RESTARTAPPLICATIONS=no",
        "/NORESTART",
    ]
    logger.info("Launching Windows installer: %s", " ".join(cmd))
    try:
        subprocess.Popen(cmd, close_fds=True)
    except Exception as exc:  # noqa: BLE001
        raise UpdateError(f"Failed to launch installer: {exc}") from exc

    # Give the installer a moment to start, then release our file locks by exiting.
    logger.info("Exiting so the installer can replace application files")
    os._exit(0)


def restart_app() -> None:
    """Relaunch the application and exit the current process."""
    exe = sys.executable
    logger.info("Restarting application: %s", exe)
    try:
        subprocess.Popen([exe])
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to restart app: %s", exc)
    os._exit(0)
