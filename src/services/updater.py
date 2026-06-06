"""Self-update support for the desktop app.

Checks the project's GitHub Releases for a newer version and, on frozen builds,
installs it in place: the ``.deb`` via ``pkexec apt-get install`` on Linux, the
``*-setup.exe`` (Inno Setup) launched silently on Windows.

Best-effort: failures surface as :class:`UpdateError`, never raised to the UI.
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
    # Installer for the running platform (.deb on Linux, *-setup.exe on Windows).
    asset_url: str | None
    asset_name: str | None
    # Linux alias of the above, kept for backwards compatibility.
    deb_url: str | None
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
    exe_url: str | None = None
    exe_name: str | None = None
    for asset in data.get("assets", []):
        name = asset.get("name", "")
        if name.endswith(".deb") and deb_url is None:
            deb_url = asset.get("browser_download_url")
            deb_name = name
        # Windows installer published by Inno Setup, e.g. "Dicto-2.7.3-setup.exe".
        elif name.endswith(".exe") and "setup" in name.lower() and exe_url is None:
            exe_url = asset.get("browser_download_url")
            exe_name = name

    # Pick the artifact installable on the running platform.
    if sys.platform == "win32":
        asset_url, asset_name = exe_url, exe_name
    else:
        asset_url, asset_name = deb_url, deb_name

    return UpdateInfo(
        available=is_newer(latest, current),
        current_version=current,
        latest_version=latest.lstrip("vV"),
        release_url=release_url,
        asset_url=asset_url,
        asset_name=asset_name,
        deb_url=deb_url,
        deb_name=deb_name,
    )


def can_self_install() -> bool:
    """True if this build can install an update in place.

    Windows: any frozen bundle (the Inno Setup installer handles files + UAC).
    Linux: a frozen bundle under /opt/dicto with ``pkexec`` available.
    """
    if not getattr(sys, "frozen", False):
        return False

    if sys.platform == "win32":
        return True

    if sys.platform != "linux":
        return False
    if shutil.which("pkexec") is None:
        return False
    # Only offer in-place install when running from the packaged location.
    exe = Path(sys.executable).resolve()
    return str(exe).startswith("/opt/dicto")


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


# Backwards-compatible alias (the .deb is just a release asset).
download_deb = download_asset


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
