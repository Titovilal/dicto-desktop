# Entrada en Wayland: hotkey global, paste e inyección de texto, clipboard

Estado, diagnóstico y plan para que Dicto funcione bien en Linux **Ubuntu / GNOME
Wayland** (y, de paso, X11, Windows y macOS). Documento de referencia previo a
implementar; recoge investigación (fuentes citadas) + pruebas reales hechas sobre
un host GNOME Wayland nativo.

> TL;DR: el **hotkey** en Wayland ya está planteado con el portal XDG
> `GlobalShortcuts`. Lo que de verdad falta es **la inyección de texto** (el
> "paste" automático), que hoy usa `pynput` y **no funciona en Wayland nativo**.
> El **clipboard** debe migrar de `pyperclip` a **`QClipboard`** (Qt, ya está en
> el stack). Para multidistro, **Flatpak** encaja mejor que AppImage.

---

## 1. El problema de fondo

Wayland impide por diseño que una app lea el teclado global o inyecte input en
otras ventanas sin un mecanismo explícitamente aprobado por el compositor. Esto
rompe dos cosas en las que `pynput` se apoyaba en X11:

1. **Hotkey global** (capturar Ctrl+Shift+Space estés donde estés).
2. **Inyección de texto / paste** (simular Ctrl+V o teclear el texto transcrito).

Wayland ya es el **default** en Ubuntu 22.04+, Fedora, etc., así que esto crece,
no desaparece.

---

## 2. Estado actual del código

| Pieza | Fichero | Backend hoy | ¿Wayland? |
|---|---|---|---|
| Hotkey global | `src/services/hotkey.py` + `hotkey_wayland.py` | `pynput` (X11/Win/mac) **o** portal `GlobalShortcuts` (Wayland) | ✅ ya hay rama Wayland |
| Inyección de texto (paste/enter/copy) | `src/services/keyboard_actions.py` | `pynput.Controller` directo | ❌ **sin rama Wayland** |
| Clipboard read/write | `src/services/clipboard.py` | `win32clipboard` (Win) / `pyperclip` (resto) | ⚠️ `pyperclip` no soporta Wayland |

- `create_hotkey_listener()` ya es la **abstracción**: detecta `is_wayland()` y
  devuelve `WaylandHotkeyListener` (portal D-Bus) o `HotkeyListener` (pynput).
- `keyboard_actions.py` y `clipboard.py` **no** tienen esa abstracción todavía.

---

## 3. Pruebas reales (host: Ubuntu 26.04, GNOME Wayland nativo)

Entorno verificado en vivo:

```
XDG_SESSION_TYPE=wayland   XDG_CURRENT_DESKTOP=ubuntu:GNOME
DISPLAY=:0  +  Xwayland :0 -enable-ei-portal   (¡XWayland activo!)
Portales:  GlobalShortcuts v1 ✅   RemoteDesktop v2 (AvailableDeviceTypes=7) ✅
Herramientas: wl-copy/wl-paste ✅  xclip ✅  ydotool ❌  wtype ❌  flatpak ❌
/dev/uinput: existe, solo root (crw------- root root)
```

| Test | Resultado | Lectura |
|---|---|---|
| `QClipboard` set/get | ✅ `Qt platform: wayland`, ida y vuelta OK | **Nativo Wayland, fiable** |
| `pyperclip` copy/paste | ✅ "funcionó"… | **Falso positivo**: va por `xclip` + XWayland. En Wayland puro sin XWayland falla |
| `pynput` inyectar tecla `'a'` | ✅ capturada por un listener propio | **Falso positivo**: pynput cayó al backend X11/XWayland. NO inyecta en ventanas Wayland nativas |
| `RemoteDesktop` portal | v2 con EIS disponible | Camino "correcto" para paste, pero ver fricción de permisos |

> ⚠️ Lección clave: **probar en esta máquina engaña**, porque tiene XWayland (`DISPLAY=:0`).
> `pynput`/`pyperclip` aparentan funcionar enganchándose a X11 por debajo, pero
> fallan al escribir en aplicaciones **nativas Wayland**. "En mi máquina va" aquí
> no es garantía.

