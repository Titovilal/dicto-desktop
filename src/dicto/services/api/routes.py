"""API endpoint URLs.

Base host is overridable via ``DEFAULT_BASE_URL`` so dev/CI can point at a mock or
staging backend. Paths mirror the contract in REBUILD_PLAN.md.
"""

from __future__ import annotations

import os

DEFAULT_BASE_URL = "https://dicto.up.railway.app"
API_V1 = "/api/v1"


def base_url() -> str:
    return os.environ.get("DEFAULT_BASE_URL", DEFAULT_BASE_URL).rstrip("/")


def url(path: str) -> str:
    return f"{base_url()}{path}"


def transcribe() -> str:
    return url(f"{API_V1}/transcribe")


def transform() -> str:
    return url(f"{API_V1}/transform")


def presets() -> str:
    return url(f"{API_V1}/presets")


def report() -> str:
    return url(f"{API_V1}/report")


# ── Library (Phase 4, mocked) ─────────────────────────────────────────────


def library() -> str:
    return url(f"{API_V1}/library")


def library_item(transcript_id: str) -> str:
    return url(f"{API_V1}/library/{transcript_id}")


# ── Dictionary (Phase 4, mocked) ──────────────────────────────────────────


def dictionary() -> str:
    return url(f"{API_V1}/dictionary")


def dictionary_item(term_id: str) -> str:
    return url(f"{API_V1}/dictionary/{term_id}")
