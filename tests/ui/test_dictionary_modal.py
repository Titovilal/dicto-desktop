"""UI tests for the dictionary modal (add / list / delete terms)."""

from __future__ import annotations

import pytest

from dicto.core.models import DictTermKind
from dicto.services.api.dictionary import DictionaryService
from dicto.services.api.mocks import MockStore

pytest.importorskip("PySide6.QtWidgets")

from dicto.ui.main.dictionary_modal import DictionaryModal  # noqa: E402
from dicto.ui.theme.manager import ThemeManager  # noqa: E402


def _service() -> DictionaryService:
    return DictionaryService(MockStore(clock=lambda: "2026-01-01T00:00:00Z"))


def _modal(qtbot, service: DictionaryService) -> DictionaryModal:
    modal = DictionaryModal(service, ThemeManager(None, theme="dark"))
    qtbot.addWidget(modal)
    return modal


def _row_count(modal: DictionaryModal) -> int:
    return modal._rows_layout.count() - 1  # minus the trailing stretch


def test_lists_existing_terms(qtbot):
    svc = _service()
    svc.create("ILATE", kind=DictTermKind.ACRONYM)
    svc.create("García Lorca", kind=DictTermKind.NAME)

    modal = _modal(qtbot, svc)
    assert _row_count(modal) == 2
    assert not modal._empty.isVisibleTo(modal)


def test_add_term_via_input(qtbot):
    svc = _service()
    modal = _modal(qtbot, svc)
    assert _row_count(modal) == 0

    modal._input.setText("  anamnesis  ")
    modal._add_btn.click()

    terms = svc.list()
    assert [t.text for t in terms] == ["anamnesis"]
    assert _row_count(modal) == 1
    assert modal._input.text() == ""


def test_add_empty_is_ignored(qtbot):
    svc = _service()
    modal = _modal(qtbot, svc)
    modal._input.setText("   ")
    modal._add_btn.click()
    assert svc.list() == []
    assert _row_count(modal) == 0


def test_delete_term(qtbot):
    svc = _service()
    term = svc.create("WASAPI", kind=DictTermKind.ACRONYM)
    modal = _modal(qtbot, svc)
    assert _row_count(modal) == 1

    modal._on_delete(term.id)
    assert svc.list() == []
    assert _row_count(modal) == 0
    assert modal._empty.isVisibleTo(modal)
