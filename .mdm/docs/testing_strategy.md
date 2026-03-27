# Estrategia de Testing

## Objetivo

Definir los tipos de tests necesarios para poder sacar nuevas versiones de Dicto Desktop con confianza, detectando regresiones antes de que lleguen al usuario.

---

## 1. Unit Tests

Tests rápidos, aislados, sin dependencias externas. Son la base de la pirámide.

### Qué testear

| Componente | Ejemplos de tests |
|---|---|
| `Settings` | Carga correcta de `config.yaml`, valores por defecto cuando falta una key, override con env vars, `save()` persiste cambios, `get_app_dir()` en modo frozen vs script |
| `AppState` (enum + transiciones) | Que el Controller transiciona correctamente entre estados (idle → recording → processing → success/error → idle) |
| `Controller` (lógica pura) | `cancel()` en cada estado, flag `_cancelled` descarta resultados, timer de éxito vuelve a idle |
| `Transcriber` | Parseo de respuestas de la API, manejo de errores (`TranscriptionError`, `APIKeyError`), construcción correcta del request |
| `AudioRecorder` | Callback de nivel de audio normaliza a 0.0-1.0, genera archivo WAV válido |
| `ClipboardManager` | Copia texto correctamente (mock de pyperclip) |
| `HotkeyListener` | Modo "hold" emite on_press/on_release, modo "press" solo emite on_press, parseo de combinaciones de teclas |
| `i18n` | `t(key)` devuelve traducción correcta, `set_language()` cambia idioma, keys faltantes no crashean |
| `icons.py` / `SVG loader` | Cache funciona, archivos inexistentes no crashean |

### Cómo mockear

- **API calls**: mock de `requests.post` (o el cliente HTTP que uses)
- **Audio hardware**: mock de `sounddevice` — no necesitás micrófono real
- **Clipboard**: mock de `pyperclip`
- **Keyboard/hotkeys**: mock de `pynput`
- **Qt signals**: usar `QSignalSpy` o simplemente conectar a un slot que guarde los valores emitidos

### Herramientas

- `pytest` + `pytest-qt` (para signals y widgets básicos)
- `unittest.mock` / `pytest-mock`

---

## 2. Integration Tests

Verifican que los componentes se comunican correctamente entre sí.

### Qué testear

| Flujo | Qué verificar |
|---|---|
| **Recording flow completo** | HotkeyListener → Controller.start → Recorder → Controller.stop → Transcriber (mockeado) → Clipboard. Verificar que las señales se emiten en orden y el estado transiciona correctamente |
| **Edit selection flow** | Hotkey press → copy simulado → recording → transcription → transform API → clipboard. Verificar toda la cadena |
| **Cancel durante recording** | Que se limpia el archivo temporal y se vuelve a idle |
| **Cancel durante processing** | Que el resultado se descarta cuando llega |
| **Settings ↔ Controller** | Cambiar hotkey en settings → Controller recrea el HotkeyListener con la nueva combinación |
| **Settings ↔ UI** | Cambiar un setting → UI refleja el cambio (y viceversa) |

### Cómo

- Instanciar los componentes reales (Controller, Settings, etc.) pero mockear las boundaries (API, audio hardware, clipboard, keyboard)
- Usar `pytest-qt` con `qtbot` para el event loop de Qt

---

## 3. UI Tests

Verifican que la interfaz se comporta correctamente.

### Qué testear

| Componente | Qué verificar |
|---|---|
| **MainWindow** | Botón record cambia label según estado (Record/Stop/Cancel), tabs se habilitan/deshabilitan según hay transcripción, panel de settings se abre/cierra |
| **MainWindow settings** | HotkeyButton entra en modo escucha, captura combinación, Escape cancela |
| **OverlayWindow** | Se muestra al grabar, cambia waveform mode según estado, se oculta tras success/error |
| **WaveformWidget** | Modos (live/wave/pulse/settle) renderizan sin crash, `set_level()` actualiza |
| **Panel protection** | Estar en settings durante recording no cambia la vista, pero al cerrar muestra el resultado |
| **TrayManager** | Menú contextual tiene las opciones correctas, click abre ventana |

