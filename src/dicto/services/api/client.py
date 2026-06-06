"""Base httpx client: auth, retries with backoff, and error normalisation.

Every API call goes through :meth:`ApiClient.request`, which maps HTTP/transport
failures onto the typed errors in ``errors.py`` and retries *retryable* ones
with exponential backoff. Endpoint modules (``transcribe.py`` …) build the
request and parse the success body; this class owns the cross-cutting concerns.

The client is sync (httpx.Client). The pipeline runs it off the Qt thread, so
blocking here is fine and keeps the call sites simple.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable

import httpx

from dicto.services.api import errors

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 60.0
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF = 2.0  # seconds; doubled each attempt


class ApiClient:
    """Thin authenticated wrapper over ``httpx.Client`` with typed errors."""

    def __init__(
        self,
        api_key: str,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff: float = DEFAULT_BACKOFF,
        client: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if not api_key:
            raise errors.AuthError("Dicto API key is required")
        self.api_key = api_key
        self.max_retries = max_retries
        self.backoff = backoff
        self._sleep = sleep
        self._client = client or httpx.Client(timeout=timeout)

    def auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Send a request, retrying retryable failures with backoff.

        ``kwargs`` are forwarded to ``httpx.Client.request`` (``files``,
        ``data``, ``json`` …). Auth headers are merged in. Raises a typed
        :class:`~dicto.services.api.errors.APIError` on failure.
        """
        headers = {**self.auth_headers(), **kwargs.pop("headers", {})}
        last: errors.APIError | None = None

        for attempt in range(self.max_retries):
            try:
                response = self._client.request(method, url, headers=headers, **kwargs)
            except httpx.TimeoutException as exc:
                last = errors.NetworkError(f"request timed out: {exc}")
            except httpx.RequestError as exc:
                last = errors.NetworkError(f"network error: {exc}")
            else:
                if response.status_code < 400:
                    return response
                last = self._error_for(response)

            if last is not None and not last.retryable:
                raise last
            if attempt < self.max_retries - 1:
                delay = self.backoff * (2**attempt)
                logger.warning(
                    "%s, retrying in %.0fs (attempt %d/%d)",
                    last.code if last else "error",
                    delay,
                    attempt + 1,
                    self.max_retries,
                )
                self._sleep(delay)

        raise last or errors.APIError("request failed after retries")

    @staticmethod
    def _error_for(response: httpx.Response) -> errors.APIError:
        status = response.status_code
        message = ApiClient._parse_error_message(response)
        if status == 401:
            return errors.AuthError(message or "invalid or missing API key")
        if status == 402:
            return errors.QuotaExceededError(message or "quota exceeded")
        if status == 413:
            return errors.AudioTooLongError(message or "audio too large")
        if status == 429:
            return errors.RateLimitError(message or "rate limit reached")
        if status >= 500:
            return errors.ServerError(f"server error {status}: {message}")
        return errors.APIError(f"API error {status}: {message}", code="api", retryable=False)

    @staticmethod
    def _parse_error_message(response: httpx.Response) -> str:
        try:
            body = response.json()
            msg = body.get("error", {}).get("message") if isinstance(body, dict) else None
            if msg:
                return str(msg)
        except Exception:  # noqa: BLE001
            pass
        return response.text[:200]

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> ApiClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
