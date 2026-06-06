# Dicto — Plan de reconstrucción desde 0

> Reescritura de la app de escritorio (Windows primero) manteniendo el stack que ya
> funciona (**PySide6 + httpx + sounddevice/soundcard + pynput + pywin32 + PyInstaller/Inno**)
> pero con una arquitectura por capas que soporta todo el documento de features.

## Decisiones tomadas

- **Distribución:** el usuario final instala un **.exe sin necesidad de Python** (PyInstaller
  congela el intérprete dentro; Inno Setup hace el instalador). Internamente el paquete se
  renombra a `src/dicto/` para imports limpios (`dicto.app`, `python -m dicto`); de cara al
  usuario no cambia nada.
- **Persistencia:** la biblioteca, el diccionario, los transforms y la cuenta viven en el
  **backend del usuario (su base de datos)**, no en local. La app habla con la API. En este
  repo solo se implementan **mocks tipados de las llamadas API**; él los conecta a su backend.
  Lo único local: config (settings), audio en disco mientras se graba (chunks) y logs.
- **Orquestación:** se rompe el `Controller` monolítico (424 líneas) en un `core/` puro
  (sin Qt, testeable) + `app.py` (wiring Qt) + máquinas de estado pequeñas.

## Principios de arquitectura

1. **Por capas, no por tipo.** `core` (lógica pura) → `audio`/`services` (efectos: SO, red) →
   `app` (orquestación) → `ui` (Qt). El core no importa Qt ni httpx.
2. **El audio es el dato sagrado.** Captura → disco en chunks → cola de jobs reintentables.
   Nada vive solo en RAM. La transcripción es un *job* sobre audio ya persistido.
3. **Dos ventanas + bandeja.** `MainWindow` (biblioteca/detalle/ajustes-modal) + `Overlay`
   efímero. La bandeja es el ancla. Ajustes = modal DENTRO de la principal (nunca ventana aparte).
4. **API mockeable.** Toda llamada de red pasa por `services/api/` con respuestas mock
   intercambiables, para desarrollar la UI sin backend.
5. **Tema e idioma son transversales, no features.** Color e idioma se resuelven con
   **tokens semánticos** (`color.bg`, `color.text`, `t("key")`), nunca colores ni textos
   hardcodeados en widgets. Un `ThemeManager` y un `i18n` viven desde Fase 0 y emiten
   señales (`themeChanged` / `languageChanged`) para refrescar la UI **en caliente**. Si se
   dejan para el final, toda la UI hay que reescribirla.

---

## Estructura de carpetas objetivo

