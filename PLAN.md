# Dicto Desktop — Plan de Reescritura en Tauri + React

## Stack
- **Framework:** Tauri 2.x
- **Frontend:** React + TypeScript + Vite
- **Styling:** Tailwind CSS
- **i18n:** i18next (ES / EN / DE)
- **Audio:** Rust crate `cpal` para captura de audio
- **Hotkeys:** Tauri plugin `global-shortcut`
- **Tray:** Tauri plugin `tray-icon`
- **Clipboard:** Tauri plugin `clipboard-manager`
- **Config:** Tauri plugin `store` (JSON persistente)
- **HTTP:** Tauri plugin `http` (reqwest backend)
- **Plataformas:** Windows, macOS, Linux

---

## Fase 1 — Scaffold + Configuración base
> Objetivo: proyecto Tauri+React corriendo, config persistente, i18n, estructura de carpetas.

- [ ] Crear proyecto con `create-tauri-app` (React + TypeScript)
- [ ] Configurar Tailwind CSS
- [ ] Instalar y configurar i18next con los tres idiomas (ES/EN/DE)
- [ ] Instalar plugins Tauri: `store`, `global-shortcut`, `clipboard-manager`, `tray-icon`, `http`
- [ ] Definir estructura de carpetas del frontend (`components/`, `hooks/`, `store/`, `i18n/`, `types/`)
- [ ] Crear tipos TypeScript globales (`AppState`, `AppConfig`, `TranscriptionModel`, etc.)
- [ ] Configurar Tauri store para persistir configuración (API key, hotkeys, idioma, etc.)
- [ ] Crear hook `useConfig` para leer/escribir configuración
- [ ] Página de Settings básica (sólo API key + idioma + hotkey por ahora)
- [ ] Verificar que compila y corre en los tres SO

**Entregable:** `npm run tauri dev` funciona, config persiste, i18n cambia idioma.

---

## Fase 2A — Grabación de audio + Transcripción (Rust backend)
> Objetivo: capturar audio con cpal y enviar a la API Dicto.

- [ ] Crate Rust para captura de audio con `cpal` (micrófono)
- [ ] Grabación start/stop desde comandos Tauri
- [ ] Monitoreo de nivel de audio en tiempo real (emit eventos al frontend)
- [ ] Codificación a WAV/WebM para envío
- [ ] Comando Tauri `transcribe` — envía audio a `/api/transcribe` con API key
- [ ] Manejo de errores específicos (APIKey, RateLimit, AudioTooShort, AudioTooLong, Network)
- [ ] Reintentos automáticos (3 intentos, backoff exponencial)
- [ ] Copiar resultado al portapapeles automáticamente
- [ ] Auto-paste (Ctrl+V simulado) y auto-enter opcionales

**Entregable:** se graba, transcribe y pega el texto en cualquier app.

## Fase 2B — Hotkeys globales + Sistema tray (paralela con 2A)
> Objetivo: hotkey de grabación funcional y tray con estados visuales.

- [ ] Registrar hotkey global configurable para grabar (default: Ctrl+Shift+Space)
- [ ] Hotkey separado para edición (default: Ctrl+Alt+Space)
- [ ] Cambiar hotkeys desde Settings sin reiniciar
- [ ] Icono en bandeja del sistema con estados (idle / recording / processing / error)
- [ ] Menú contextual en tray (Abrir, Grabar, Salir)
- [ ] Notificaciones del sistema para errores

**Entregable:** hotkeys funcionan globalmente, tray muestra estado.

---

## Fase 3A — Overlay flotante (paralela con 3B)
> Objetivo: ventana overlay draggable con estado visual.

- [ ] Ventana overlay secundaria (frameless, always-on-top, transparente)
- [ ] Mostrar estado actual (idle / recording / processing / success / error)
- [ ] Waveform animado en tiempo real durante grabación
- [ ] Overlay draggable (guardar posición en config)
- [ ] Modo "persistent overlay" (siempre visible)
- [ ] Botones de control en overlay (Grabar / Parar)
- [ ] Popover con opciones rápidas (resetear posición, ocultar overlay, abrir app)

**Entregable:** overlay aparece al grabar, se puede mover y persiste posición.

## Fase 3B — Feature Edit por voz (paralela con 3A)
> Objetivo: flujo de edición de texto seleccionado via voz.

- [ ] Hotkey de edición: capturar texto seleccionado (Ctrl+C simulado)
- [ ] Grabar instrucción de voz
- [ ] Transcribir instrucción
- [ ] Enviar texto + instrucción a `/api/edit`
- [ ] Pegar resultado automáticamente
- [ ] Auto-paste y auto-enter para edición
- [ ] Estado visual "Editing" en overlay y tray

**Entregable:** seleccionar texto → hotkey → hablar → texto editado pegado.

---

## Fase 4 — Presets + Transformaciones
> Objetivo: cargar presets desde API y aplicar transformaciones.

- [ ] Llamada a API para cargar presets favoritos del usuario
- [ ] UI de presets en ventana principal (tab Presets)
- [ ] Aplicar preset a última transcripción
- [ ] Instrucciones de transformación personalizadas (system prompts)
- [ ] Modelo configurable para transformaciones
- [ ] Envío a `/api/transform` con transcription ID

**Entregable:** presets cargados y aplicables desde la UI.

---

## Fase 5 — UI principal completa + Pulido final
> Objetivo: ventana principal completa, selección de dispositivo, test de micro.

- [ ] Ventana principal con tabs: Transcripción / Presets / Ajustes
- [ ] Tab Ajustes completo: hotkeys, modelos, overlay, idioma, API key, auto-paste
- [ ] Selección de dispositivo de micrófono
- [ ] Captura de audio del sistema (sólo Windows — WASAPI loopback)
- [ ] Test de micrófono con waveform
- [ ] Splash screen de carga
- [ ] Opción always-on-top para ventana principal
- [ ] Reporte de errores/logs a la API
- [ ] Iconos, branding, assets finales
- [ ] Build de producción verificado en Windows, macOS y Linux

**Entregable:** aplicación completa, pulida y distribuible.

---

## Resumen de fases

```
Fase 1  ────────────────────────────────────────────► scaffold + config + i18n
Fase 2A ─────────────────────────────────────────────► audio + transcripción     ┐ paralelas
Fase 2B ─────────────────────────────────────────────► hotkeys + tray            ┘
Fase 3A ─────────────────────────────────────────────► overlay flotante           ┐ paralelas
Fase 3B ─────────────────────────────────────────────► feature edit               ┘
Fase 4  ────────────────────────────────────────────► presets + transformaciones
Fase 5  ────────────────────────────────────────────► UI completa + build final
```
