# Dicto — Resumen de funcionalidades

App de escritorio para transcripción de voz a texto mediante un atajo global.
Grabas con un atajo, Dicto transcribe el audio vía API y copia el resultado al
portapapeles. Construida con Python + PySide6. Soporta Windows y Linux (X11 y
Wayland).

## Flujo principal

1. **Grabar** — mantén pulsado el atajo (por defecto `Ctrl+Shift+Space`).
2. **Transcribir** — al soltar, el audio se envía a la API y se transcribe.
3. **Copiar** — el texto resultante se copia automáticamente al portapapeles.
4. **(Opcional) Transformar** — aplica un preset o un prompt propio al texto.
5. **(Opcional) Auto-pegar / Auto-enter** — pega el texto en la app enfocada.

Estados de la app: `IDLE → RECORDING → PROCESSING → SUCCESS/ERROR → IDLE`.

## Grabación

- **Atajo global** para iniciar/parar. En Windows/X11 el modo es configurable en
  Ajustes (`behavior.recording_mode`): *hold* (mantener pulsado para grabar,
  defecto) o *toggle* (pulsar para iniciar, pulsar de nuevo para parar). En
  Wayland siempre es *toggle* (limitación del portal).
- **Selección de micrófono** en Ajustes → Audio, con botón de prueba y forma de
  onda en vivo.
- **Captura de audio del sistema** (solo Windows): mezcla el audio del sistema
  con el micrófono vía WASAPI loopback, con *Stereo Mix* como alternativa.
- **Visualización**: forma de onda en vivo y temporizador durante la grabación,
  tanto en la ventana principal como en el overlay flotante.

Config de audio (`config.yaml`):

| Clave | Defecto | Descripción |
|-------|---------|-------------|
| `audio.sample_rate` | `16000` | Frecuencia de muestreo (Hz) |
| `audio.max_duration` | `7200` | Duración máxima (s) — 2 horas |
| `audio.channels` | `1` | Canales (mono) |
| `audio.input_device` | `null` | Micrófono (null = predeterminado) |
| `audio.include_system_audio` | `false` | Capturar audio del sistema (Windows) |

## Transcripción

- **Modelos** (Ajustes → Models): `v3-turbo` (rápido, por defecto) y `v3`
  (más preciso). Clave: `transcription.model`.
- **Idioma** de transcripción: auto-detección o un idioma concreto. Clave:
  `transcription.language` (defecto `es`).

## Transformación de texto y presets

- **Presets**: se descargan de la API al arrancar; los favoritos aparecen como
  pestañas junto a "Original".
- **Prompt personalizado**: escribe instrucciones y pulsa Aplicar.
- La transformación usa un modelo LLM configurable
  (`transformation.model`, defecto `qwen/qwen3-32b`).
- Resultados cacheados (LRU) para no recalcular.

## Auto-pegar y auto-enter

- `behavior.auto_paste` (defecto `false`): pega el texto (`Ctrl+V`) tras
  transcribir.
- `behavior.auto_enter` (defecto `false`): pulsa Enter tras pegar (requiere
  auto-paste).
- Implementación por plataforma: pynput en Windows/X11; en Wayland se usa
  `ydotool` (requiere `ydotoold`) o `xdotool`.

## Atajos de teclado

- **Atajo de grabación** configurable en Ajustes. Defecto: `Ctrl+Shift+Space`
  (`hotkey.modifiers` = `["ctrl","shift"]`, `hotkey.key` = `"space"`).
- Modificadores admitidos: `ctrl`, `shift`, `alt`, `cmd` (con variantes L/R).
- **Modo de grabación** (`behavior.recording_mode`, defecto `hold`): elige entre
  *hold* (mantener) o *toggle* (pulsar para activar/desactivar) en Ajustes. Solo
  aplica a Windows/X11; Wayland es siempre *toggle*.
- **Windows / Linux X11**: listener global vía pynput (modo *hold* o *toggle*).
- **Linux Wayland**: portal XDG GlobalShortcuts vía D-Bus (siempre *toggle*;
  requiere `dbus-next`). El compositor puede pedir confirmación del atajo.
- **Degradación elegante**: si no hay atajos disponibles, la grabación por
  botón en la GUI sigue funcionando.

## Overlay flotante

Ventana pequeña, siempre visible, que muestra el estado: grabando, transcribiendo,
copiado (✓) o error. Arrastrable, con un popover de ajustes (resetear posición,
ocultar, abrir la app).

