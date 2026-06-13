"""Unit tests for the Phase 5 transform layer (pure schema + service cache)."""

from __future__ import annotations

import itertools

import pytest

from dicto.config.settings import Settings
from dicto.services.api import errors
from dicto.services.api import transform as transform_api
from dicto.services.api.mocks import MockStore
from dicto.services.api.transform import TransformService
from dicto.transform import presets
from dicto.transform.schema import build_request


def _store() -> MockStore:
    counter = itertools.count(1)
    return MockStore(clock=lambda: f"2026-05-01T00:00:{next(counter):02d}Z")


# ── schema (pure) ───────────────────────────────────────────────────────────


def test_build_request_uses_preset_instructions_and_model():
    req = build_request(presets.SUMMARY, "hola mundo", model="m1")
    assert req.text == "hola mundo"
    assert req.model == "m1"
    assert req.instructions == presets.SUMMARY.instructions


def test_chat_request_appends_question():
    req = build_request(presets.ASK, "notes", model="m1", question="  what?  ")
    assert "what?" in req.instructions
    assert req.instructions.startswith(presets.ASK.instructions)


def test_non_chat_request_ignores_question():
    req = build_request(presets.SUMMARY, "notes", model="m1", question="ignored")
    assert "ignored" not in req.instructions


def test_get_preset_known_and_unknown():
    assert presets.get_preset("summary") is presets.SUMMARY
    assert presets.get_preset("nope") is None


def test_tab_presets_ids_match_detail_tab_keys():
    # The detail view maps tabs 1..4 to TAB_PRESETS by id; keep them aligned.
    assert [p.id for p in presets.TAB_PRESETS] == [
        "summary", "keypoints", "flashcards", "rewrite"
    ]


# ── service cache ─────────────────────────────────────────────────────────


class _FakeClient:
    def __init__(self) -> None:
        self.calls = 0

    def transform(self, *_a, **_k):  # not used directly
        ...


def _patch_transform(monkeypatch, result="RESULT", counter=None):
    def fake(client, text, instructions, *, model):
        if counter is not None:
            counter.append(1)
        return result
    monkeypatch.setattr(transform_api, "transform_text", fake)


def test_apply_calls_endpoint_then_caches(monkeypatch):
    calls: list[int] = []
    _patch_transform(monkeypatch, result="SUMMARY TEXT", counter=calls)
    store = _store()
    svc = TransformService(client=_FakeClient(), store=store)

    out1 = svc.apply("trx_1", "body", presets.SUMMARY, Settings())
    assert out1.text == "SUMMARY TEXT"
    assert out1.preset == "summary"
    # Second call is served from cache — no second endpoint hit.
    out2 = svc.apply("trx_1", "body", presets.SUMMARY, Settings())
    assert out2.text == "SUMMARY TEXT"
    assert len(calls) == 1
    assert svc.cached("trx_1", "summary") is not None


def test_force_bypasses_cache(monkeypatch):
    calls: list[int] = []
    _patch_transform(monkeypatch, result="X", counter=calls)
    store = _store()
    svc = TransformService(client=_FakeClient(), store=store)

    svc.apply("trx_1", "body", presets.SUMMARY, Settings())
    svc.apply("trx_1", "body", presets.SUMMARY, Settings(), force=True)
    assert len(calls) == 2


def test_chat_is_never_cached(monkeypatch):
    calls: list[int] = []
    _patch_transform(monkeypatch, result="answer", counter=calls)
    store = _store()
    svc = TransformService(client=_FakeClient(), store=store)

    svc.apply("trx_1", "body", presets.ASK, Settings(), question="q1")
    svc.apply("trx_1", "body", presets.ASK, Settings(), question="q2")
    assert len(calls) == 2
    assert svc.cached("trx_1", "ask") is None


def test_unknown_preset_raises():
    svc = TransformService(client=_FakeClient(), store=_store())
    with pytest.raises(errors.APIError):
        svc.apply("trx_1", "body", "does_not_exist", Settings())


def test_missing_api_key_raises_on_cache_miss():
    # No client, no key in settings → auth error when it must call out.
    svc = TransformService(client=None, store=_store())
    settings = Settings()
    settings.transcription.api_key = ""
    with pytest.raises(errors.AuthError):
        svc.apply("trx_1", "body", presets.SUMMARY, settings)
