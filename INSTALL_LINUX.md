# Instalación en Linux

Guía para instalar y ejecutar Dicto Desktop en distribuciones Linux basadas en Ubuntu/Debian.

> **Sesiones soportadas**: funciona tanto en **X11** como en **Wayland**.
>
> - **X11**: atajo global vía pynput, en modo *hold* (mantener pulsado) o
>   *toggle*, configurable en Ajustes. Auto-pegado con pynput.
> - **Wayland**: atajo global vía el portal XDG GlobalShortcuts (D-Bus), siempre
>   en modo *toggle* (pulsar para iniciar, pulsar para parar) por limitación del
>   portal; el compositor puede pedir confirmación del atajo la primera vez. El
>   auto-pegado necesita `ydotool` (con `ydotoold`) o `xdotool` instalados a mano
>   (ver más abajo); sin ellos el texto se copia al portapapeles y se pega con
>   `Ctrl+V`.

---

## 1. Dependencias del sistema

```bash
# Audio (PortAudio para grabación de micrófono)
sudo apt install portaudio19-dev

# Clipboard (pyperclip necesita xclip o xsel)
sudo apt install xclip

# Qt/PySide6 (librerías X11 necesarias)
sudo apt install libxcb-xinerama0 libxcb-cursor0

# Python dev headers (si compilas dependencias nativas)
sudo apt install python3-dev
```

**Fedora:**
```bash
sudo dnf install portaudio-devel xclip python3-devel
```

**Arch:**
```bash
sudo pacman -S portaudio xclip
```

---

## 2. Descargar el binario

Descarga la última versión desde [GitHub Releases](https://github.com/Titovilal/dicto-desktop/releases):

```bash
# Descargar la última release
curl -LO https://github.com/Titovilal/dicto-desktop/releases/latest/download/dicto-linux-amd64

# Dar permisos de ejecución
chmod +x dicto-linux-amd64
```

---

## 3. Configurar

Configura tu API key con variable de entorno:

```bash
export DICTO_API_KEY="tu-api-key"
```

---

## 4. Ejecutar

```bash
./dicto-linux-amd64
```

---

## Notas por entorno de escritorio

| Entorno | System Tray | Notas |
|---|---|---|
| **XFCE** (Xubuntu) | Funciona | Sin configuración extra |
| **KDE** | Funciona | Sin configuración extra |
| **Cinnamon** (Mint) | Funciona | Sin configuración extra |
| **GNOME 42+** | Necesita extensión | Instalar [AppIndicator Support](https://extensions.gnome.org/extension/615/appindicator-support/) |

---

## Troubleshooting

### No se detecta el micrófono
```bash
# Verificar que el mic es visible
arecord -l

# Si no aparece, revisar PulseAudio/PipeWire
pactl list sources short
```

### Clipboard no funciona
```bash
# Verificar que xclip está instalado
which xclip

# Test manual
echo "test" | xclip -selection clipboard
xclip -selection clipboard -o
```

### Hotkey no responde

Comprueba primero qué tipo de sesión usas:
```bash
echo $XDG_SESSION_TYPE   # "x11" o "wayland"
```

- **X11**: el atajo se registra con pynput. Si no responde, comprueba que otra
  app no esté capturando la misma combinación.
- **Wayland**: el atajo se registra por el portal XDG GlobalShortcuts y requiere
  `dbus-next` y un portal activo (`xdg-desktop-portal` + el backend de tu
  escritorio, p. ej. `xdg-desktop-portal-gnome` o `-kde`). El compositor puede
  pedir confirmación del atajo la primera vez: acéptala. En Wayland el modo es
  siempre *toggle* (pulsar para iniciar, pulsar para parar), no *hold*.
- Si no hay atajo disponible, el botón de grabar de la ventana sigue funcionando.

### Auto-pegado no funciona en Wayland

En Wayland la simulación de teclado necesita una herramienta externa que **no
viene incluida en el `.deb`**:
```bash
# Opción A: ydotool (funciona en Wayland nativo)
sudo apt install ydotool
sudo systemctl enable --now ydotoold   # el demonio debe estar en marcha
sudo usermod -aG input $USER           # acceso a /dev/uinput; requiere volver a iniciar sesión

# Opción B: xdotool (más simple, pero solo llega a ventanas XWayland)
sudo apt install xdotool
```
Sin ninguna de las dos, el texto se copia al portapapeles y basta con pegarlo
con `Ctrl+V`. La app avisa cuando falta la herramienta en lugar de fallar en
silencio.

### "App siempre visible" / "Overlay siempre visible" no hacen nada

Wayland no permite que una aplicación normal se coloque por encima de las
demás: la petición sale de la app y el compositor la descarta. Para que
funcione, Dicto arranca a través de **XWayland** (`QT_QPA_PLATFORM=xcb`)
automáticamente cuando alguno de los dos ajustes está activado.

Como la plataforma se elige al arrancar, hay que **reiniciar la app** después de
activar el ajuste por primera vez. Contrapartida: con escalado fraccional
(125 %, 150 %) XWayland puede verse algo menos nítido; con escalado entero
(100 %, 200 %) no hay diferencia. Para forzar Wayland nativo pese al ajuste,
arranca con `QT_QPA_PLATFORM=wayland dicto` — la app respeta esa variable.

### Error "qt.qpa.plugin: Could not load the Qt platform plugin"
```bash
sudo apt install libxcb-xinerama0 libxcb-cursor0 libegl1
```

### Error al importar PySide6
```bash
# Instalar dependencias adicionales de Qt
sudo apt install libgl1-mesa-glx libegl1
```