```
dicto-desktop/
├─ src/dicto/
│  ├─ __init__.py
│  ├─ __main__.py                  # python -m dicto
│  ├─ app.py                       # DictoApp: arranca Qt, DI, wiring de señales
│  ├─ version.py
│  │
│  ├─ core/                        # LÓGICA PURA — sin Qt, sin red, sin SO
│  │  ├─ state.py                  # AppState + RecordingSession (idle/rec/paused/processing)
│  │  ├─ events.py                 # bus de eventos tipado del dominio
│  │  ├─ models.py                 # Transcript, TransformResult, DictTerm, Job, Plan, Account
│  │  ├─ pipeline.py               # orquesta capture→persist→transcribe→transform→deliver
│  │  ├─ vad.py                    # recorte de silencios (webrtcvad)
│  │  ├─ chunking.py               # política de chunks a disco (tamaño/rotación)
│  │  ├─ dictionary.py             # diccionario propio → biasing/prompt para STT
│  │  ├─ cleanup.py                # limpieza de dictado (muletillas, puntuación)
│  │  └─ result_router.py          # decide cursor vs portapapeles vs biblioteca
│  │
│  ├─ audio/                       # CAPTURA (efectos de audio aislados)
│  │  ├─ devices.py                # enumerar/seleccionar micro
│  │  ├─ capture.py                # AudioCapture: stream → chunks a disco
│  │  ├─ loopback.py               # WASAPI loopback (audio del sistema)
│  │  ├─ monitor.py                # AudioMonitor para test de micro + nivel en vivo
│  │  └─ session_writer.py         # escribe chunks a disco mientras se graba
│  │
│  ├─ services/                    # EFECTOS externos (red, SO)
│  │  ├─ api/
│  │  │  ├─ client.py              # httpx base: auth, reintentos, errores tipados
│  │  │  ├─ transcribe.py          # POST audio → texto (modelo rápido/preciso)
│  │  │  ├─ transform.py           # POST texto + preset → texto IA
│  │  │  ├─ library.py             # CRUD biblioteca + búsqueda (MOCK)
│  │  │  ├─ dictionary.py          # CRUD diccionario (MOCK)
│  │  │  ├─ account.py             # cuenta, plan, minutos incluidos, uso (MOCK)
│  │  │  ├─ report.py              # envío de logs / bug report
│  │  │  ├─ mocks.py               # respuestas mock intercambiables
│  │  │  └─ errors.py              # RateLimit, AuthError, QuotaExceeded...
│  │  ├─ hotkey.py                 # listener global (hold/toggle) robusto
│  │  ├─ injector.py               # insertar en cursor + auto-enter
│  │  ├─ clipboard.py              # portapapeles (fallback)
│  │  └─ updater.py                # auto-update Windows (Inno, in-place)
│  │
│  ├─ transform/                   # PRESETS DE IA (declarativos)
│  │  ├─ presets.py                # resumen, puntos clave, flashcards, reescribir, chat
│  │  └─ schema.py                 # contrato preset → request de /transform
│  │
│  ├─ config/
│  │  ├─ settings.py               # Settings tipado (pydantic) + load/save
│  │  └─ defaults.py               # defaults (es, limpieza on, modelo rápido)
│  │
│  ├─ i18n/
│  │  ├─ __init__.py               # t() / loader / señal languageChanged
│  │  └─ locales/                  # en.json, es.json, de.json, fr.json, pt.json
│  │
│  ├─ ui/
│  │  ├─ tray.py                   # bandeja: icono de estado + menú (ancla)
│  │  ├─ overlay/
│  │  │  ├─ overlay.py             # ventana efímera arrastrable
│  │  │  ├─ waveform.py            # onda en vivo
│  │  │  └─ controls.py            # timer, pausa, parar
│  │  ├─ main/
│  │  │  ├─ window.py              # MainWindow: contenedor de las 3 zonas
│  │  │  ├─ library_view.py        # lista + búsqueda + orden + etiquetas
│  │  │  ├─ detail_view.py         # texto + pestañas transform + export/copy/edit
│  │  │  ├─ chat_view.py           # "pregúntale a tus apuntes"
│  │  │  └─ settings_modal.py      # AJUSTES como modal DENTRO de la principal
│  │  ├─ settings/                 # paneles del modal
│  │  │  ├─ general.py  audio.py  hotkey.py  account.py  dictionary.py
│  │  │  ├─ appearance.py          # tema (claro/oscuro/sistema) + idioma
│  │  │  ├─ privacy.py             # "Datos y privacidad" (qué pasa con el audio)
│  │  │  └─ about.py
│  │  ├─ components/               # widgets reutilizables (consumen tokens del theme)
│  │  ├─ splash.py
│  │  ├─ icons.py
│  │  └─ theme/
│  │     ├─ manager.py             # ThemeManager: aplica QSS, señal themeChanged, sigue al SO
│  │     ├─ tokens.py              # tokens semánticos (color.bg/text/accent…) por tema
│  │     └─ palettes.py            # paletas light / dark
│  │
│  └─ utils/
│     ├─ logger.py                 # logging + buffer para reporte de errores
│     ├─ errors.py                 # captura/exporta log para enviar
│     └─ platform.py               # rutas Windows, helpers SO
│
├─ assets/                         # iconos, fuentes
├─ tests/
│  ├─ unit/        # core/ y audio/ sin Qt — la mayoría
│  ├─ integration/ # pipeline completo con API y audio mockeados
│  ├─ ui/          # pytest-qt
│  └─ fixtures/    # audios cortos, respuestas API
├─ packaging/      # dicto.spec, installer.iss, build.yml
└─ docs/ (.ctx/)   pyproject.toml   README.md   AGENTS.md
```

---

## Endpoints API (existentes + nuevos a mockear)

Existentes (ver `.ctx/docs/endpoints_used.md`):
- `POST /api/v1/transcribe`, `POST /api/v1/transform`, `GET /api/v1/presets`, `POST /api/v1/report`

Nuevos a definir como **mock** (el usuario los implementa en su backend):
- `GET /api/v1/library` — lista de transcripciones (paginada, buscable, filtro por tag)
- `GET /api/v1/library/{id}` — detalle de una transcripción
- `POST /api/v1/library` — guardar transcripción nueva
- `PATCH /api/v1/library/{id}` — editar texto / tags / asignatura
- `DELETE /api/v1/library/{id}`
- `GET/POST/DELETE /api/v1/dictionary` — términos del diccionario propio
- `GET /api/v1/account` — plan, minutos incluidos, minutos usados, estado
- `GET /api/v1/transforms/{transcript_id}` — caché de transforms ya generados

---

## Fases

> Orden alineado con el doc: 1) fiabilidad en largo · 2) biblioteca + diccionario ·
> 3) transforms para estudiantes · 4) auto-update + planes.

