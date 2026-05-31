"""API contract tests — verify request format and response parsing without hitting the real API."""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest

from src.services import routes
from src.services.transcriber import Transcriber


@pytest.fixture
def transcriber():
    return Transcriber(
        api_key="sk-dicto-test",
        language="es",
        model="v3-turbo",
        transformation_model="qwen/qwen3-32b",
    )


class TestTranscribeContract:
    """Verify the request sent to POST /api/v1/transcribe."""

    def test_request_format(self, transcriber, sample_audio_file):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"text": "hello"}

        with patch.object(
            transcriber.client, "post", return_value=mock_response
        ) as mock_post:
            transcriber.transcribe(sample_audio_file)

        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args

        # URL
        assert call_kwargs.args[0] == routes.transcribe()

        # Auth header
        assert call_kwargs.kwargs["headers"]["Authorization"] == "Bearer sk-dicto-test"

        # Data fields
        data = call_kwargs.kwargs["data"]
        assert data["source"] == "mic_app"
        assert data["model"] == "v3-turbo"
        assert data["language"] == "es"

        # File field
        files = call_kwargs.kwargs["files"]
        assert "file" in files
        filename, file_obj, mime = files["file"]
        assert filename == "test.wav"
        assert mime == "audio/wav"

    def test_wav_mime_type(self, transcriber, sample_audio_file):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"text": "hello"}

        with patch.object(
            transcriber.client, "post", return_value=mock_response
        ) as mock_post:
            transcriber.transcribe(sample_audio_file)

        files = mock_post.call_args.kwargs["files"]
        assert files["file"][2] == "audio/wav"


class TestTransformContract:
    """Verify the request sent to POST /api/v1/transform."""

    def test_request_format(self, transcriber):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"text": "ok"}

        with patch.object(
            transcriber.client, "post", return_value=mock_response
        ) as mock_post:
            transcriber.transform("some text", "format as email")

        call_kwargs = mock_post.call_args

        # URL
        assert call_kwargs.args[0] == routes.transform()

        # Headers
        assert call_kwargs.kwargs["headers"]["Authorization"] == "Bearer sk-dicto-test"
        assert call_kwargs.kwargs["headers"]["Content-Type"] == "application/json"

        # JSON body
        payload = call_kwargs.kwargs["json"]
        assert payload["model"] == "qwen/qwen3-32b"
        assert payload["text"] == "some text"
        assert payload["instructions"] == "format as email"


class TestResponseParsing:
    """Verify response formats are parsed correctly."""

    def test_transcribe_response(self, transcriber, sample_audio_file):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"text": "  hello world  "}

        with patch.object(transcriber.client, "post", return_value=mock_response):
            result = transcriber.transcribe(sample_audio_file)

        assert result == "hello world"  # stripped

    def test_transform_response(self, transcriber):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"text": "  formatted  "}

        with patch.object(transcriber.client, "post", return_value=mock_response):
            result = transcriber.transform("text", "format")

        assert result == "formatted"  # stripped
