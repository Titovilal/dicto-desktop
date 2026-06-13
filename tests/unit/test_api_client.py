"""Unit tests for the API client's retry + error-normalisation logic.

A fake httpx transport returns canned responses/exceptions so we can assert the
client retries the right failures and raises the right typed errors without a
network.
"""

from __future__ import annotations

import httpx
import pytest

from dicto.services.api import errors
from dicto.services.api.client import ApiClient


def _client(handler) -> ApiClient:
    transport = httpx.MockTransport(handler)
    http = httpx.Client(transport=transport)
    return ApiClient("key", client=http, backoff=0, sleep=lambda _: None)


def test_auth_required():
    with pytest.raises(errors.AuthError):
        ApiClient("")


def test_success_returns_response():
    c = _client(lambda req: httpx.Response(200, json={"text": "ok"}))
    resp = c.request("POST", "https://x/api")
    assert resp.json()["text"] == "ok"


def test_401_raises_auth_not_retried():
    calls = []

    def handler(req):
        calls.append(req)
        return httpx.Response(401, json={"error": {"message": "bad key"}})

    c = _client(handler)
    with pytest.raises(errors.AuthError):
        c.request("POST", "https://x/api")
    assert len(calls) == 1  # not retried


def test_429_is_retried_then_raises():
    calls = []

    def handler(req):
        calls.append(req)
        return httpx.Response(429, json={"error": {"message": "slow down"}})

    c = _client(handler)
    with pytest.raises(errors.RateLimitError):
        c.request("POST", "https://x/api")
    assert len(calls) == 3  # default max_retries


def test_500_retried_then_succeeds():
    state = {"n": 0}

    def handler(req):
        state["n"] += 1
        if state["n"] < 3:
            return httpx.Response(500, text="boom")
        return httpx.Response(200, json={"text": "ok"})

    c = _client(handler)
    resp = c.request("POST", "https://x/api")
    assert resp.status_code == 200
    assert state["n"] == 3


def test_network_error_retried():
    calls = []

    def handler(req):
        calls.append(req)
        raise httpx.ConnectError("refused")

    c = _client(handler)
    with pytest.raises(errors.NetworkError):
        c.request("POST", "https://x/api")
    assert len(calls) == 3


def test_413_audio_too_long_not_retried():
    calls = []

    def handler(req):
        calls.append(req)
        return httpx.Response(413, json={"error": {"message": "too big"}})

    c = _client(handler)
    with pytest.raises(errors.AudioTooLongError):
        c.request("POST", "https://x/api")
    assert len(calls) == 1


def test_auth_header_is_sent():
    seen = {}

    def handler(req):
        seen["auth"] = req.headers.get("Authorization")
        return httpx.Response(200, json={"text": "ok"})

    c = _client(handler)
    c.request("GET", "https://x/api")
    assert seen["auth"] == "Bearer key"
