"""Centralized API routes for the Dicto desktop app."""

from __future__ import annotations

import os

# Base host for the Dicto API; overridable via the DICTO_API_URL env var.
BASE_URL = os.environ.get("DICTO_API_URL", "https://dicto.up.railway.app")

# API version prefix.
API_V1 = "/api/v1"

# Endpoint paths (relative to BASE_URL).
TRANSCRIBE = f"{API_V1}/transcribe"
TRANSFORM = f"{API_V1}/transform"
PRESETS = f"{API_V1}/presets"
REPORT = f"{API_V1}/report"
MODELS = f"{API_V1}/models"


def url(path: str) -> str:
    """Join the configured BASE_URL with an endpoint path."""
    return f"{BASE_URL}{path}"


def transcribe() -> str:
    """Full URL for POST /api/v1/transcribe."""
    return url(TRANSCRIBE)


def transform() -> str:
    """Full URL for POST /api/v1/transform."""
    return url(TRANSFORM)


def presets() -> str:
    """Full URL for GET /api/v1/presets."""
    return url(PRESETS)


def report() -> str:
    """Full URL for POST /api/v1/report."""
    return url(REPORT)


def models() -> str:
    """Full URL for GET /api/v1/models."""
    return url(MODELS)
