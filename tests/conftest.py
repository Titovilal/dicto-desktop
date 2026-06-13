"""Shared test fixtures."""

from __future__ import annotations

import pytest

from dicto import i18n
from dicto.config.settings import reset_settings


@pytest.fixture(autouse=True)
def _reset_global_state():
    """Keep the i18n language and settings singleton from leaking across tests."""
    original_lang = i18n.get_language()
    yield
    i18n.set_language(original_lang)
    reset_settings()
