"""Unit tests for the dictionary: bias prompt (pure) + the mocked service."""

from __future__ import annotations

import pytest

from dicto.core.dictionary import build_bias_prompt
from dicto.core.models import DictTerm, DictTermKind
from dicto.services.api.dictionary import DictionaryService
from dicto.services.api.mocks import MockStore


def _term(text: str) -> DictTerm:
    return DictTerm(id=f"t-{text}", text=text)


# ── pure: build_bias_prompt ───────────────────────────────────────────────


def test_empty_dictionary_yields_none():
    assert build_bias_prompt([]) is None


def test_prompt_joins_terms():
    prompt = build_bias_prompt([_term("mitocondria"), _term("AEMET")])
    assert prompt == "mitocondria, AEMET"


def test_dedupe_is_case_insensitive_first_wins():
    prompt = build_bias_prompt([_term("AEMET"), _term("aemet"), _term("Aemet")])
    assert prompt == "AEMET"


def test_blank_terms_are_skipped():
    assert build_bias_prompt([_term("   "), _term("")]) is None
    assert build_bias_prompt([_term("  x  ")]) == "x"


def test_max_terms_cap():
    terms = [_term(f"w{i}") for i in range(10)]
    assert build_bias_prompt(terms, max_terms=3) == "w0, w1, w2"


def test_max_chars_drops_whole_terms():
    terms = [_term("alpha"), _term("beta"), _term("gamma")]
    prompt = build_bias_prompt(terms, max_chars=11)  # "alpha, beta" == 11
    assert prompt == "alpha, beta"


# ── service (mocked store) ────────────────────────────────────────────────


def test_service_create_list_delete():
    svc = DictionaryService(MockStore())
    a = svc.create("mitocondria")
    svc.create("AEMET", kind=DictTermKind.ACRONYM)
    terms = svc.list()
    assert {t.text for t in terms} == {"mitocondria", "AEMET"}
    assert svc.delete(a.id) is True
    assert [t.text for t in svc.list()] == ["AEMET"]


def test_service_rejects_empty_term():
    svc = DictionaryService(MockStore())
    with pytest.raises(ValueError):
        svc.create("   ")
