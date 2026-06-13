"""UI tests for the library + detail views.

Need a QApplication; they use pytest-qt's ``qtbot`` and skip gracefully where Qt
has no platform plugin. The library is backed by a fresh mock store so each test
is isolated.
"""

from __future__ import annotations

import itertools

import pytest

from dicto.services.api.library import LibraryService
from dicto.services.api.mocks import MockStore

pytest.importorskip("PySide6.QtWidgets")

from dicto.ui.main.detail_view import DetailView  # noqa: E402
from dicto.ui.main.library_view import LibraryView  # noqa: E402
from dicto.ui.main.window import MainWindow  # noqa: E402


def _library() -> LibraryService:
    counter = itertools.count(1)
    return LibraryService(MockStore(clock=lambda: f"2026-01-01T00:00:{next(counter):02d}Z"))


def test_library_view_lists_and_filters(qtbot):
    lib = _library()
    lib.create("the mitochondria", language="en", tags=["bio"])
    lib.create("calculus notes", language="en", tags=["math"])

    view = LibraryView(lib)
    qtbot.addWidget(view)
    view.refresh()
    assert view._list.count() == 2

    # Search narrows the list.
    view._search.setText("calculus")
    assert view._list.count() == 1
    assert "calculus" in view._list.item(0).text()


def test_library_view_emits_selection(qtbot):
    lib = _library()
    created = lib.create("hello", language="en")
    view = LibraryView(lib)
    qtbot.addWidget(view)

    with qtbot.waitSignal(view.transcriptSelected) as blocker:
        view.refresh()
    assert blocker.args == [created.id]


def test_detail_view_loads_and_saves(qtbot):
    lib = _library()
    created = lib.create("original body", language="en")

    detail = DetailView(lib)
    qtbot.addWidget(detail)
    detail.load(created.id)
    assert detail._body.toPlainText() == "original body"

    detail._body.setPlainText("edited body")
    detail._title.setText("My Title")
    detail._tags.setText("bio, chem")

    with qtbot.waitSignal(detail.saved):
        detail._on_save()

    stored = lib.get(created.id)
    assert stored.text == "edited body"
    assert stored.title == "My Title"
    assert stored.tags == ["bio", "chem"]


def test_detail_view_copy_uses_clipboard(qtbot):
    lib = _library()
    created = lib.create("copy me", language="en")

    class FakeClipboard:
        def __init__(self):
            self.value = None

        def copy(self, text):
            self.value = text
            return True

    clip = FakeClipboard()
    detail = DetailView(lib, clipboard=clip)
    qtbot.addWidget(detail)
    detail.load(created.id)
    detail._on_copy()
    assert clip.value == "copy me"


def test_window_auto_save_refresh_shows_new_transcript(qtbot):
    lib = _library()
    window = MainWindow(lib)
    qtbot.addWidget(window)
    assert window._library_view._list.count() == 0

    lib.create("freshly dictated", language="en")
    window.refresh_library()
    assert window._library_view._list.count() == 1