> Nota de entorno: el `.venv` del repo se creó dentro del **devcontainer**
> (`home = /home/vscode/.local/share/uv/...`), por eso su `bin/python` no resuelve
> en el host. Para pruebas en host se cargó el `site-packages` del venv con el
> python del sistema vía `PYTHONPATH`. Las pruebas de runtime "de verdad"
> conviene correrlas **dentro del devcontainer** o en el host con su intérprete.

---

## 4. Opciones de inyección de texto en GNOME Wayland

| Opción | ¿GNOME/Mutter? | Permiso en runtime | Setup | Empaquetado | Veredicto |
|---|---|---|---|---|---|
| **Clipboard + Ctrl+V manual** (QClipboard) | ✅ siempre | No | Ninguno | Trivial (.deb/AppImage/Flatpak) | **Default seguro** |
| **ydotool** (uinput) | ✅ siempre (bajo Wayland, a nivel kernel) | No (tras setup) | udev rule + grupo `input` + daemon `ydotoold` | `.deb` con `postinst`; Flatpak **difícil** (sandbox sin `/dev/uinput`) | **Auto-paste real recomendado** |
| **Portal `RemoteDesktop`** (NotifyKeyboard / EIS) | ✅ (oficial) | ⚠️ **diálogo cada sesión** (persistencia rota en GNOME) | Ninguno extra | Flatpak excelente | Futuro / experimental |
| **wtype** (`virtual-keyboard-v1`) | ❌ **NO** (Mutter no implementa el protocolo) | — | — | — | **Descartado en GNOME** |

Detalles:

- **ydotool**: opera vía `/dev/uinput`, por debajo de Wayland → display-server
  agnostic, sin diálogos en uso. Requiere una vez:
  ```
  # /etc/udev/rules.d/70-uinput.rules
  KERNEL=="uinput", GROUP="input", MODE="0660", TAG+="uaccess"
  ```
  `usermod -aG input $USER` (+ relogin) y el daemon `ydotoold` (systemd user
  service). En Ubuntu 24.04 hay bug conocido: si el daemon corre como root el
  socket queda 600 y el cliente no conecta → forzar `chmod 666` del socket.
  Invocación: `subprocess.run(["ydotool","type","--",texto], env={...,"YDOTOOL_SOCKET":socket})`.
- **Portal RemoteDesktop**: en GNOME el diálogo de permiso **no persiste de forma
  fiable** (el "recordar" no funciona); inaceptable como flujo principal de una
  app de dictado. Útil en Flatpak el día que GNOME arregle la persistencia.
- **wtype**: confirmado que **no funciona en GNOME** (`"Compositor does not
  support the virtual keyboard protocol"`); solo wlroots (Sway/Hyprland).

---

## 5. Clipboard

- `pyperclip` **no soporta Wayland** oficialmente (issue abierto desde 2019);
  necesita `xclip`/`xsel` (X11) o un fork (`pyperclipfix`) que llame a
  `wl-clipboard`.
- **Recomendado: `QClipboard` de PySide6**. Python puro (sin binario externo),
  ya está en el stack, **nativo Wayland** (Qt habla `wl-data-device`). Verificado
  funcionando en el host.
  ```python
  from PySide6.QtWidgets import QApplication
  QApplication.clipboard().setText(texto)
  ```
- Si por algo se mantiene un backend de CLI, el paquete apt es `wl-clipboard`
  (`wl-copy`/`wl-paste`).

---

## 6. Empaquetado multidistro

| Formato | Hotkey/paste Wayland | Multidistro | Fricción Ubuntu | Mantenimiento | Veredicto |
|---|---|---|---|---|---|
| `.deb` (actual) | Manual (udev/ydotool vía `postinst`) | No | Baja | Bajo | Mantener para Ubuntu/Debian |
| **Flatpak** | **Portales nativos** (GlobalShortcuts/RemoteDesktop) | Sí | Baja (Flathub) | Medio-alto | **Recomendado multidistro** |
| AppImage | Depende del host; riesgo de faltar plugin `qt6-wayland` | Sí | Muy baja | Bajo | **No aporta** sobre el `.tar.gz` actual |