### Fase 0 — Andamiaje y migración del esqueleto
- [x] Crear `src/dicto/` con la estructura de carpetas y `__init__.py` en cada paquete
- [x] `pyproject.toml`: paquete `dicto`, entrypoint `dicto = "dicto.app:main"`, deps
- [ ] Ajustar `dicto.spec` / `installer.iss` / `build.yml` a la nueva ruta (mover a `packaging/`) — *pendiente (se hará en Fase 7); fuentes en `Antiguo/`*
- [x] `core/state.py`: `AppState` (idle/recording/paused/processing/success/error) + `RecordingSession`
- [x] `core/events.py`: bus de eventos tipado (desacopla core de Qt)
- [x] `core/models.py`: dataclasses `Transcript`, `TransformResult`, `DictTerm`, `Job`, `Account`, `Plan`
- [x] `app.py`: `DictoApp` que arranca Qt, inyecta dependencias y conecta señales
- [x] `utils/logger.py` + `utils/platform.py` (rutas `%APPDATA%\dicto\`) portados
- [x] **Tema (transversal):** `ui/theme/tokens.py` + `palettes.py` (light/dark) + `ThemeManager`
      que aplica QSS desde tokens, emite `themeChanged` y soporta modo **claro/oscuro/sistema**
      (detecta el tema de Windows). Persistido en `Settings`. Todo widget consume tokens, nada hardcodea color.
- [x] **i18n (transversal):** `i18n/` con `t()` + loader de locales y señal `languageChanged`.
      Convención de claves desde el primer widget (nada de texto literal en la UI).
- [x] App arranca, muestra bandeja + ventana vacía, sin funcionalidad aún, **ya con tema e i18n vivos**
- [x] **Check:** `python -m dicto` abre la app; cambiar tema (claro/oscuro/sistema) e idioma
      en caliente refresca la UI vacía; `pytest tests/unit/test_state.py tests/unit/test_theme.py tests/unit/test_i18n.py` pasa (25 tests verdes)

### Fase 1 — Fiabilidad en grabaciones largas (lo primero del doc)
- [ ] `audio/devices.py`: enumerar/seleccionar micro (portado de recorder actual)
- [ ] `audio/capture.py` + `audio/session_writer.py`: **stream → chunks a disco**, no RAM
- [ ] `core/chunking.py`: política de tamaño/rotación de chunks
- [ ] `audio/loopback.py`: WASAPI loopback (audio del sistema) como fuente seleccionable
- [ ] `core/vad.py`: VAD para recortar silencios antes de subir (webrtcvad)
- [ ] `services/api/client.py` + `transcribe.py`: cliente httpx con reintentos y errores tipados
- [ ] `core/pipeline.py`: capture→persist→(vad)→transcribe como **jobs reintentables**
- [ ] No perder audio si falla la transcripción → reintento desde el audio en disco
- [ ] Progreso visible + resultados parciales en grabaciones largas
- [ ] **Check:** grabar 60+ min sin reventar RAM; matar la red a mitad y reintentar OK;
      `pytest tests/unit/test_chunking.py tests/unit/test_vad.py tests/integration/test_long_recording.py`

### Fase 2 — Overlay + captura (hotkey, pausa, onda)
- [ ] `services/hotkey.py`: listener global robusto, modos hold y toggle (portado y endurecido)
- [ ] `ui/overlay/overlay.py` + `waveform.py` + `controls.py`: overlay efímero arrastrable
- [ ] **Pausa** de grabación (descansos de clase sin partir el archivo)
- [ ] Temporizador + estado + botón parar en el overlay
- [ ] `audio/monitor.py` + panel de prueba de micro con onda en vivo
- [ ] `ui/tray.py`: icono con color de estado (listo/grabando/procesando/error) + menú
- [ ] **Check:** hold y toggle no se cortan a mitad de frase; pausa/reanuda; overlay arrastrable
      recuerda posición; `pytest tests/unit/test_hotkey.py tests/ui/test_overlay.py`

### Fase 3 — Salida (insertar en cursor, limpieza, export)
- [ ] `services/injector.py`: insertar en el cursor por defecto + auto-enter opcional
- [ ] `services/clipboard.py`: portapapeles como fallback
- [ ] `core/result_router.py`: decide cursor vs portapapeles vs biblioteca
- [ ] `core/cleanup.py`: limpieza activada por defecto en dictado (muletillas, puntuación)
- [ ] Exportar txt / md desde el detalle
- [ ] **Check:** dictado rápido → texto pegado en el cursor con limpieza; fallback a portapapeles
      donde no se puede inyectar; `pytest tests/unit/test_cleanup.py tests/unit/test_result_router.py`

### Fase 4 — Biblioteca + diccionario propio (vía API mock)
- [ ] `services/api/library.py` + `mocks.py`: CRUD + búsqueda (mockeado)
- [ ] `services/api/dictionary.py`: términos/siglas/nombres (mockeado)
- [ ] `core/dictionary.py`: aplicar diccionario como biasing/prompt al transcribir
- [ ] `ui/main/window.py`: contenedor de las 3 zonas (biblioteca/detalle/ajustes)
- [ ] `ui/main/library_view.py`: lista buscable, ordenable por fecha, etiquetas/asignatura
- [ ] `ui/main/detail_view.py`: ver/editar texto, exportar, copiar
- [ ] Guardar toda transcripción automáticamente (no efímera)
- [ ] **Check:** transcribir → aparece en biblioteca; buscar; etiquetar; diccionario mejora jerga;
      `pytest tests/unit/test_dictionary.py tests/integration/test_library_flow.py`

### Fase 5 — Transformar (IA) para estudiantes
- [ ] `transform/presets.py`: resumen, puntos clave, flashcards/preguntas, reescribir, chat
- [ ] `transform/schema.py`: preset → request de `/transform`
- [ ] `services/api/transform.py`: llamada + manejo de errores
- [ ] Caché de resultados de transform (vía API mock `transforms/{id}`)
- [ ] Prompt personalizado
- [ ] `ui/main/detail_view.py`: pestañas de transform por preset
- [ ] `ui/main/chat_view.py`: "pregúntale a tus apuntes"
- [ ] **Check:** cada preset devuelve resultado y se cachea; chat responde sobre la transcripción;
      `pytest tests/integration/test_transform_flow.py`

### Fase 6 — Sistema: cuenta, planes, auto-update, errores, apariencia
- [ ] `services/api/account.py` (mock): plan, minutos incluidos, minutos usados
- [ ] `ui/settings/account.py`: cuenta + API key + estado del plan + uso de minutos
- [ ] `services/updater.py`: auto-update Windows in-place (portado y verificado)
- [ ] `utils/errors.py` + `ui/settings/about.py`: ver/copiar/enviar log (bug report)
- [ ] `i18n/locales/`: completar en, es, de, fr, pt (infra ya creada en Fase 0)
- [ ] `ui/settings/appearance.py`: panel de **tema (claro/oscuro/sistema) + idioma**
      (sobre el `ThemeManager` e `i18n` de Fase 0)
- [ ] `ui/settings/privacy.py`: panel **"Datos y privacidad"** (qué se guarda, qué pasa con el audio)
- [ ] `ui/main/settings_modal.py` + paneles: todos los ajustes como modal en la principal
- [ ] **Check:** auto-update detecta versión nueva e instala; bug report se envía; cambiar idioma
      y tema en caliente desde el panel de apariencia; `pytest tests/unit/test_updater.py tests/unit/test_i18n.py`

### Fase 7 — Empaquetado y release
- [ ] Verificar `dicto.spec` con la nueva estructura (`--copy-metadata dicto`, assets, i18n)
- [ ] `installer.iss` instala y arranca el .exe sin Python
- [ ] `build.yml`: CI construye instalador `Dicto-<ver>-setup.exe`
- [ ] Política de datos visible en la app (qué pasa con el audio)
- [ ] **Check:** instalar el .exe en una Windows limpia y completar un dictado de punta a punta

---

## Notas de migración (qué se reaprovecha del código actual)

| Código actual | Destino | Estado |
|---|---|---|
| `src/services/recorder.py` | `audio/devices.py` + `audio/capture.py` + `audio/monitor.py` | refactor (añadir chunks a disco) |
| `src/services/hotkey.py` | `services/hotkey.py` | portar casi tal cual |
| `src/services/transcriber.py` | `services/api/client.py` + `transcribe.py` + `transform.py` | dividir por endpoint |
| `src/services/keyboard_actions.py` | `services/injector.py` | renombrar |
| `src/services/clipboard.py` | `services/clipboard.py` | portar |
| `src/services/updater.py` | `services/updater.py` | portar |
| `src/controller.py` | `core/pipeline.py` + `core/state.py` + `app.py` | romper en capas |
| `src/ui/overlay.py` + `waveform.py` | `ui/overlay/*` | portar + añadir pausa |
| `src/ui/tray.py` | `ui/tray.py` | portar |
| `src/ui/main_window*.py` (7 ficheros) | `ui/main/*` + `ui/settings/*` | reescribir (3 zonas + modal) |
| `src/config/settings.py` | `config/settings.py` + `defaults.py` | migrar a pydantic (+ campos `theme`, `language`) |
| `src/i18n/translations.py` | `i18n/locales/*.json` + `i18n/__init__.py` | extraer a JSON + señal `languageChanged` |
| (estilos QSS sueltos actuales) | `ui/theme/{manager,tokens,palettes}.py` | reescribir a tokens + light/dark + seguir al SO |
