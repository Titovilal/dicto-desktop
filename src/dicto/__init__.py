"""Dicto — voice-to-text desktop app for Windows.

Layered architecture (see REBUILD_PLAN.md):

    core      pure logic (no Qt, no network, no OS)
    audio     audio capture (isolated side effects)
    services  external effects (network, OS)
    transform AI presets (declarative)
    config    typed settings
    i18n      translations + languageChanged
    ui        Qt widgets, consuming theme tokens
    utils     logging, OS paths
"""

from dicto.version import __version__

__all__ = ["__version__"]
