"""Windows path helpers and OS detection.

Dicto is Windows-only. The only state we keep on the local machine is config,
audio chunks while recording, and logs — everything else lives in the user's
backend. These helpers centralise *where* those local files go so the rest of
the app never hardcodes a path.

Layout under ``%APPDATA%\\dicto`` (per-user, writable even when the app is
installed in Program Files)::

    %APPDATA%\\dicto\\
        config.yaml         # settings
        logs\\dicto.log      # rotating log
        audio\\<session>\\   # chunks while recording (transient)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "dicto"


def is_frozen() -> bool:
    """True when running from a PyInstaller-frozen executable."""
    return bool(getattr(sys, "frozen", False))


def get_app_dir() -> Path:
    """Directory the app runs from.

    Frozen: the folder containing the ``.exe``. From source: the project root
    (``src/dicto/utils/platform.py`` -> up four levels).
    """
    if is_frozen():
        return Path(sys.executable).parent
    return Path(__file__).resolve().parents[3]


def get_data_dir() -> Path:
    """Per-user writable data directory: ``%APPDATA%\\dicto``.

    Created on demand. When running from source we still use ``%APPDATA%`` so
    dev and installed runs share one settings location.
    """
    base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
    data_dir = Path(base) / APP_NAME
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_config_path() -> Path:
    """Path to the writable ``config.yaml``."""
    return get_data_dir() / "config.yaml"


def get_logs_dir() -> Path:
    d = get_data_dir() / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_audio_dir() -> Path:
    """Root for transient recording chunks, ``%APPDATA%\\dicto\\audio``."""
    d = get_data_dir() / "audio"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_session_audio_dir(session_id: str) -> Path:
    """Per-session folder that holds the chunks for one recording."""
    d = get_audio_dir() / session_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_assets_dir() -> Path:
    """Bundled assets (icons, fonts).

    Frozen builds unpack assets next to the executable under ``assets``; from
    source they live at ``<project_root>/assets``.
    """
    if is_frozen():
        bundled = Path(getattr(sys, "_MEIPASS", get_app_dir())) / "assets"
        if bundled.exists():
            return bundled
    return get_app_dir() / "assets"
