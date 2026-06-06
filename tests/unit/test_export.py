"""Unit tests for transcript export (pure content + disk write)."""

from __future__ import annotations

from dicto.core.export import build_export, to_markdown, to_txt, write_export
from dicto.core.models import Transcript


def _transcript(**kw) -> Transcript:
    base = dict(
        id="abc123",
        text="Hello world.",
        created_at="2026-06-06T10:00:00Z",
        language="en",
    )
    base.update(kw)
    return Transcript(**base)


def test_txt_is_just_the_body():
    assert to_txt(_transcript()) == "Hello world.\n"


def test_markdown_has_heading_and_metadata():
    md = to_markdown(_transcript(title="My note", subject="Bio", tags=["a", "b"]))
    assert md.startswith("# My note")
    assert "**Date:** 2026-06-06T10:00:00Z" in md
    assert "**Language:** en" in md
    assert "**Subject:** Bio" in md
    assert "**Tags:** a, b" in md
    assert md.rstrip().endswith("Hello world.")


def test_markdown_default_title_when_missing():
    assert to_markdown(_transcript()).startswith("# Dicto transcript")


def test_build_export_filename_and_format():
    p = build_export(_transcript(title="Clase de Bio!"), "md")
    assert p.filename == "Clase-de-Bio.md"
    assert p.content.startswith("# Clase de Bio!")

    p = build_export(_transcript(), "txt")
    assert p.filename == "dicto-abc123.txt"


def test_build_export_rejects_unknown_format():
    try:
        build_export(_transcript(), "pdf")
    except ValueError as e:
        assert "pdf" in str(e)
    else:  # pragma: no cover
        raise AssertionError("expected ValueError")


def test_write_export_infers_format_from_extension(tmp_path):
    md_path = write_export(_transcript(title="T"), tmp_path / "out.md")
    assert md_path.read_text(encoding="utf-8").startswith("# T")

    txt_path = write_export(_transcript(), tmp_path / "out.txt")
    assert txt_path.read_text(encoding="utf-8") == "Hello world.\n"


def test_write_export_explicit_format_wins(tmp_path):
    # .dat extension but forced markdown.
    p = write_export(_transcript(title="X"), tmp_path / "out.dat", fmt="md")
    assert p.read_text(encoding="utf-8").startswith("# X")