| Clave | Defecto | Opciones |
|-------|---------|----------|
| `overlay.position` | `top-right` | `top-left`, `top-right`, `bottom-left`, `bottom-right`, `center` |
| `overlay.size` | `100` | tamaño en píxeles |
| `overlay.opacity` | `0.9` | `0.0`–`1.0` |
| `behavior.persistent_overlay` | `false` | overlay siempre visible |

## Ventana principal

- Sin marco, arrastrable por la cabecera, tamaño fijo.
- Cabecera: punto de estado de color, título, botón web, temporizador, Models,
  pin (siempre encima), ajustes, cerrar.
- Páginas: inicio, grabación, resultado (con pestañas de formato), ajustes,
  modelos.
- Barra de formato (cuando hay transcripción): desplegable de presets + prompt
  personalizado.
- `behavior.always_on_top` (defecto `false`): mantener la ventana encima.

## Bandeja del sistema (system tray)

- Menú: Abrir Dicto · Ajustes · Salir.
- El icono cambia de color según el estado (verde = listo, rojo = grabando/error,
  ámbar = procesando) y el tooltip muestra el estado actual.
- La app sigue en la bandeja al cerrar la ventana; se sale desde el menú.

## Idiomas de la interfaz

Inglés (`en`), Español (`es`, por defecto), Alemán (`de`), Francés (`fr`) y
Portugués (`pt`). Se cambia en Ajustes; clave `ui_language`.

## Auto-actualización (Windows y Linux)

- Comprueba la última *release* en GitHub (Ajustes → Updates).
- En builds *frozen*, descarga e instala la nueva versión en el sitio:
  - **Windows**: descarga el instalador `Dicto-<ver>-setup.exe` (Inno Setup), lo
    ejecuta en modo silencioso y cierra la app para que el instalador reemplace
    los ficheros y la **relance automáticamente** al terminar. Puede aparecer el
    aviso de UAC si la instalación es para todos los usuarios.
  - **Linux**: descarga el `.deb` de la release y lo instala vía
    `pkexec apt-get install` (autenticación por PolicyKit). Tras instalar, la app
    ofrece reiniciarse.
- Si no es posible instalar en el sitio (p. ej. el `.tar.gz` portable), el botón
  abre la página de la release para descargarla a mano.
- Clave repo: env `DICTO_UPDATE_REPO` (defecto `Titovilal/dicto-desktop`).

## Reporte de errores

Ajustes → Report Error: ver el log en memoria, copiarlo o enviarlo a la API para
diagnóstico.

## Integración con la API

Base: `https://dicto.up.railway.app` (override con `DICTO_API_URL`).

| Endpoint | Método | Uso |
|----------|--------|-----|
| `/api/v1/transcribe` | POST | Transcribir un archivo de audio |
| `/api/v1/transform` | POST | Transformar texto vía LLM |
| `/api/v1/presets` | GET | Obtener presets favoritos |
| `/api/v1/report` | POST | Enviar logs de diagnóstico |

- **API key** obligatoria (formato `sk-dicto-*`). Se valida al guardar.
- Errores: `401` → clave inválida; `429` → límite de uso (reintenta con backoff
  exponencial); resto → error genérico.

## Variables de entorno

| Variable | Descripción |
|----------|-------------|
| `DICTO_API_KEY` | Sobrescribe la API key |
| `DICTO_API_URL` | Base de la API |
| `DICTO_WEB_URL` | URL de la web |
| `DICTO_UPDATE_REPO` | Repo de GitHub para updates |
| `GITHUB_TOKEN` | Token opcional para subir el límite de rate de GitHub |

## Ubicación de la configuración

- **Desarrollo**: `config.yaml` en la raíz del proyecto.
- **Windows (frozen)**: `%APPDATA%\dicto\config.yaml`.
- **Linux (frozen)**: `$XDG_CONFIG_HOME/dicto/config.yaml` (o `~/.config/dicto/`).

La configuración antigua junto al ejecutable se migra automáticamente al primer
arranque.

## Diferencias por plataforma

| Funcionalidad | Windows | Linux X11 | Linux Wayland |
|---------------|---------|-----------|---------------|
| Atajo global | pynput (hold/toggle) | pynput (hold/toggle) | portal XDG (toggle) |
| Audio del sistema | ✅ WASAPI | ❌ | ❌ |
| Auto-pegar | pynput | pynput | ydotool / xdotool |
| Portapapeles | win32clipboard | pyperclip | pyperclip |
| Auto-actualización | ✅ (setup.exe) | ✅ (.deb) | ✅ (.deb) |
