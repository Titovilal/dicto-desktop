# Fase 4 — Biblioteca + diccionario propio (vía API mock) ✅

Toda transcripción se **guarda automáticamente** en la biblioteca (nunca
efímera). La biblioteca y el diccionario viven en el **backend del usuario**;
aquí se implementan **mocks tipados** (un `MockStore` en memoria) detrás de las
mismas clases de servicio, para construir y testear la UI sin servidor. El
**diccionario** del usuario se convierte en un **prompt de biasing** que mejora
cómo el STT escribe la jerga.

## Estructura nueva en `src/dicto/`

```
services/api/mocks.py        MockStore: base de datos en memoria, determinista
                             (ids secuenciales trx_/trm_, reloj inyectable,
                             thread-safe). get/set/reset_mock_store. Sustituible
                             por httpx real detrás de los mismos servicios.
services/api/library.py      LibraryService: CRUD + búsqueda de transcripciones.
                             query_transcripts (PURO): filtra por texto/etiqueta
                             y ordena (recientes/antiguas/título). all_tags().
services/api/dictionary.py   DictionaryService: CRUD de términos/siglas/nombres.
services/api/routes.py       + endpoints /library, /library/{id}, /dictionary,
                             /dictionary/{id} (contrato para el backend real).
core/dictionary.py           build_bias_prompt (PURO): términos → prompt de
                             biasing (dedup case-insensitive, orden preservado,
                             cap de términos/caracteres). None si no hay nada.
ui/main/window.py            Shell de zonas: biblioteca (izq) + detalle (der) en
                             un QSplitter + barra de estado. refresh_library().
                             (El modal de ajustes — 3.ª zona — → Fase 6.)
ui/main/library_view.py      Lista + búsqueda + orden + filtro por etiqueta.
                             Emite transcriptSelected(id) / emptied.
ui/main/detail_view.py       Ver/editar texto + título + etiquetas; Guardar,
                             Copiar, Exportar (txt/md vía core/export).
```

**Principios:** las *semánticas de consulta* son puras (`query_transcripts`,
`build_bias_prompt`) y testeables sin Qt ni red · el *efecto* (red) va detrás de
los servicios, hoy mockeado, mañana httpx, **misma firma** · color/idioma por
tokens y `t()`, nada hardcodeado · el reloj y los ids del mock son inyectables →
tests deterministas (sin `Date.now`/aleatoriedad, como el resto del repo).

## Flujo

1. **Diccionario → biasing.** Al empezar a grabar, el orquestador lee el
   diccionario (`DictionaryService.list`), lo convierte con `build_bias_prompt`
   y lo pasa como `prompt` a `make_transcribe_chunk` (best-effort: un fallo del
   diccionario nunca bloquea la grabación).
2. **Auto-guardado.** En `TranscriptionDone`, `app._on_transcription_done`
   limpia el texto (Fase 3) y lo **guarda** con `LibraryService.create` antes de
   entregarlo al cursor/portapapeles; luego refresca la ventana. Un fallo de
   guardado se registra pero no rompe la entrega.
3. **Biblioteca.** `LibraryView` lista lo guardado, busca por texto (cuerpo /
   título / etiquetas), ordena y filtra por etiqueta; al seleccionar emite el
   id y `DetailView` lo carga.
4. **Detalle.** Ver/editar texto, título y etiquetas → `LibraryService.update`
   (y refresca la lista). Copiar usa el mismo `Clipboard` de la app. Exportar
   construye txt/md con `core/export` y lo escribe vía diálogo de archivo.

## Verificado

- Transcribir → la transcripción **aparece en la biblioteca**; la búsqueda la
  encuentra por cuerpo/título/etiqueta; ordenar por reciente/antiguo/título.
- Editar texto/título/etiquetas y **Guardar** → persiste en el store y la lista
  se refresca; **Copiar** deja el cuerpo en el portapapeles; **Exportar** txt/md.
- El **diccionario** (`mitocondria`, `AEMET`) produce el prompt de biasing y el
  factory lo reenvía a la llamada de transcripción (test con WAV real + fake).
- **24 tests nuevos** (136 en total): `pytest tests/unit/test_dictionary.py
  tests/unit/test_library.py tests/integration/test_library_flow.py
  tests/ui/test_library.py`
- `ruff` limpio en los ficheros de la fase; `mypy` sin errores nuevos (los de
  `QCoreApplication` en `app.py` son previos a esta fase).

## Pendiente (otras fases)

- Modal de **ajustes** como 3.ª zona dentro de la principal → **Fase 6**.
- Panel de **diccionario** en ajustes (la UI de alta/baja de términos) → **Fase 6**
  (`ui/settings/dictionary.py`); el `DictionaryService` ya existe.
- **Transforms** de IA sobre la transcripción del detalle (pestañas) → **Fase 5**.
- Borrar transcripción desde la UI (el `LibraryService.delete` ya existe) → si se pide.
