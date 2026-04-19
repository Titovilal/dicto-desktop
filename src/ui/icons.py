"""
SVG icon loader — reads .svg files from the assets directory.
"""

from pathlib import Path

_ASSETS = Path(__file__).parent / "assets"
_cache: dict[str, str] = {}


def load_svg(name: str) -> str:
    """Load an SVG file by name (without extension) and cache the result."""
    if name not in _cache:
        _cache[name] = (_ASSETS / f"{name}.svg").read_text(encoding="utf-8").strip()
    return _cache[name]


# Convenience constants (lazy-loaded on first access via module-level getattr)
_ICON_NAMES = [
    "settings",
    "close",
    "external",
    "audio_lines",
    "back",
    "models",
    "settings_small",
    "record",
    "stop",
    "reset",
    "bug_report",
    "speaker",
    "speaker_off",
]


def __getattr__(name: str) -> str:
    prefix = "SVG_"
    if name.startswith(prefix):
        key = name[len(prefix) :].lower()
        if key in _ICON_NAMES:
            return load_svg(key)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
