"""
Transcription and transformation service using the Dicto API.

API Base: https://terturionsland.dev
- POST /api/transcribe  — audio to text
- POST /api/transform   — text transformation (format conversion)
"""

import logging
import time
from pathlib import Path

import os

import httpx

logger = logging.getLogger(__name__)

BASE_URL = os.environ.get("DICTO_API_URL", "https://terturionsland.dev")


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

    def __init__(self, api_key: str, language: str = "es", model: str = "v3-turbo"):
        if not api_key:
            raise APIKeyError("Dicto API key is required")

        self.api_key = api_key
        self.language = language if language != "auto" else "es"
        self.model = model
        self.client = httpx.Client(timeout=30.0)
        self._last_transcription_id: int | None = None

    @property
    def last_transcription_id(self) -> int | None:
        return self._last_transcription_id

    # ── Transcribe ──────────────────────────────────────────

    def transcribe(self, audio_file_path: str) -> str:
        audio_path = Path(audio_file_path)

        if not audio_path.exists():
            raise TranscriptionError(f"Audio file not found: {audio_file_path}")

        file_size_mb = audio_path.stat().st_size / (1024 * 1024)
        if file_size_mb > 25:
            raise AudioTooLongError(f"Audio file too large: {file_size_mb:.1f}MB (max 25MB)")
        if file_size_mb < 0.001:
            raise AudioTooShortError("Audio file too small (likely no audio recorded)")

        last_error = None
        for attempt in range(self.MAX_RETRIES):
            try:
                return self._transcribe_request(audio_path)
            except RateLimitError as e:
                last_error = e
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_DELAY * (2 ** attempt)
                    logger.warning(f"Rate limit hit, retrying in {delay}s… (attempt {attempt + 1}/{self.MAX_RETRIES})")
                    time.sleep(delay)
            except APIKeyError:
                raise
            except TranscriptionError as e:
                last_error = e
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_DELAY * (2 ** attempt)
                    logger.warning(f"Transcription failed, retrying in {delay}s… (attempt {attempt + 1}/{self.MAX_RETRIES})")
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
                    f"{BASE_URL}/api/transcribe",
                    headers=headers,
                    files=files,
                    data=data,
                )

            if response.status_code == 200:
                result = response.json()
                text = result.get("text", "")
                if not text:
                    raise TranscriptionError("API returned empty transcription")
                self._last_transcription_id = result.get("id")
                logger.info(f"Transcription OK (id={self._last_transcription_id}, lang={result.get('language')}, duration={result.get('duration')}s)")
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

    def transform(self, text: str, instructions: str, transcription_id: int | None = None) -> str:
        """
        Transform text using the Dicto /api/transform endpoint (Dicto format).

        Args:
            text: The text to transform
            instructions: System prompt / instructions for transformation
            transcription_id: Optional transcription ID to link the result

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
            }
            if transcription_id is not None:
                payload["transcriptionId"] = transcription_id

            response = self.client.post(
                f"{BASE_URL}/api/transform",
                headers=headers,
                json=payload,
            )

            if response.status_code == 200:
                result = response.json()
                choices = result.get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", "")
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

    # ── Error handling ──────────────────────────────────────

    def _handle_error_response(self, response: httpx.Response):
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
            error_data = response.json()
            if "error" in error_data:
                err = error_data["error"]
                if isinstance(err, dict):
                    return err.get("message", str(err))
                return str(err)
            return response.text[:200]
        except Exception:
            return response.text[:200]

    def close(self):
        if self.client:
            self.client.close()

    def __del__(self):
        self.close()
