# Fase 3 — Salida (insertar en cursor, limpieza, export) ✅

Cuando una transcripción termina, el texto se **limpia** y un **router** decide
a dónde va: por defecto al **cursor** de la app con foco (inyección), con
**portapapeles como fallback** cuando no se puede inyectar. La política es pura
(testeable sin teclado ni red); el efecto (teclado/portapapeles) vive en
`services/`.

## Estructura nueva en `src/dicto/`

```
core/cleanup.py        clean_dictation: quita muletillas (lista conservadora por
                       idioma es/en), arregla espacios/puntuación, capitaliza frases.
                       Activado por defecto (behavior.cleanup_enabled). PURO.
core/result_router.py  route_result → RouteDecision (cursor vs portapapeles vs
                       biblioteca) desde settings + flag can_inject. PURO.
core/export.py         build_export / write_export: txt o Markdown desde un
                       Transcript (md lleva título + metadatos). PURO.
services/clipboard.py  Clipboard: backend perezoso win32 → Qt → no-op (headless).
                       Es el fallback y el mecanismo que usa la inyección por dentro.
services/injector.py   Injector: pega en el cursor (portapapeles + Ctrl+V) + auto-enter
                       opcional. available() dice si hay inyección real. pynput perezoso.
```

**Principios:** la *decisión* es pura, el *efecto* va en services · la inyección
**siempre** deja el texto en el portapapeles primero, así un paste fallido cae al
fallback sin perder nada · color/idioma por tokens · pynput/win32 perezosos
(importar nunca exige display ni Windows → tests headless).

## Flujo de entrega

1. `TranscriptionDone` → `app.py` limpia el texto (`clean_dictation`) si
   `cleanup_enabled`.
2. `route_result(text, auto_paste, auto_enter, can_inject=Injector.available())`
   devuelve un `RouteDecision`.
3. `decision.inject` → `Injector.inject` (Ctrl+V, + Enter si procede); si falla,
   el texto ya está en el portapapeles. Si no, `Clipboard.copy` (fallback marcado
   con `used_fallback`).
4. Guardar en biblioteca → **Fase 4**.

## Verificado

- Dictado → texto limpio pegado en el cursor; muletillas fuera, espacios y
  puntuación normalizados, frases capitalizadas.
- Sin inyección disponible (headless) → cae al portapapeles, nada se pierde.
- Export txt (cuerpo tal cual) y md (título + metadatos + cuerpo); nombre de
  fichero saneado.
- **31 tests nuevos** (112 en total): `pytest tests/unit/test_cleanup.py
  tests/unit/test_result_router.py tests/unit/test_export.py tests/unit/test_delivery.py`
- `ruff` limpio; `mypy` sin errores reales (solo `import-untyped` de
  win32clipboard/pynput, igual que Fases 1–2).

## Pendiente

- UI de export/copy en el detalle (los helpers `core/export` ya existen) → **Fase 4**
  (cuando exista `detail_view`).
- Feedback visual de entrega ("pegado" / "copiado") — claves i18n `delivery.*` y
  `detail.*` ya añadidas; conectar a un toast/estado → **Fase 6**.
- Endurecer la supresión del atajo para que no llegue a otras apps → si molesta.
