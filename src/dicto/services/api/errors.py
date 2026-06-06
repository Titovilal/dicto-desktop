"""Typed API errors shared across all service clients.

The pipeline distinguishes *retryable* failures (network blip, rate limit,
server 5xx) from *terminal* ones (bad key, audio too long) so it knows whether
to re-queue a job from the audio still on disk or give up and surface the error.
Each error carries a short machine ``code`` mirrored into ``ErrorOccurred``
events for the UI.
"""

from __future__ import annotations


class APIError(Exception):
    """Base for all API failures.

    Args:
        message: human-readable detail.
        code: short machine code (``auth``, ``rate_limit``, ``network``, …).
        retryable: whether retrying the same request from disk could succeed.
    """

    code: str = "api"
    retryable: bool = False

    def __init__(self, message: str, *, code: str | None = None, retryable: bool | None = None):
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code
        if retryable is not None:
            self.retryable = retryable


class AuthError(APIError):
    """API key is invalid or missing. Not retryable — needs user action."""

    code = "auth"
    retryable = False


class RateLimitError(APIError):
    """Rate or spending limit hit. Retryable after a backoff."""

    code = "rate_limit"
    retryable = True


class QuotaExceededError(APIError):
    """Included minutes exhausted. Not retryable — needs a plan change."""

    code = "quota"
    retryable = False


class NetworkError(APIError):
    """Connection/timeout problem. Retryable — the audio is safe on disk."""

    code = "network"
    retryable = True


class ServerError(APIError):
    """5xx from the backend. Retryable."""

    code = "server"
    retryable = True


class AudioTooLongError(APIError):
    """The audio file exceeds the API size limit. Not retryable as-is."""

    code = "audio_too_long"
    retryable = False


class AudioTooShortError(APIError):
    """The audio file is empty / too short to transcribe. Not retryable."""

    code = "audio_too_short"
    retryable = False
