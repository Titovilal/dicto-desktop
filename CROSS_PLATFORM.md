# Dicto Desktop - Plan de soporte multiplataforma (Windows + Linux)

Estado actual: la app es **~90% cross-platform**. Las dependencias (PySide6, pynput, sounddevice, pyperclip, httpx) son todas multiplataforma. El CI ya tiene build de Linux. Los cambios necesarios son menores.

---

## Cambios necesarios

### 1. `src/main.py` - AppUserModelID (Windows-only)

```python
# Actual (líneas 15-19)
if sys.platform == "win32":
    import ctypes
    app_id = "dicto.desktop.1.0"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
```

**Estado**: Ya tiene guard `sys.platform == "win32"`. No requiere cambios.

---

### 2. `src/services/hotkey.py` - Filtro de eventos Windows

El método `_win32_filter` usa `data.vkCode` y constantes de mensajes Win32 (`0x0100`, etc.), y se pasa como `win32_event_filter` al listener de pynput.

**Cambio**: Verificar que en Linux, sin el filtro, la supresión de hotkeys funcione correctamente con pynput. pynput en Linux (X11) gestiona la supresión de forma distinta. Posible necesidad de lógica condicional:

```python
if sys.platform == "win32":
    kwargs["win32_event_filter"] = self._win32_filter
# En Linux, pynput maneja suppress nativamente con X11
```

**Riesgo**: En **Wayland**, pynput NO puede capturar hotkeys globales (es una limitación del protocolo de seguridad). Opciones:
- Documentar que se requiere X11 (o XWayland)
- Investigar alternativas como `evdev` o `libinput` para Wayland (futuro)

---

### 3. `src/services/keyboard_actions.py` - Simulación de teclado

Usa `pynput.keyboard.Controller` para simular Ctrl+C, Ctrl+V, Enter.

**Cambio**: Funciona en X11 sin cambios. En **Wayland**, la simulación de teclado está restringida por seguridad. Misma situación que hotkeys: documentar requisito de X11 o buscar alternativa.

---

### 4. `src/services/clipboard.py` - Clipboard

Usa `pyperclip`, que en Linux depende de herramientas del sistema.

**Cambio**: Documentar dependencia de sistema en Linux:
```bash
# Ubuntu/Debian
sudo apt install xclip
# o alternativamente
sudo apt install xsel
```

Sin `xclip` o `xsel` instalado, pyperclip lanza excepción en Linux.

---

### 5. `src/services/recorder.py` - Audio

Usa `sounddevice` + `soundfile`, que dependen de PortAudio.

**Cambio**: Documentar dependencia de sistema:
```bash
# Ubuntu/Debian
sudo apt install portaudio19-dev
```

Ya está documentado en README y en el workflow de CI.

---

### 6. `src/ui/tray.py` - System tray

Usa `QSystemTrayIcon` de PySide6. Funciona en la mayoría de entornos Linux, pero:
- **GNOME 42+** eliminó el soporte nativo de system tray. Se necesita la extensión [AppIndicator](https://extensions.gnome.org/extension/615/appindicator-support/).
- **KDE, XFCE, Cinnamon**: Funcionan sin cambios.

**Cambio**: El código ya maneja el caso de tray no disponible (muestra warning). Documentar que en GNOME se necesita la extensión AppIndicator, o considerar usar `libappindicator` vía Qt.

---

### 7. `src/ui/overlay.py` y `main_window.py` - Ventanas frameless

Las ventanas sin marco (`FramelessWindowHint`) pueden comportarse distinto en algunos window managers de Linux (posición, transparencia, always-on-top).

**Cambio**: Testear en los DEs target (XFCE, KDE, GNOME). Posible necesidad de ajustar flags de ventana condicionalmente.

---

### 8. `Makefile` - Comandos Windows-only

```makefile
clean:
    rmdir /s /q build dist 2>nul & del /q *.spec 2>nul & echo Done

build:
    # usa ";" como separador de --add-data (Windows)
```

**Cambio**: Hacer cross-platform:
```makefile
clean:
ifeq ($(OS),Windows_NT)
    rmdir /s /q build dist 2>nul & del /q *.spec 2>nul & echo Done
else
    rm -rf build dist *.spec && echo Done
endif

build:
ifeq ($(OS),Windows_NT)
    pyinstaller ... --add-data "assets;assets" --add-data "src/ui/assets;src/ui/assets" ...
else
    pyinstaller ... --add-data "assets:assets" --add-data "src/ui/assets:src/ui/assets" ...
endif
```

---

## Dependencias de sistema en Linux

| Paquete | Propósito | Instalación (Ubuntu/Debian) |
|---|---|---|
| `portaudio19-dev` | Grabación de audio | `sudo apt install portaudio19-dev` |
| `xclip` o `xsel` | Clipboard | `sudo apt install xclip` |
| `libxcb-xinerama0` | PySide6/Qt en X11 | `sudo apt install libxcb-xinerama0` |
| `libxcb-cursor0` | PySide6/Qt en X11 | `sudo apt install libxcb-cursor0` |

---

## Limitación conocida: Wayland

Las siguientes funciones **no funcionan en Wayland** por restricciones de seguridad del protocolo:
- Captura de hotkeys globales (pynput)
- Simulación de teclado (pynput)
- Posiblemente clipboard en algunas configs

**Decisión**: Soportar **X11 solamente** en la primera versión Linux. Documentarlo claramente. La mayoría de distros LTS (Ubuntu 22.04, Xubuntu, etc.) usan X11 por defecto o permiten seleccionarlo en login.

---

## Resumen de esfuerzo

| Área | Esfuerzo | Notas |
|---|---|---|
| Makefile | Bajo | Condicionales por OS |
| Hotkey service | Bajo-Medio | Testear sin `_win32_filter` en Linux |
| Keyboard simulation | Bajo | Testear en X11 |
| Clipboard | Bajo | Documentar `xclip` |
| Audio | Ninguno | Ya funciona |
| System tray | Bajo | Documentar extensión GNOME |
| UI/Ventanas | Medio | Testear en varios DEs |
| Dependencias Python | Ninguno | Todas son cross-platform |
| CI/CD | Ninguno | Ya tiene build Linux |

**Estimación global**: La app necesita principalmente **testing en Linux** y ajustes menores. No hay refactors grandes. El 80% del trabajo es validación, no código nuevo.

---

## Preparación futura para macOS

Puntos a tener en cuenta cuando se añada soporte macOS:
- **Permisos**: macOS requiere permisos explícitos de Accesibilidad para hotkeys globales y simulación de teclado (System Preferences > Privacy > Accessibility)
- **Notarización**: Las apps deben estar firmadas y notarizadas para distribuirse fuera de la App Store
- **Icono**: Formato `.icns` en lugar de `.ico`
- **Menu bar**: macOS usa menu bar en lugar de system tray (PySide6 lo maneja, pero la UX es distinta)
- **Packaging**: Usar `py2app` o PyInstaller con bundle `.app`
- pynput funciona en macOS pero requiere el permiso de Accesibilidad