- **Flatpak** va de la mano con los portales (su sandbox es justo el modelo para
  el que se diseñaron); es el camino técnicamente correcto para hotkeys/paste
  legítimos en Wayland sin permisos de root ni herramientas externas.
- **AppImage** no añade valor frente al `.tar.gz` que ya generas, y puede empeorar
  Wayland si no se empaqueta el plugin QPA `qt6-wayland`.

---

## 7. Recomendación / plan

**Inyección de texto — niveles con fallback automático (detectar y degradar):**
1. **Nivel 1 (default, cero fricción):** QClipboard + notificación "pega con
   Ctrl+V". Guardar y restaurar el portapapeles previo (delay ~300 ms).
2. **Nivel 2 (auto-paste real):** usar `ydotool` si el socket está disponible;
   `.deb` configura udev + daemon en `postinst`. Si no, caer al nivel 1.
3. **Nivel 3 (futuro/Flatpak):** portal `RemoteDesktop`, marcado "experimental"
   por el diálogo de permisos de GNOME.
4. **No** implementar `wtype` en GNOME.

**Clipboard:** migrar la rama Linux de `clipboard.py` a `QClipboard`.

**Empaquetado:** `.deb` (Ubuntu) + **Flatpak** (multidistro). Descartar AppImage.

**Arquitectura sugerida:** una abstracción `text_injector` análoga a
`create_hotkey_listener()` (selección de backend por entorno), y un comando
**`dicto --check-input`** ("doctor") que imprima qué backend de hotkey/paste se
usará y por qué.

### Qué se puede testear automáticamente (sin intervención humana)
- Detección de entorno: `XDG_SESSION_TYPE`, portales vía `busctl introspect`,
  `ydotool`/`/dev/uinput`, XWayland.
- `QClipboard` set/get (ya pasa en el host).
- Selección de backend del `text_injector` según entorno simulado.

### Qué NO se puede testear sin un humano (una vez)
- El diálogo de permiso del portal (`GlobalShortcuts` / `RemoteDesktop`).
- La inyección real en una **ventana nativa Wayland** de otra app.

---

## 8. Otras plataformas (referencia)

- **Windows**: `pynput._win32` + `win32clipboard`. Funciona; reactivar job
  `build-windows`.
- **macOS**: `pynput._darwin` + permisos de Accesibilidad; build `--windowed`
  `.app`/`.dmg` con **firma + notarización** (si no, Gatekeeper bloquea); requiere
  runner `macos-latest`.
- **Linux X11**: `pynput._xorg` funciona tal cual.

---

## 9. Fuentes

- Remote Desktop Portal — https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.RemoteDesktop.html
- Global Shortcuts Portal — https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.GlobalShortcuts.html
- GNOME Discourse, persistencia RemoteDesktop (Feb 2024) — https://discourse.gnome.org/t/persistent-remote-desktop-access-api/19415
- Mutter no implementa virtual-keyboard-v1 — https://gitlab.gnome.org/GNOME/mutter/-/issues/4124
- wtype falla en GNOME — https://github.com/atx/wtype/issues/45
- ydotool (repo + Ubuntu 24.04 issue) — https://github.com/ReimuNotMoe/ydotool · https://github.com/ReimuNotMoe/ydotool/issues/285
- KeePassXC autotype vía portal — https://github.com/keepassxreboot/keepassxc/pull/10905
- pyperclip + Wayland (issue #141) — https://github.com/asweigart/pyperclip/issues/141
- QClipboard (PySide6) — https://doc.qt.io/qtforpython-6/PySide6/QtGui/QClipboard.html
- Wayland and Qt — https://doc.qt.io/qt-6/wayland-and-qt.html
- AppImage + Wayland (plugin QPA) — https://github.com/AppImage/AppImageKit/wiki/Wayland
- Flatpak desktop integration / portales — https://docs.flatpak.org/en/latest/desktop-integration.html
- wl-clipboard — https://github.com/bugaevc/wl-clipboard
