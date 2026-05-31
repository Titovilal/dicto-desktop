"""
Transcription and transformation service using the Dicto API.

All endpoint URLs come from `src.services.routes` (see that module for the
base URL and paths). This service wraps transcribe, transform and presets.
"""

from __future__ import annotations

import logging
from typing import NoReturn
import time
from pathlib import Path

import httpx

from src.services import routes

logger = logging.getLogger(__name__)


class TranscriptionError(Exception):
    """Base exception for transcription errors."""

    pass


class APIKeyError(TranscriptionError):
    """API key is invalid or missing."""

    pass


class RateLimitError(TranscriptionError):
    """API rate limit / spending limit exceeded."""

    pass


class AudioTooShortError(TranscriptionError):
    """Audio file is too short."""

    pass


class AudioTooLongError(TranscriptionError):
    """Audio file is too long."""

    pass


class Transcriber:
    """Handles audio transcription and text transformation via the Dicto API."""

    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds

    def __init__(
        self,
        api_key: str,
        language: str = "es",
        model: str = "v3-turbo",
        transformation_model: str = "qwen/qwen3-32b",
    ):
        if not api_key:
            raise APIKeyError("Dicto API key is required")

        self.api_key = api_key
        self.language = language
        self.model = model
        self.transformation_model = transformation_model
        self.client = httpx.Client(timeout=30.0)

    # ── Transcribe ──────────────────────────────────────────

    def transcribe(self, audio_file_path: str) -> str:
        audio_path = Path(audio_file_path)

        if not audio_path.exists():
            raise TranscriptionError(f"Audio file not found: {audio_file_path}")

        file_size_mb = audio_path.stat().st_size / (1024 * 1024)
        if file_size_mb > 25:
            raise AudioTooLongError(
                f"Audio file too large: {file_size_mb:.1f}MB (max 25MB)"
            )
        if file_size_mb < 0.001:
            raise AudioTooShortError("Audio file too small (likely no audio recorded)")

        last_error = None
        for attempt in range(self.MAX_RETRIES):
            try:
                return self._transcribe_request(audio_path)
            except RateLimitError as e:
                last_error = e
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_DELAY * (2**attempt)
                    logger.warning(
                        f"Rate limit hit, retrying in {delay}s… (attempt {attempt + 1}/{self.MAX_RETRIES})"
                    )
                    time.sleep(delay)
            except APIKeyError:
                raise
            except TranscriptionError as e:
                last_error = e
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_DELAY * (2**attempt)
                    logger.warning(
                        f"Transcription failed, retrying in {delay}s… (attempt {attempt + 1}/{self.MAX_RETRIES})"
                    )
                    time.sleep(delay)

        raise last_error or TranscriptionError("Transcription failed after all retries")

    def _transcribe_request(self, audio_path: Path) -> str:
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}

            # Guess MIME type from extension
            suffix = audio_path.suffix.lower()
            mime_types = {
                ".wav": "audio/wav",
                ".mp3": "audio/mpeg",
                ".webm": "audio/webm",
                ".m4a": "audio/m4a",
                ".ogg": "audio/ogg",
            }
            mime = mime_types.get(suffix, "audio/wav")

            data = {"source": "mic_app", "model": self.model}
            if self.language:
                data["language"] = self.language

            with open(audio_path, "rb") as audio_file:
                files = {"file": (audio_path.name, audio_file, mime)}
                response = self.client.post(
                    routes.transcribe(),
                    headers=headers,
                    files=files,
                    data=data,
                )

            if response.status_code == 200:
                result = response.json()
                text = result.get("text", "")
                if not text:
                    raise TranscriptionError("API returned empty transcription")
                logger.info("Transcription OK")
                return text.strip()

            self._handle_error_response(response)

        except httpx.TimeoutException:
            raise TranscriptionError("Request timeout — API took too long to respond")
        except httpx.RequestError as e:
            raise TranscriptionError(f"Network error: {e}")
        except TranscriptionError:
            raise
        except Exception as e:
            raise TranscriptionError(f"Unexpected error: {e}")

    # ── Transform ───────────────────────────────────────────

    def transform(self, text: str, instructions: str) -> str:
        """
        Transform text using the Dicto /api/v1/transform endpoint (Dicto format).

        Args:
            text: The text to transform
            instructions: System prompt / instructions for transformation

        Returns:
            Transformed text
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            payload: dict = {
                "text": text,
                "instructions": instructions,
                "model": self.transformation_model,
            }

            response = self.client.post(
                routes.transform(),
                headers=headers,
                json=payload,
            )

            if response.status_code == 200:
                result = response.json()
                content = result.get("text", "")
                if content:
                    return content.strip()
                raise TranscriptionError("Transform API returned empty result")

            self._handle_error_response(response)

        except httpx.TimeoutException:
            raise TranscriptionError("Transform request timeout")
        except httpx.RequestError as e:
            raise TranscriptionError(f"Network error: {e}")
        except TranscriptionError:
            raise
        except Exception as e:
            raise TranscriptionError(f"Unexpected error during transform: {e}")

    # ── Presets ─────────────────────────────────────────────

    def get_favorite_presets(self) -> list[dict]:
        """Fetch the user's favorite presets from the API.

        Returns:
            List of dicts with keys: name, instructions
        """
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = self.client.get(
                routes.presets(),
                headers=headers,
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("presets", [])

            logger.warning(f"Failed to fetch presets: {response.status_code}")
            return []
        except Exception as e:
            logger.warning(f"Error fetching presets: {e}")
            return []

    # ── Error handling ──────────────────────────────────────

    def _handle_error_response(self, response: httpx.Response) -> NoReturn:
        """Parse error response and raise appropriate exception."""
        if response.status_code == 401:
            raise APIKeyError("Invalid or missing API key")
        elif response.status_code == 429:
            raise RateLimitError("Spending limit reached")
        else:
            msg = self._parse_error_message(response)
            raise TranscriptionError(f"API error ({response.status_code}): {msg}")

    @staticmethod
    def _parse_error_message(response: httpx.Response) -> str:
        try:
            # Normalized error shape: { "error": { "message": "…" } }
            message = response.json().get("error", {}).get("message")
            if message:
                return message
        except Exception:
            pass
        # Fallback for non-JSON / unexpected bodies (e.g. proxy/gateway errors)
        return response.text[:200]

    def close(self):
        if getattr(self, "client", None):
            self.client.close()

    def __del__(self):
        self.close()
