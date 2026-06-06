# Fase 2 — Overlay + captura (hotkey, pausa, onda) ✅

La UI de grabación enchufa el `Pipeline` de Fase 1: un **atajo global** dispara la
captura, un **overlay efímero** muestra onda en vivo + temporizador + pausa/parar,
y la bandeja sigue el estado. Toda la orquestación vive en un único `RecordingOrchestrator`
(capa app) que mantiene el `core` puro y cruza el bus de eventos a señales Qt.

## Estructura nueva en `src/dicto/`

```
services/hotkey.py     HotkeyMatcher (puro: hold/toggle, traga auto-repeat, normaliza L/R) +
                       HotkeyListener (backend pynput inyectado, headless-safe)
audio/monitor.py       AudioMonitor: nivel de micro en vivo para el test, NO escribe a disco
orchestrator.py        RecordingOrchestrator (QObject): ciclo de vida de la grabación,
                       transcribe en hilo worker, bus de dominio → señales Qt
ui/overlay/overlay.py  Overlay: tarjeta sin marco, always-on-top, arrastrable; refleja
                       AppState; recuerda su posición en Settings; emite intención
ui/overlay/waveform.py WaveformWidget: barras coloreadas por token (live/pulse/settle),
                       repinta en themeChanged
ui/overlay/controls.py OverlayControls: temporizador (format_elapsed) + pausa/parar
ui/settings/audio.py   MicTestPanel: selector de micro + prueba en vivo con onda
ui/icons.py            svg_icon(): recolorea glifos SVG de acción a un token de tema
assets/icons/svg/      record · stop · pause · settings_small · reset · close · external · mic
```

**Principios:** el overlay es **solo visual** (emite intención, nunca toca audio) ·
color por tokens, nada hardcodeado · el matcher de atajos es **puro** (testeable sin
pynput) · la transcripción corre fuera del hilo Qt; el bus se puentea con señales.

## Flujo

1. Atajo (hold o toggle) → `RecordingOrchestrator.toggle/start/stop`.
2. `start` crea `AudioCapture` + `Pipeline`, arranca captura → estado RECORDING →
   overlay visible con onda en vivo (nivel RMS) + temporizador; bandeja roja.
3. **Pausa/reanuda** sin partir el fichero (la captura descarta bloques en pausa).
4. `stop` cierra chunks y transcribe en hilo worker; progreso por chunk y texto final
   llegan por el bus → señales → UI. Entrega mínima: copia al portapapeles (Fase 3
   pondrá el `result_router` + limpieza).

## Verificado

- App arranca, atajo global activo, overlay oculto hasta grabar; cierre/dispose limpio.
- Overlay: aparece al grabar, arrastrable, **recuerda posición** (Settings), "reset" la borra.
- Pausa→reanuda emite intención correcta; parar dispara stop.
- Bus `TranscriptionDone` → estado SUCCESS en hilo principal (puente verificado).
- **19 tests nuevos** (78 en total): `pytest tests/unit/test_hotkey.py tests/ui/test_overlay.py`
  (9 matcher puro: hold/toggle, auto-repeat, L/R, callbacks; 10 overlay: visibilidad,
  posición, pausa/parar, estados + `format_elapsed`).
- `ruff` limpio en todos los ficheros nuevos; `mypy` sin errores reales (solo
  import-untyped de pynput/sounddevice, igual que Fase 1).

## Pendiente

- Suprimir el atajo para que no llegue a otras apps (win32 filter) → endurecer si molesta.
- Inyección en cursor / portapapeles como fallback / limpieza → **Fase 3**.
- Panel de ajustes que aloje `MicTestPanel` (el widget ya existe) → **Fase 6** (modal).
- `dicto.spec` / `installer.iss` / `build.yml` → **Fase 7** (incluir `assets/icons/svg/`).
