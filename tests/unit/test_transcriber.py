"""Unit tests for Transcriber API client."""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

import httpx

from src.services.transcriber import (
    Transcriber,
    TranscriptionError,
    APIKeyError,
    RateLimitError,
    AudioTooShortError,
    AudioTooLongError,
)


@pytest.fixture
def transcriber():
    return Transcriber(api_key="sk-dicto-test", language="es", model="v3-turbo")


class TestInit:
    def test_requires_api_key(self):
        with pytest.raises(APIKeyError):
            Transcriber(api_key="")

    def test_auto_language_kept_as_is(self):
        t = Transcriber(api_key="sk-dicto-test", language="auto")
        assert t.language == "auto"

    def test_stores_models(self):
        t = Transcriber(
            api_key="sk-dicto-test",
            transformation_model="gpt-4",
        )
        assert t.transformation_model == "gpt-4"


class TestTranscribeValidation:
    def test_file_not_found(self, transcriber):
        with pytest.raises(TranscriptionError, match="not found"):
            transcriber.transcribe("/nonexistent/file.wav")

    def test_file_too_large(self, transcriber, tmp_path):
        big_file = tmp_path / "big.wav"
        big_file.write_bytes(b"\x00" * (26 * 1024 * 1024))
        with pytest.raises(AudioTooLongError):
            transcriber.transcribe(str(big_file))

    def test_file_too_small(self, transcriber, tmp_path):
        tiny_file = tmp_path / "tiny.wav"
        tiny_file.write_bytes(b"\x00")
        with pytest.raises(AudioTooShortError):
            transcriber.transcribe(str(tiny_file))


class TestTranscribeRequest:
    def test_success_returns_text(self, transcriber, sample_audio_file):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"text": "  hello world  "}

        with patch.object(transcriber.client, "post", return_value=mock_response):
            result = transcriber.transcribe(sample_audio_file)

        assert result == "hello world"

    def test_empty_text_raises(self, transcriber, sample_audio_file):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"text": ""}

        with patch.object(transcriber.client, "post", return_value=mock_response):
            with pytest.raises(TranscriptionError, match="empty"):
                transcriber.transcribe(sample_audio_file)

    def test_401_raises_api_key_error(self, transcriber, sample_audio_file):
        mock_response = MagicMock()
        mock_response.status_code = 401

        with patch.object(transcriber.client, "post", return_value=mock_response):
            with pytest.raises(APIKeyError):
                transcriber.transcribe(sample_audio_file)

    def test_429_retries_then_raises(self, transcriber, sample_audio_file):
        mock_response = MagicMock()
        mock_response.status_code = 429

        with (
            patch.object(transcriber.client, "post", return_value=mock_response),
            patch("src.services.transcriber.time.sleep"),
        ):
            with pytest.raises(RateLimitError):
                transcriber.transcribe(sample_audio_file)

    def test_500_retries_then_raises(self, transcriber, sample_audio_file):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": {"message": "internal"}}
        mock_response.text = "internal server error"

        with (
            patch.object(transcriber.client, "post", return_value=mock_response),
            patch("src.services.transcriber.time.sleep"),
        ):
            with pytest.raises(TranscriptionError, match="500"):
                transcriber.transcribe(sample_audio_file)

    def test_timeout_raises(self, transcriber, sample_audio_file):
        with (
            patch.object(
                transcriber.client,
                "post",
                side_effect=httpx.TimeoutException("timeout"),
            ),
            patch("src.services.transcriber.time.sleep"),
        ):
            with pytest.raises(TranscriptionError, match="timeout"):
                transcriber.transcribe(sample_audio_file)

    def test_network_error_raises(self, transcriber, sample_audio_file):
        with (
            patch.object(
                transcriber.client, "post", side_effect=httpx.ConnectError("no network")
            ),
            patch("src.services.transcriber.time.sleep"),
        ):
            with pytest.raises(TranscriptionError, match="Network"):
                transcriber.transcribe(sample_audio_file)


class TestTransform:
    def test_success(self, transcriber):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"text": "  formatted text  "}

        with patch.object(transcriber.client, "post", return_value=mock_response):
            result = transcriber.transform("raw text", "format as email")

        assert result == "formatted text"

    def test_empty_text_raises(self, transcriber):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"text": ""}

        with patch.object(transcriber.client, "post", return_value=mock_response):
            with pytest.raises(TranscriptionError, match="empty"):
                transcriber.transform("raw text", "format")

    def test_sends_text_and_instructions(self, transcriber):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"text": "ok"}

        with patch.object(
            transcriber.client, "post", return_value=mock_response
        ) as mock_post:
            transcriber.transform("text", "instructions")

        payload = mock_post.call_args.kwargs["json"]
        assert payload["text"] == "text"
        assert payload["instructions"] == "instructions"


class TestGetModels:
    def test_success_returns_lists(self, transcriber):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "transcription": [{"id": "v3-turbo", "name": "Whisper V3 Turbo", "default": True}],
            "transformation": [{"id": "qwen/qwen3-32b", "name": "Qwen3 32B", "default": True}],
        }

        with patch.object(transcriber.client, "get", return_value=mock_response):
            result = transcriber.get_models()

        assert result["transcription"][0]["id"] == "v3-turbo"
        assert result["transformation"][0]["id"] == "qwen/qwen3-32b"

    def test_missing_keys_default_to_empty(self, transcriber):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}

        with patch.object(transcriber.client, "get", return_value=mock_response):
            result = transcriber.get_models()

        assert result == {"transcription": [], "transformation": []}

    def test_non_200_returns_empty_dict(self, transcriber):
        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch.object(transcriber.client, "get", return_value=mock_response):
            assert transcriber.get_models() == {}

    def test_exception_returns_empty_dict(self, transcriber):
        with patch.object(
            transcriber.client, "get", side_effect=httpx.RequestError("boom")
        ):
            assert transcriber.get_models() == {}


class TestErrorParsing:
    def test_parse_error_dict(self, transcriber, sample_audio_file):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": {"message": "bad request"}}
        mock_response.text = ""

        with (
            patch.object(transcriber.client, "post", return_value=mock_response),
            patch("src.services.transcriber.time.sleep"),
        ):
            with pytest.raises(TranscriptionError, match="bad request"):
                transcriber.transcribe(sample_audio_file)

    def test_parse_error_falls_back_to_body(self, transcriber, sample_audio_file):
        # Non-JSON / unexpected body (e.g. proxy or gateway error)
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.side_effect = ValueError("not json")
        mock_response.text = "something went wrong"

        with (
            patch.object(transcriber.client, "post", return_value=mock_response),
            patch("src.services.transcriber.time.sleep"),
        ):
            with pytest.raises(TranscriptionError, match="something went wrong"):
                transcriber.transcribe(sample_audio_file)
