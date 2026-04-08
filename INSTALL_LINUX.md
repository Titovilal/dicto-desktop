# Instalación en Linux

Guía para instalar y ejecutar Dicto Desktop en distribuciones Linux basadas en Ubuntu/Debian.

> **Requisito**: Se necesita **X11** (no Wayland). La captura de hotkeys globales y la simulación de teclado no funcionan en Wayland por restricciones de seguridad del protocolo. La mayoría de distros LTS permiten seleccionar X11 en la pantalla de login.

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
- Verificar que estás en sesión **X11**, no Wayland:
  ```bash
  echo $XDG_SESSION_TYPE
  # Debe mostrar "x11"
  ```
- Si muestra "wayland", cerrar sesión y seleccionar "Ubuntu on Xorg" (o equivalente) en la pantalla de login.

### Error "qt.qpa.plugin: Could not load the Qt platform plugin"
```bash
sudo apt install libxcb-xinerama0 libxcb-cursor0 libegl1
```

### Error al importar PySide6
```bash
# Instalar dependencias adicionales de Qt
sudo apt install libgl1-mesa-glx libegl1
```
