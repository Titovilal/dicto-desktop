# Problemas anteriores

Registro corto de bugs ya resueltos, para no repetirlos.

## Fase 2 — El atajo grababa pero "no pasaba nada"

**Síntoma:** pulsar Ctrl+Shift+Space grababa (se creaban chunks en disco) pero
acababa en ERROR silencioso con mensaje vacío y reintentos.

**Causa:** en `orchestrator.py`, `_build_client()` creaba el `ApiClient` pero
**no lo guardaba** en `self._client` (hacía `return` sin asignar). Al transcribir
en el hilo worker, `self._client` era `None` → fallo con `str()` vacío.

**Arreglo:**
- `_build_client` ahora asigna y cachea `self._client`.
- Se graba primero; la API key solo se pide al **parar** (el audio es sagrado y
  no debe bloquearse por falta de key — queda en disco para reintentar).
- Callbacks del hotkey marshalados al hilo Qt vía señales de intent
  (`_startIntent`/`_stopIntent`/…), no se tocan widgets desde el hilo de pynput.
- `pipeline._run_job` loguea el **tipo** de excepción + traceback (un `str()`
  vacío ya no es indiagnosticable).

**Test de regresión:** `tests/ui/test_orchestrator.py` →
`test_stop_builds_client_and_transcribes` afirma `orch._client is not None`.

**Requisito:** `DICTO_API_KEY` en `.env` (junto a `DEFAULT_BASE_URL`).
