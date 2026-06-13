"""Transform endpoint + service: apply an AI preset to a transcript.

``transform_text`` is the stateless POST to ``/api/v1/transform`` (mirrors
``transcribe.py``). ``TransformService`` layers on the product behaviour: it
resolves a preset, checks the cache (``/transforms/{id}``, mocked in
:class:`MockStore` for now), calls the endpoint on a miss, and stores the
result so reopening a tab is instant. The cache lives in the user's backend;
this is the typed seam in front of it.
"""

from __future__ import annotations

import logging

from dicto.config.settings import Settings
from dicto.core.models import TransformResult
from dicto.services.api import errors, routes
from dicto.services.api.client import ApiClient
from dicto.services.api.mocks import MockStore, get_mock_store
from dicto.transform import presets as preset_lib
from dicto.transform.schema import Preset, build_request

logger = logging.getLogger(__name__)


def transform_text(client: ApiClient, text: str, instructions: str, *, model: str) -> str:
    """POST ``text`` + ``instructions`` to ``/transform`` and return the result.

    Raises a typed :class:`~dicto.services.api.errors.APIError` on failure.
    """
    if not text.strip():
        raise errors.APIError("nothing to transform (empty text)", code="empty")

    payload = {"text": text, "instructions": instructions, "model": model}
    response = client.request("POST", routes.transform(), json=payload)
    body = response.json()
    result = (body.get("text") or "").strip()
    if not result:
        raise errors.APIError("transform API returned empty result", code="empty")
    return result


class TransformService:
    """Apply presets to transcripts, with a result cache.

    ``client`` is optional so the service can be constructed before the API key
    is known; an actual transform call requires one.
    """

    def __init__(self, client: ApiClient | None = None, store: MockStore | None = None) -> None:
        self._client = client
        self._store = store or get_mock_store()

    def _resolve_client(self, settings: Settings) -> ApiClient:
        """Return the client, building one from the API key on first use."""
        if self._client is None:
            api_key = settings.transcription.api_key
            if not api_key:
                raise errors.AuthError("Dicto API key is required to transform")
            self._client = ApiClient(api_key)
        return self._client

    def cached(self, transcript_id: str, preset_id: str) -> TransformResult | None:
        """Return a previously computed transform, or ``None``."""
        return self._store.get_transform(transcript_id, preset_id)

    def apply(
        self,
        transcript_id: str,
        transcript_text: str,
        preset: Preset | str,
        settings: Settings,
        *,
        question: str | None = None,
        force: bool = False,
    ) -> TransformResult:
        """Apply ``preset`` to a transcript, using the cache when possible.

        Chat presets (and any explicit ``force``) always call the endpoint and
        are not cached — the answer depends on the question, not just the id.
        """
        resolved = preset if isinstance(preset, Preset) else preset_lib.get_preset(preset)
        if resolved is None:
            raise errors.APIError(f"unknown preset: {preset}", code="bad_preset")

        cacheable = not resolved.is_chat and not force
        if cacheable:
            hit = self._store.get_transform(transcript_id, resolved.id)
            if hit is not None:
                return hit

        client = self._resolve_client(settings)
        request = build_request(
            resolved,
            transcript_text,
            model=settings.transform.model,
            question=question,
        )
        text = transform_text(
            client,
            request.text,
            request.instructions,
            model=request.model,
        )

        if cacheable:
            return self._store.save_transform(transcript_id, resolved.id, text)
        return TransformResult(
            transcript_id=transcript_id,
            preset=resolved.id,
            text=text,
            created_at=self._store.now(),
        )
