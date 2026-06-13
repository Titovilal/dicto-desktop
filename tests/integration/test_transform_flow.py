"""Integration test for the Phase 5 transform flow (no Qt, no real network).

Exercises the composition the detail/chat views drive:

1. A saved transcript → a preset transform calls the endpoint once and the
   result is cached, so reopening the tab is instant (a second call is free).
2. The chat preset answers a question grounded in the transcript and is not
   cached (the answer depends on the question).
"""

from __future__ import annotations

import itertools

from dicto.config.settings import Settings
from dicto.services.api import transform as transform_api
from dicto.services.api.library import LibraryService
from dicto.services.api.mocks import MockStore
from dicto.services.api.transform import TransformService
from dicto.transform import presets


def _store() -> MockStore:
    counter = itertools.count(1)
    return MockStore(clock=lambda: f"2026-06-13T00:00:{next(counter):02d}Z")


class _Client:  # stands in for an authed ApiClient; never touched by the fake
    pass


def test_preset_transform_is_cached_across_reopens(monkeypatch):
    store = _store()
    library = LibraryService(store)
    transcript = library.create(text="la fotosintesis convierte luz en energia", language="es")

    seen: list[str] = []

    def fake(client, text, instructions, *, model):
        seen.append(instructions)
        return "Resumen: la fotosíntesis transforma luz en energía."

    monkeypatch.setattr(transform_api, "transform_text", fake)

    svc = TransformService(client=_Client(), store=store)
    settings = Settings()

    first = svc.apply(transcript.id, transcript.text, presets.SUMMARY, settings)
    assert "fotosíntesis" in first.text
    # Reopen the tab → served from the cache, no second endpoint call.
    again = svc.apply(transcript.id, transcript.text, presets.SUMMARY, settings)
    assert again.text == first.text
    assert len(seen) == 1
    assert svc.cached(transcript.id, "summary") is not None


def test_chat_answers_with_transcript_context(monkeypatch):
    store = _store()
    library = LibraryService(store)
    transcript = library.create(text="la mitocondria produce ATP", language="es")

    captured: dict[str, str] = {}

    def fake(client, text, instructions, *, model):
        captured["text"] = text
        captured["instructions"] = instructions
        return "Produce ATP."

    monkeypatch.setattr(transform_api, "transform_text", fake)

    svc = TransformService(client=_Client(), store=store)
    answer = svc.apply(
        transcript.id, transcript.text, presets.ASK, Settings(),
        question="¿Qué produce la mitocondria?",
    )
    assert answer.text == "Produce ATP."
    # The transcript is the context; the question is folded into the prompt.
    assert captured["text"] == transcript.text
    assert "¿Qué produce la mitocondria?" in captured["instructions"]
    # Chat answers are never cached.
    assert svc.cached(transcript.id, "ask") is None
