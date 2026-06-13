# Fase 5 — Transformar (IA) para estudiantes ✅

Sobre una transcripción guardada, el usuario aplica **presets de IA**
(resumen, puntos clave, flashcards, reescribir) desde las pestañas del detalle,
y conversa con sus apuntes en el **chat** ("pregúntale a tus apuntes"). Los
presets son **datos declarativos**; la decisión preset→petición es **pura**; el
*efecto* (red) vive detrás de `TransformService`, hoy contra el `MockStore`,
mañana httpx con la misma firma. Los resultados de los presets se **cachean**
por `(transcript_id, preset)` para que reabrir una pestaña sea instantáneo; las
respuestas del chat **no** se cachean (dependen de la pregunta).

## Estructura nueva en `src/dicto/`

```
transform/schema.py        Preset (id, label_key, instructions, is_chat) +
                           build_request (PURO): preset + transcripción →
                           TransformRequest; en chat pliega la pregunta en las
                           instrucciones.
transform/presets.py       Presets declarativos para estudiantes: SUMMARY,
                           KEYPOINTS, FLASHCARDS, REWRITE + ASK (chat).
                           TAB_PRESETS / ALL_PRESETS, get_preset(id). Los ids
                           coinciden con los sufijos de detail.tab.*.
services/api/transform.py  transform_text (POST sin estado a /transform, errores
                           tipados) + TransformService: resuelve el preset, mira
                           la caché (/transforms/{id}, mock), llama en miss y
                           guarda; construye su ApiClient en perezoso desde la
                           API key; chat nunca se cachea, force salta la caché.
services/api/mocks.py      + caché de transforms (get/list/save_transform) clave
                           (transcript_id, preset) + now().
services/api/routes.py     + endpoint /transforms/{transcript_id}.
ui/main/transform_worker.py run_transform: corre la llamada en el QThreadPool y
                           devuelve resultado/error en el hilo Qt (red fuera del
                           hilo de UI).
ui/main/transform_render.py render_result: texto del transform → widget con la
                           forma del diseño — flashcards en grid de tarjetas,
                           puntos clave en lista numerada, resumen/reescribir en
                           prosa; parseo tolerante con fallback a prosa.
ui/main/detail_view.py     Pestañas de transform (stack: editor | resultado);
                           cabecera del resultado (✦ preset · chip "Cacheado" ·
                           Generar/Regenerar) sobre un scroll con el contenido
                           renderizado; footer con "Prompt personalizado". La
                           pestaña Preguntar emite askRequested para abrir el chat.
ui/main/chat_view.py       ChatView: cabecera + scroll de burbujas (usuario a la
                           derecha/acento, IA a la izquierda/elevado) + input/Ask.
                           Corre el preset ASK anclado a una transcripción.
ui/main/window.py          El panel derecho apila DetailView + ChatView; Ask
                           cambia al chat, una nueva selección vuelve al detalle.
```

**Principios:** los presets son datos (cambiar el comportamiento = cambiar las
instrucciones, sin tocar servicio ni UI) · `build_request` es puro y testeable
sin Qt ni red · el efecto va detrás de `TransformService`, mockeado hoy con la
misma firma · color/idioma por tokens y `t()` · reloj/ids del mock inyectables →
tests deterministas · las llamadas de red corren fuera del hilo Qt.

## Flujo

1. **Pestaña de transform.** En `DetailView`, seleccionar una pestaña
   (Resumen/Puntos clave/Flashcards/Reescribir) muestra el panel de resultado;
   si hay caché la pinta, si no ofrece **Generar**. Generar llama
   `TransformService.apply(transcript_id, text, preset, settings)` en un worker;
   el resultado se cachea y se pinta. **Regenerar** fuerza una llamada nueva
   (`force=True`).
2. **Caché.** `apply` mira `MockStore.get_transform((id, preset))`; en miss
   construye `build_request` y hace `transform_text` (POST a `/transform`), luego
   `save_transform`. Reabrir la pestaña sirve de la caché sin red.
3. **Chat.** La pestaña *Preguntar* del detalle emite `askRequested(id)`; la
   ventana cambia el panel a `ChatView`. Cada pregunta corre el preset `ASK`
   con la pregunta plegada en las instrucciones y la transcripción como
   contexto; la respuesta se añade al log y **no** se cachea.
4. **Cliente perezoso.** `TransformService` construye su `ApiClient` desde
   `settings.transcription.api_key` la primera vez que debe llamar; sin key,
   `AuthError`.

## Verificado

- Cada preset devuelve resultado y se **cachea**: la 2.ª apertura no vuelve a
  llamar al endpoint; **Regenerar** sí. El chat responde sobre la transcripción
  y no se cachea (la pregunta va en las instrucciones, el cuerpo es el contexto).
- UI (pytest-qt): seleccionar una pestaña de transform ofrece **Generar** (no
  genera solo); generar pinta el resultado; la pestaña **Preguntar** emite
  `askRequested` y vuelve al transcript; el chat envía y pinta la respuesta.
- **24 tests nuevos**: `pytest tests/unit/test_transform.py
  tests/integration/test_transform_flow.py tests/ui/test_transform_view.py`
  (incluye parseo de flashcards/puntos clave y fallback a prosa).
- `ruff` limpio en los ficheros de la fase; `mypy` sin errores nuevos.
- Capturas (`scripts/screenshot.py`, claro y oscuro): `05_transform.png`
  (flashcards en grid + cabecera con chip de caché + footer "Prompt
  personalizado"), `06_chat.png` (burbujas usuario/IA). Cotejadas contra el
  diseño `Dicto - Entrega/capturas/02-principal-detalle.png`.

## Pendiente (otras fases)

- Cuenta, planes y uso de minutos → **Fase 6** (`services/api/account.py`).
- Paneles de ajustes (cuenta, salida, privacidad, about) → **Fase 6**.
- Auto-update, bug report, completar locales → **Fase 6**.
