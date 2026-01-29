"""
Transcription service using Groq or OpenAI Whisper API.
"""

import httpx
import time
from pathlib import Path


class TranscriptionError(Exception):
    """Base exception for transcription errors."""

    pass


class APIKeyError(TranscriptionError):
    """API key is invalid or missing."""

    pass


class RateLimitError(TranscriptionError):
    """API rate limit exceeded."""

    pass


class AudioTooShortError(TranscriptionError):
    """Audio file is too short."""

    pass


class AudioTooLongError(TranscriptionError):
    """Audio file is too long."""

    pass


class Transcriber:
    """Handles audio transcription using Groq or OpenAI Whisper API."""

    PROVIDERS = {
        "groq": {
            "url": "https://api.groq.com/openai/v1/audio/transcriptions",
            "model": "whisper-large-v3-turbo",
        },
        "openai": {
            "url": "https://api.openai.com/v1/audio/transcriptions",
            "model": "whisper-1",
        },
    }
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds

    def __init__(self, api_key: str, language: str = "auto", provider: str = "groq"):
        """
        Initialize transcriber.

        Args:
            api_key: API key for the transcription provider
            language: Language code (e.g., 'en', 'es') or 'auto' for automatic detection
            provider: Transcription provider ('groq' or 'openai')
        """
        if not api_key:
            raise APIKeyError(f"{provider.upper()} API key is required")

        if provider not in self.PROVIDERS:
            raise TranscriptionError(f"Unknown provider: {provider}. Use 'groq' or 'openai'")

        self.api_key = api_key
        self.language = None if language == "auto" else language
        self.provider = provider
        self.api_url = self.PROVIDERS[provider]["url"]
        self.model = self.PROVIDERS[provider]["model"]
        self.client = httpx.Client(timeout=30.0)

    def transcribe(self, audio_file_path: str) -> str:
        """
        Transcribe audio file to text.

        Args:
            audio_file_path: Path to audio file (WAV format)

        Returns:
            Transcribed text

        Raises:
            TranscriptionError: If transcription fails
        """
        audio_path = Path(audio_file_path)

        if not audio_path.exists():
            raise TranscriptionError(f"Audio file not found: {audio_file_path}")

        # Check file size
        file_size_mb = audio_path.stat().st_size / (1024 * 1024)
        if file_size_mb > 25:
            raise AudioTooLongError(
                f"Audio file too large: {file_size_mb:.1f}MB (max 25MB)"
            )

        if file_size_mb < 0.001:
            raise AudioTooShortError("Audio file too small (likely no audio recorded)")

        # Attempt transcription with retries
        last_error = None
        for attempt in range(self.MAX_RETRIES):
            try:
                text = self._transcribe_request(audio_path)
                return text.strip()

            except RateLimitError as e:
                last_error = e
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_DELAY * (2**attempt)  # Exponential backoff
                    print(
                        f"Rate limit hit, retrying in {delay}s... (attempt {attempt + 1}/{self.MAX_RETRIES})"
                    )
                    time.sleep(delay)
                continue

            except APIKeyError:
                # Don't retry on auth errors
                raise

            except TranscriptionError as e:
                last_error = e
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_DELAY * (2**attempt)
                    print(
                        f"Transcription failed, retrying in {delay}s... (attempt {attempt + 1}/{self.MAX_RETRIES})"
                    )
                    time.sleep(delay)
                continue

        # All retries failed
        raise last_error or TranscriptionError("Transcription failed after all retries")

    def _transcribe_request(self, audio_path: Path) -> str:
        """
        Make a single transcription API request.

        Args:
            audio_path: Path to audio file

        Returns:
            Transcribed text

        Raises:
            TranscriptionError: If request fails
        """
        try:
            # Prepare request
            headers = {"Authorization": f"Bearer {self.api_key}"}

            # Prepare form data
            files = {"file": (audio_path.name, open(audio_path, "rb"), "audio/wav")}

            data = {"model": self.model}

            # Add language if specified
            if self.language:
                data["language"] = self.language

            # Make request
            response = self.client.post(
                self.api_url, headers=headers, files=files, data=data
            )

            # Close file
            files["file"][1].close()

            # Handle response
            if response.status_code == 200:
                result = response.json()
                text = result.get("text", "")
                if not text:
                    raise TranscriptionError("API returned empty transcription")
                return text

            elif response.status_code == 401:
                raise APIKeyError("Invalid API key")

            elif response.status_code == 429:
                raise RateLimitError("API rate limit exceeded")

            else:
                error_msg = self._parse_error_message(response)
                raise TranscriptionError(
                    f"API error ({response.status_code}): {error_msg}"
                )

        except httpx.TimeoutException:
            raise TranscriptionError("Request timeout - API took too long to respond")

        except httpx.RequestError as e:
            raise TranscriptionError(f"Network error: {e}")

        except Exception as e:
            if isinstance(e, TranscriptionError):
                raise
            raise TranscriptionError(f"Unexpected error: {e}")

    def _parse_error_message(self, response: httpx.Response) -> str:
        """Extract error message from API response."""
        try:
            error_data = response.json()
            if "error" in error_data:
                if isinstance(error_data["error"], dict):
                    return error_data["error"].get("message", str(error_data["error"]))
                return str(error_data["error"])
            return response.text[:200]  # First 200 chars
        except:
            return response.text[:200]

    def close(self):
        """Close HTTP client."""
        if self.client:
            self.client.close()

    def __del__(self):
        """Destructor to ensure cleanup."""
        self.close()
