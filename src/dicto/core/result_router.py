"""Result router — decide what happens to a finished transcript.

When a transcription completes, three things can happen to the text, and they
are not mutually exclusive:

- **inject** it at the cursor of whatever app has focus (the default — that's
  the whole point of a dictation tool), optionally pressing Enter after;
- **clipboard**: put it on the clipboard, either as the deliberate destination
  or as a *fallback* when injection isn't possible;
- **library**: every transcript is also saved to the user's library (Phase 4),
  so dictation is never lost.

This module is **pure**: it makes the *decision* (a ``RouteDecision``) from the
settings and the runtime capability flags handed to it; the app layer carries
that decision out by calling the injector / clipboard / library services. That
split keeps the policy unit-testable without touching the keyboard or network.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RouteDecision:
    """What to do with a finished transcript.

    ``inject`` and ``clipboard`` can both be true: injection works by copying to
    the clipboard then sending Ctrl+V, so the text ends up there anyway, and we
    surface that explicitly. ``used_fallback`` records that we *wanted* to inject
    but couldn't, so the UI can tell the user "copied to clipboard instead".
    """

    inject: bool
    clipboard: bool
    auto_enter: bool
    save_to_library: bool
    used_fallback: bool = False

    @property
    def primary(self) -> str:
        """A short label for the chosen primary destination (for UI/logs)."""
        if self.inject:
            return "cursor"
        if self.clipboard:
            return "clipboard"
        return "library"


def route_result(
    *,
    text: str,
    auto_paste: bool,
    auto_enter: bool,
    can_inject: bool,
) -> RouteDecision:
    """Decide delivery for a finished transcript.

    Args:
        text: The (already cleaned) transcript text.
        auto_paste: User preference — inject at the cursor by default.
        auto_enter: User preference — press Enter after injecting.
        can_inject: Runtime capability — is keyboard injection available here
            (pynput present, not headless)? When injection is requested but
            unavailable, we fall back to the clipboard.

    Returns:
        A ``RouteDecision``. Empty text yields a no-op decision that still marks
        the transcript for the library (so the save path can decide to skip it).
    """
    if not text.strip():
        return RouteDecision(
            inject=False,
            clipboard=False,
            auto_enter=False,
            save_to_library=False,
        )

    if auto_paste and can_inject:
        # Inject at the cursor. The injector copies to the clipboard as part of
        # pasting, so clipboard is true too.
        return RouteDecision(
            inject=True,
            clipboard=True,
            auto_enter=auto_enter,
            save_to_library=True,
        )

    if auto_paste and not can_inject:
        # Wanted the cursor, can't reach it — clipboard fallback.
        return RouteDecision(
            inject=False,
            clipboard=True,
            auto_enter=False,
            save_to_library=True,
            used_fallback=True,
        )

    # Auto-paste off: deliberate clipboard delivery.
    return RouteDecision(
        inject=False,
        clipboard=True,
        auto_enter=False,
        save_to_library=True,
    )
