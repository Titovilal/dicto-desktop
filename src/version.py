"""Single source of truth for the running application version.

Reads the version from the installed package metadata when available
(works for `pip install` / editable installs) and falls back to parsing
``pyproject.toml``. The resolved value is baked into the PyInstaller bundle
via :data:`__version__`, so the frozen app reports the version it was built
from.
"""

from __future__ import annotations

import sys
from pathlib import Path


def _read_from_pyproject() -> str:
    """Parse the version out of pyproject.toml (dev / source runs)."""
    # When frozen, pyproject.toml is not bundled, so this only runs from source.
    root = Path(__file__).resolve().parent.parent
    pyproject = root / "pyproject.toml"
    try:
        for line in pyproject.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("version"):
                # version = "2.6.0"
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        pass
    return "0.0.0"


def _resolve_version() -> str:
    try:
        from importlib.metadata import PackageNotFoundError, version

        try:
            return version("dicto")
        except PackageNotFoundError:
            pass
    except ImportError:
        pass
    return _read_from_pyproject()


# Resolved at import time so the value is frozen into the PyInstaller bundle.
__version__ = _resolve_version()


def get_version() -> str:
    """Return the running application version as a string (e.g. ``2.6.0``)."""
    return __version__


def parse_version(value: str) -> tuple[int, ...]:
    """Parse a ``MAJOR.MINOR.PATCH`` string into a comparable tuple.

    Strips a leading ``v`` and ignores any pre-release/build suffix so that
    ``v2.6.0`` and ``2.6.0`` compare equal. Non-numeric parts become 0.
    """
    value = value.strip().lstrip("vV")
    # Drop anything after the first '-' or '+' (pre-release / build metadata).
    for sep in ("-", "+"):
        if sep in value:
            value = value.split(sep, 1)[0]
    parts: list[int] = []
    for chunk in value.split("."):
        digits = "".join(c for c in chunk if c.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts) if parts else (0,)


def is_newer(remote: str, local: str) -> bool:
    """Return True if ``remote`` is a strictly newer version than ``local``."""

    def _pad(t: tuple[int, ...], n: int) -> tuple[int, ...]:
        return t + (0,) * (n - len(t))

    r, lo = parse_version(remote), parse_version(local)
    n = max(len(r), len(lo))
    return _pad(r, n) > _pad(lo, n)


# Platform detection helper used by the updater UI.
def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))
