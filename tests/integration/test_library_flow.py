"""Integration test for the Phase 4 library + dictionary flow.

Exercises the composition the app performs without Qt:

1. A finished transcript is cleaned then auto-saved to the library, and shows up
   in a search — dictation is never lost.
2. The user's dictionary becomes a biasing prompt that the transcribe factory
   forwards to the (faked) transcribe call, so jargon is biased.
"""

from __future__ import annotations

import wave

from dicto.config.settings import Settings
from dicto.core.cleanup import clean_dictation
from dicto.core.dictionary import build_bias_prompt
from dicto.services.api import transcribe as transcribe_api
from dicto.services.api.dictionary import DictionaryService
from dicto.services.api.factory import make_transcribe_chunk
from dicto.services.api.library import LibraryQuery, LibraryService
from dicto.services.api.mocks import MockStore

SR = 16000


def _make_store():
    import itertools

    counter = itertools.count(1)
    return MockStore(clock=lambda: f"2026-06-06T00:00:{next(counter):02d}Z")


def test_transcript_is_cleaned_saved_and_searchable():
    store = _make_store()
    library = LibraryService(store)

    raw = "eh bueno la mitocondria es la central energetica"
    cleaned = clean_dictation(raw, lang="es")
    library.create(text=cleaned, language="es")

    # Appears in the library and is findable by a word in the body.
    assert len(library.list()) == 1
    found = library.list(LibraryQuery(text="mitocondria"))
    assert len(found) == 1
    assert "mitocondria" in found[0].text.lower()


def test_dictionary_biases_the_transcribe_call(tmp_path, monkeypatch):
    store = _make_store()
    dictionary = DictionaryService(store)
    dictionary.create("mitocondria")
    dictionary.create("AEMET")

    prompt = build_bias_prompt(dictionary.list())
    assert prompt == "mitocondria, AEMET"

    # A real (tiny) WAV chunk on disk.
    chunk = tmp_path / "chunk.wav"
    with wave.open(str(chunk), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(b"\x00\x01" * SR)  # 1s of audio

    seen: dict[str, object] = {}

    def fake_transcribe_file(client, audio_path, *, model, language, prompt=None):
        seen["prompt"] = prompt
        seen["language"] = language
        return "mitocondria"

    # factory calls ``transcribe_api.transcribe_file`` via the module, so
    # patching the attribute there intercepts it (auto-restored by monkeypatch).
    monkeypatch.setattr(transcribe_api, "transcribe_file", fake_transcribe_file)

    settings = Settings()
    settings.audio.channels = 1
    fn = make_transcribe_chunk(client=None, settings=settings, apply_vad=False, prompt=prompt)
    text = fn(str(chunk))

    assert text == "mitocondria"
    assert seen["prompt"] == "mitocondria, AEMET"
