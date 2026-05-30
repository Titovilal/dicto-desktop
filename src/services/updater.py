"""Self-update support for the desktop app.

Checks the project's GitHub Releases for a newer version and, on Linux, can
download the published ``.deb`` and install it via ``pkexec apt-get install``
(which prompts the user for authentication through PolicyKit).

The whole flow is best-effort and never raises to the caller: callers receive
structured results / exceptions wrapped in :class:`UpdateError`.
"""

from __future__ import annotations

import os
import sys
import shutil
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
    deb_url: str | None  # download URL for the .deb asset, if any
    deb_name: str | None


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

    deb_url: str | None = None
    deb_name: str | None = None
    for asset in data.get("assets", []):
        name = asset.get("name", "")
        if name.endswith(".deb"):
            deb_url = asset.get("browser_download_url")
            deb_name = name
            break

    return UpdateInfo(
        available=is_newer(latest, current),
        current_version=current,
        latest_version=latest.lstrip("vV"),
        release_url=release_url,
        deb_url=deb_url,
        deb_name=deb_name,
    )


def can_self_install() -> bool:
    """True if this build can install a .deb update in place.

    Requires: running on Linux, as a frozen bundle installed under a system
    path (the .deb installs to /opt/dicto), and a PolicyKit agent (``pkexec``)
    available to elevate the install.
    """
    if sys.platform != "linux":
        return False
    if not getattr(sys, "frozen", False):
        return False
    if shutil.which("pkexec") is None:
        return False
    # Only offer in-place install when running from the packaged location.
    exe = Path(sys.executable).resolve()
    return str(exe).startswith("/opt/dicto")


def download_deb(deb_url: str, deb_name: str, timeout: float = 120.0) -> Path:
    """Download the .deb asset to a temp file and return its path."""
    tmp_dir = Path(tempfile.gettempdir()) / "dicto-update"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    dest = tmp_dir / deb_name

    try:
        with httpx.stream("GET", deb_url, timeout=timeout, follow_redirects=True) as r:
            r.raise_for_status()
            with open(dest, "wb") as fh:
                for chunk in r.iter_bytes(chunk_size=64 * 1024):
                    fh.write(chunk)
    except Exception as exc:  # noqa: BLE001
        raise UpdateError(f"Failed to download update: {exc}") from exc

    logger.info("Downloaded update package to %s", dest)
    return dest


def install_deb(deb_path: Path) -> None:
    """Install the given .deb via ``pkexec apt-get install`` (prompts for auth).

    Uses ``apt-get`` so dependencies are resolved. Raises :class:`UpdateError`
    if the install command fails or is cancelled.
    """
    if not deb_path.is_file():
        raise UpdateError(f"Update package not found: {deb_path}")

    cmd = [
        "pkexec",
        "apt-get",
        "install",
        "-y",
        "--reinstall",
        "--allow-downgrades",
        str(deb_path),
    ]
    logger.info("Installing update: %s", " ".join(cmd))
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
        )
    except Exception as exc:  # noqa: BLE001
        raise UpdateError(f"Failed to launch installer: {exc}") from exc

    if proc.returncode == 126:
        # pkexec: user dismissed the authentication dialog.
        raise UpdateError("Installation cancelled")
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        raise UpdateError(f"Installer failed (code {proc.returncode}): {detail}")

    logger.info("Update installed successfully")


def restart_app() -> None:
    """Relaunch the application and exit the current process."""
    exe = sys.executable
    logger.info("Restarting application: %s", exe)
    try:
        subprocess.Popen([exe])
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to restart app: %s", exc)
    os._exit(0)
