"""Dictionary service — the user's own terms/acronyms/names (mocked).

The user teaches Dicto domain jargon so the STT model spells it right. Terms live
in the user's backend; this is the typed seam in front of it, backed by the
in-memory :class:`MockStore` for now. The pure ``core/dictionary.py`` turns the
terms into the biasing prompt the transcribe call uses.
"""

from __future__ import annotations

from typing import List

from dicto.core.models import DictTerm, DictTermKind
from dicto.services.api.mocks import MockStore, get_mock_store


class DictionaryService:
    """CRUD for dictionary terms, backed by the mock store for now."""

    def __init__(self, store: MockStore | None = None) -> None:
        self._store = store or get_mock_store()

    def list(self) -> List[DictTerm]:
        return self._store.list_terms()

    def create(
        self,
        text: str,
        *,
        kind: DictTermKind = DictTermKind.TERM,
        note: str | None = None,
    ) -> DictTerm:
        text = text.strip()
        if not text:
            raise ValueError("dictionary term cannot be empty")
        return self._store.create_term(text, kind=kind, note=note)

    def delete(self, term_id: str) -> bool:
        return self._store.delete_term(term_id)
