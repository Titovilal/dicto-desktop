"""Unit tests for the library service + pure query semantics (mocked store)."""

from __future__ import annotations

import itertools

from dicto.core.models import Transcript
from dicto.services.api.library import LibraryQuery, LibraryService, query_transcripts
from dicto.services.api.mocks import MockStore


def _store_with_clock() -> MockStore:
    # Monotonic ISO-ish stamps so created_desc/asc ordering is deterministic.
    counter = itertools.count(1)
    return MockStore(clock=lambda: f"2026-01-01T00:00:{next(counter):02d}Z")


def _svc() -> LibraryService:
    return LibraryService(_store_with_clock())


# ── pure query ────────────────────────────────────────────────────────────


def _t(id_: str, text: str, *, created: str, tags=None, title=None) -> Transcript:
    return Transcript(id=id_, text=text, created_at=created, tags=tags or [], title=title)


def test_query_text_searches_body_title_and_tags():
    items = [
        _t("1", "the mitochondria is the powerhouse", created="a"),
        _t("2", "unrelated", created="b", title="Mitochondria notes"),
        _t("3", "nope", created="c", tags=["biology"]),
    ]
    found = {t.id for t in query_transcripts(items, LibraryQuery(text="mitochondria"))}
    assert found == {"1", "2"}
    found_tag = {t.id for t in query_transcripts(items, LibraryQuery(text="biology"))}
    assert found_tag == {"3"}


def test_query_tag_filter():
    items = [
        _t("1", "x", created="a", tags=["bio"]),
        _t("2", "y", created="b", tags=["math"]),
    ]
    out = query_transcripts(items, LibraryQuery(tag="bio"))
    assert [t.id for t in out] == ["1"]


def test_query_sort_orders():
    items = [
        _t("1", "x", created="2026-01-01T00:00:01Z", title="banana"),
        _t("2", "y", created="2026-01-01T00:00:03Z", title="apple"),
        _t("3", "z", created="2026-01-01T00:00:02Z", title="cherry"),
    ]
    newest = [t.id for t in query_transcripts(items, LibraryQuery(sort="created_desc"))]
    assert newest == ["2", "3", "1"]
    oldest = [t.id for t in query_transcripts(items, LibraryQuery(sort="created_asc"))]
    assert oldest == ["1", "3", "2"]
    by_title = [t.id for t in query_transcripts(items, LibraryQuery(sort="title"))]
    assert by_title == ["2", "1", "3"]  # apple, banana, cherry


# ── service CRUD ──────────────────────────────────────────────────────────


def test_create_then_list_and_get():
    svc = _svc()
    created = svc.create("hello world", language="en")
    assert created.id
    assert created.created_at.endswith("Z")
    fetched = svc.get(created.id)
    assert fetched is not None and fetched.text == "hello world"
    assert [t.id for t in svc.list()] == [created.id]


def test_update_fields():
    svc = _svc()
    t = svc.create("body")
    updated = svc.update(t.id, title="My note", tags=["bio"], text="edited")
    assert updated is not None
    assert updated.title == "My note"
    assert updated.tags == ["bio"]
    assert updated.text == "edited"
    # Round-trips through the store.
    assert svc.get(t.id).title == "My note"


def test_update_missing_returns_none():
    svc = _svc()
    assert svc.update("nope", title="x") is None


def test_delete():
    svc = _svc()
    t = svc.create("body")
    assert svc.delete(t.id) is True
    assert svc.get(t.id) is None
    assert svc.delete(t.id) is False


def test_all_tags_distinct_sorted():
    svc = _svc()
    svc.create("a", tags=["math", "bio"])
    svc.create("b", tags=["bio", "chem"])
    assert svc.all_tags() == ["bio", "chem", "math"]


def test_list_returns_copies_not_internal_refs():
    svc = _svc()
    t = svc.create("body")
    listed = svc.list()[0]
    listed.text = "mutated"
    # Mutating the returned object must not change the stored one.
    assert svc.get(t.id).text == "body"
