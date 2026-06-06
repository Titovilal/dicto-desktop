# Fase 1 — Fiabilidad en grabaciones largas ✅

El audio es el **dato sagrado**: se graba a disco en chunks acotados (nunca entero
en RAM) y la transcripción son *jobs reintentables* sobre esos ficheros.

## Estructura nueva en `src/dicto/`

```
core/chunking.py    ChunkPolicy: rota chunk a 5 min / 20 MB (contadores puros, sin I/O)
core/vad.py         trim_silence con webrtcvad; ante cualquier error devuelve el audio intacto
core/pipeline.py    Pipeline: 1 Job reintentable por chunk; captura y red INYECTADAS (core puro)
audio/devices.py    enumerar micro + negociar sample rate + descubrir loopback WASAPI
audio/session_writer.py  escribe int16 PCM a chunks WAV rotatorios (stdlib wave)
audio/capture.py    AudioCapture: stream sounddevice (hilo) → resample → writer; pausa/nivel
audio/loopback.py   LoopbackCapture: audio del sistema (soundcard / Stereo Mix)
services/api/       client (httpx, reintentos+backoff) · errors (tipados, retryable) ·
                    transcribe (1 chunk → texto) · routes · factory (arma el callable de STT)
```

**Principios:** core sin Qt/red/SO (efectos inyectados) · cada chunk es un WAV válido
independiente · fallos *retryable* (red/429/5xx) reintentan; *terminales* (auth/quota) cortan ya.

## Flujo

1. `AudioCapture` graba el micro a disco; `SessionWriter` rota chunks según `ChunkPolicy`.
2. `Pipeline.stop()` cierra los chunks y crea un `Job` por fichero.
3. `Pipeline.transcribe()` transcribe en orden vía `services/api`, reintenta desde disco
   si falla la red, emite `TranscriptionProgress` (texto parcial) y `TranscriptionDone`.

## Verificado

- Grabación simulada de **63 min** → ~13 chunks acotados (RAM acotada, ningún fichero gigante).
- Fallo de red a mitad → el audio sigue en disco y `retry_failed()` lo recupera.
- Progreso + resultados parciales por chunk en grabaciones largas.
- **34 tests verdes Fase 1** (59 en total):
  `pytest tests/unit/{test_chunking,test_vad,test_session_writer,test_api_client}.py tests/integration/test_long_recording.py`

## Dependencias

- `webrtcvad-wheels` (wheel precompilada, sin compilador C) + `numpy` añadidas a `pyproject.toml`.

## Pendiente

- UI de grabación (botón / overlay que dispara el `Pipeline`) → **Fase 2** (el pipeline ya
  acepta efectos inyectados, así que enchufa limpio).
- `dicto.spec` / `installer.iss` / `build.yml` → Fase 7 (fuentes en `Antiguo/`).
