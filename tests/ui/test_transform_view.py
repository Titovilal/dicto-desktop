"""UI tests for the Phase 5 transform tabs (detail view) and chat view.

Need a QApplication; use pytest-qt's ``qtbot`` and skip where Qt has no platform
plugin. Transforms are stubbed at the service so no network is touched. The
worker runs the call inline-ish on the thread pool; ``qtbot.waitUntil`` drains it.
"""

from __future__ import annotations

import itertools

import pytest

from dicto.config.settings import Settings
from dicto.services.api.library import LibraryService
from dicto.services.api.mocks import MockStore

pytest.importorskip("PySide6.QtWidgets")

from dicto.ui.main.chat_view import ChatView  # noqa: E402
from dicto.ui.main.detail_view import DetailView  # noqa: E402
from dicto.ui.main import transform_render  # noqa: E402


def _library() -> LibraryService:
    counter = itertools.count(1)
    return LibraryService(MockStore(clock=lambda: f"2026-01-01T00:00:{next(counter):02d}Z"))


def _all_label_text(widget) -> str:
    """Concatenate the text of every QLabel under ``widget`` (rendered output)."""
    from PySide6.QtWidgets import QLabel

    return " ".join(lbl.text() for lbl in widget.findChildren(QLabel))


class _FakeTransform:
    """Records calls; returns canned text. Mirrors TransformService's surface."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []
        self._cache: dict[tuple[str, str], object] = {}

    def cached(self, transcript_id, preset_id):
        return self._cache.get((transcript_id, preset_id))

    def apply(self, transcript_id, text, preset, settings, *, question=None, force=False):
        pid = preset.id if hasattr(preset, "id") else preset
        self.calls.append((transcript_id, pid))
        from dicto.core.models import TransformResult

        result = TransformResult(transcript_id, pid, f"OUT:{pid}", "now")
        if not getattr(preset, "is_chat", False):
            self._cache[(transcript_id, pid)] = result
        return result


def test_selecting_transform_tab_offers_generate(qtbot):
    lib = _library()
    created = lib.create("body text", language="en")
    fake = _FakeTransform()
    detail = DetailView(lib, transform=fake, settings=Settings())
    qtbot.addWidget(detail)
    detail.load(created.id)

    # Switch to the Summary tab (index 1) — nothing cached yet.
    detail._tabs.setCurrentIndex(1)
    assert detail._stack.currentIndex() == 1
    assert fake.calls == []  # generation is on demand, not automatic

    # Generate → service called once, result rendered.
    detail._on_generate()
    qtbot.waitUntil(lambda: fake.calls == [(created.id, "summary")], timeout=2000)
    qtbot.waitUntil(lambda: "OUT:summary" in _all_label_text(detail._xform_scroll), timeout=2000)


def test_ask_tab_emits_ask_requested(qtbot):
    lib = _library()
    created = lib.create("body text", language="en")
    detail = DetailView(lib, transform=_FakeTransform(), settings=Settings())
    qtbot.addWidget(detail)
    detail.load(created.id)

    ask_index = detail._tabs.count() - 1
    with qtbot.waitSignal(detail.askRequested) as blocker:
        detail._tabs.setCurrentIndex(ask_index)
    assert blocker.args == [created.id]
    # It snaps back to the transcript so the tab can be re-triggered.
    assert detail._tabs.currentIndex() == 0


def test_chat_view_asks_and_renders_answer(qtbot):
    lib = _library()
    created = lib.create("la mitocondria produce ATP", language="es")
    fake = _FakeTransform()
    chat = ChatView(lib, transform=fake, settings=Settings())
    qtbot.addWidget(chat)
    chat.load(created.id)

    chat._input.setText("¿qué hace?")
    chat._on_ask()
    qtbot.waitUntil(lambda: fake.calls == [(created.id, "ask")], timeout=2000)
    qtbot.waitUntil(lambda: "OUT:ask" in _all_label_text(chat), timeout=2000)
    assert "¿qué hace?" in _all_label_text(chat)


# ── result rendering (parsing) ──────────────────────────────────────────────


def test_flashcards_parse_q_a_pairs():
    text = "Q: ¿Qué es el ATP? / A: La moneda energética.\nQ: ¿Dónde? / A: Mitocondria."
    cards = transform_render._parse_flashcards(text)
    assert cards == [
        ("¿Qué es el ATP?", "La moneda energética."),
        ("¿Dónde?", "Mitocondria."),
    ]


def test_keypoints_parse_bullets():
    text = "- Primer punto\n* Segundo punto\n1. Tercero"
    assert transform_render._parse_points(text) == [
        "Primer punto", "Segundo punto", "Tercero",
    ]


def test_flashcards_widget_has_one_card_per_pair(qtbot):
    w = transform_render.render_result(
        "flashcards", "Q: a / A: b\nQ: c / A: d"
    )
    qtbot.addWidget(w)
    from PySide6.QtWidgets import QFrame

    cards = [f for f in w.findChildren(QFrame) if f.objectName() == "xformCard"]
    assert len(cards) == 2


def test_plain_text_falls_back_to_prose(qtbot):
    w = transform_render.render_result("summary", "Un resumen sin formato.")
    qtbot.addWidget(w)
    assert w.objectName() == "prose"
    assert "resumen" in w.text()
