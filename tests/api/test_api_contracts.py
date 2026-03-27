"""API contract tests — verify request format and response parsing without hitting the real API."""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest

from src.services.transcriber import Transcriber, BASE_URL


@pytest.fixture
def transcriber():
    return Transcriber(
        api_key="sk-dicto-test",
        language="es",
        model="v3-turbo",
        transformation_model="qwen/qwen3-32b",
        edition_model="qwen/qwen3-32b",
    )


class TestTranscribeContract:
    """Verify the request sent to POST /api/transcribe."""

    def test_request_format(self, transcriber, sample_audio_file):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"text": "hello", "id": 1}

        with patch.object(
            transcriber.client, "post", return_value=mock_response
        ) as mock_post:
            transcriber.transcribe(sample_audio_file)

        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args

        # URL
        assert call_kwargs.args[0] == f"{BASE_URL}/api/transcribe"

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
        mock_response.json.return_value = {"text": "hello", "id": 1}

        with patch.object(
            transcriber.client, "post", return_value=mock_response
        ) as mock_post:
            transcriber.transcribe(sample_audio_file)

        files = mock_post.call_args.kwargs["files"]
        assert files["file"][2] == "audio/wav"


class TestTransformContract:
    """Verify the request sent to POST /api/transform."""

    def test_request_format(self, transcriber):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"message": {"content": "ok"}}]}

        with patch.object(
            transcriber.client, "post", return_value=mock_response
        ) as mock_post:
            transcriber.transform("some text", "format as email", transcription_id=42)

        call_kwargs = mock_post.call_args

        # URL
        assert call_kwargs.args[0] == f"{BASE_URL}/api/transform"

        # Headers
        assert call_kwargs.kwargs["headers"]["Authorization"] == "Bearer sk-dicto-test"
        assert call_kwargs.kwargs["headers"]["Content-Type"] == "application/json"

        # JSON body
        payload = call_kwargs.kwargs["json"]
        assert payload["text"] == "some text"
        assert payload["instructions"] == "format as email"
        assert payload["model"] == "qwen/qwen3-32b"
        assert payload["transcriptionId"] == 42

    def test_no_transcription_id(self, transcriber):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"message": {"content": "ok"}}]}

        with patch.object(
            transcriber.client, "post", return_value=mock_response
        ) as mock_post:
            transcriber.transform("text", "instructions")

        payload = mock_post.call_args.kwargs["json"]
        assert "transcriptionId" not in payload


class TestEditContract:
    """Verify the request sent to POST /api/edit."""

    def test_request_format(self, transcriber, sample_audio_file):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "edited"}}]
        }

        with patch.object(
            transcriber.client, "post", return_value=mock_response
        ) as mock_post:
            transcriber.edit("selected text", sample_audio_file)

        call_kwargs = mock_post.call_args

        # URL
        assert call_kwargs.args[0] == f"{BASE_URL}/api/edit"

        # Auth
        assert call_kwargs.kwargs["headers"]["Authorization"] == "Bearer sk-dicto-test"

        # Data fields
        data = call_kwargs.kwargs["data"]
        assert data["text"] == "selected text"
        assert data["source"] == "mic_app"
        assert data["edition_model"] == "qwen/qwen3-32b"

        # Audio file
        files = call_kwargs.kwargs["files"]
        assert "audio" in files


class TestResponseParsing:
    """Verify response formats are parsed correctly."""

    def test_transcribe_response(self, transcriber, sample_audio_file):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "text": "  hello world  ",
            "id": 123,
            "language": "es",
            "duration": 2.5,
        }

        with patch.object(transcriber.client, "post", return_value=mock_response):
            result = transcriber.transcribe(sample_audio_file)

        assert result == "hello world"  # stripped
        assert transcriber.last_transcription_id == 123

    def test_transform_response(self, transcriber):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "  formatted  "}}]
        }

        with patch.object(transcriber.client, "post", return_value=mock_response):
            result = transcriber.transform("text", "format")

        assert result == "formatted"  # stripped

    def test_edit_response(self, transcriber, sample_audio_file):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "  edited  "}}]
        }

        with patch.object(transcriber.client, "post", return_value=mock_response):
            result = transcriber.edit("text", sample_audio_file)

        assert result == "edited"