### Herramientas

- `pytest-qt` con `qtbot.addWidget()` para instanciar widgets aislados
- Simular clicks y keypresses con `qtbot.mouseClick()`, `qtbot.keyPress()`

---

## 4. API Contract Tests

Verifican que la comunicación con el Dicto API no se rompe.

### Qué testear

- Request de transcripción: formato correcto (multipart con archivo WAV, headers, modelo)
- Request de transform: body correcto (texto + instrucciones + modelo)
- Request de edit: body correcto
- Responses: parseo correcto de respuestas exitosas y de error (4xx, 5xx, timeout, JSON inválido)

### Cómo

- Fixtures con payloads reales grabados (responses guardados en archivos JSON)
- Mock del HTTP client para verificar que se construye el request correcto
- Opcionalmente: un test que corre contra la API real (marcado como `@pytest.mark.api`) para verificar compatibilidad antes de un release

---

## 5. Config / Persistence Tests

### Qué testear

- `config.yaml` corrupto o vacío → la app arranca con defaults
- `config.yaml` con keys extra (forward compatibility) → no crashea
- `config.yaml` con keys faltantes → usa defaults
- `.env` faltante → la app informa claramente que falta la API key
- `save()` en settings → el YAML resultante es válido y contiene los valores correctos

---

## 6. Smoke / E2E Tests (opcional pero recomendado)

Un test que levanta la app completa (con mocks de hardware y API) y verifica el happy path:

1. App arranca sin crash
2. MainWindow es visible
3. Simular hotkey → estado pasa a recording
4. Soltar hotkey → estado pasa a processing
5. Mock de API responde → texto aparece en transcripción, clipboard tiene el texto

### Herramientas

- `pytest-qt` levantando `DictoApp` con mocks inyectados
- Timeout corto para que no bloquee CI

---

## Estructura de archivos propuesta

```
tests/
├── conftest.py              # Fixtures compartidos (settings mock, qtbot config)
├── unit/
│   ├── test_settings.py
│   ├── test_controller.py
│   ├── test_transcriber.py
│   ├── test_recorder.py
│   ├── test_clipboard.py
│   ├── test_hotkey.py
│   └── test_i18n.py
├── integration/
│   ├── test_recording_flow.py
│   ├── test_edit_flow.py
│   ├── test_cancel_flow.py
│   └── test_settings_sync.py
├── ui/
│   ├── test_main_window.py
│   ├── test_overlay.py
│   └── test_waveform.py
├── api/
│   ├── test_api_contracts.py
│   └── fixtures/            # Responses grabados
│       ├── transcribe_success.json
│       └── transcribe_error.json
└── e2e/
    └── test_smoke.py
```

---

## Prioridad de implementación

Si partís de cero, este es el orden que más confianza te da por esfuerzo invertido:

1. **Unit tests de Settings** — es lo más fácil y protege contra regresiones de config
2. **Unit tests de Controller** (transiciones de estado, cancel) — es el corazón de la app
3. **API contract tests de Transcriber** — protege contra cambios en la API
4. **Integration test del recording flow** — el happy path más importante
5. **UI tests de MainWindow** (estado del botón, tabs) — previene regresiones visuales
6. **Integration test del edit flow** — segundo flujo más importante
7. **Smoke test E2E** — red de seguridad final
8. **El resto** — completar cobertura según donde aparezcan bugs

---

## Configuración base

```toml
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
    "api: tests that hit the real API (deselect with -m 'not api')",
    "e2e: end-to-end smoke tests",
]
qt_api = "pyside6"
```

```txt
# requirements-dev.txt (o en pyproject.toml extras)
pytest
pytest-qt
pytest-mock
pytest-cov
```

---

## En CI

```yaml
# Ejemplo para GitHub Actions
- run: pytest -m "not api" --cov=src --cov-report=term-missing
```

Correr todo menos los tests de API real. Los tests de API real se pueden correr manualmente antes de un release o en un workflow separado con la API key como secret.
