# Notas de empaquetado / distribución

Hallazgos y decisiones sobre cómo se construye y distribuye Dicto en las
distintas plataformas. Origen: análisis del log de GitHub Actions al construir
el `.deb` (2026-05-31).

## Estado actual del CI (`.github/workflows/build.yml`)

- **Linux (`build-linux`)**: activo. Construye bundle PyInstaller `onedir`,
  genera `dicto-linux-amd64.tar.gz` y empaqueta `.deb` vía
  `scripts/build-deb.sh` con `SKIP_PYINSTALLER=1`.
- **Windows (`build-windows`)**: comentado.
- **macOS**: no existe job.
- Release: `softprops/action-gh-release` al hacer push de tag `v*` o
  `workflow_dispatch` con `create_release=true`.

## Hallazgos del log de build del `.deb`

El build de PyInstaller **termina correctamente** ("Build complete!"). Los
mensajes problemáticos son *warnings*, no errores, pero afectan al runtime:

### 1. Librerías `libxcb-*` no encontradas (impacto real en X11)

PyInstaller no pudo resolver las dependencias del plugin Qt `xcb`
(`libqxcb.so`, `libQt6XcbQpa.so.6`) porque no están instaladas en el runner de
CI. Sin esas libs, en una máquina **X11** la app falla al arrancar con:

> Could not load the Qt platform plugin "xcb"

Libs implicadas: `libxcb-shape0`, `libxcb-keysyms1`, `libxcb-xkb1`,
`libxcb-util1`, `libxcb-image0`, `libxcb-render-util0`, `libxcb-cursor0`,
`libxcb-icccm4`, `libxkbcommon-x11-0`, `libtiff5` (esta última solo para
`libqtiff`, no crítica).

**Solución aplicada**: declararlas como `Depends` en el control del `.deb`
(`scripts/build-deb.sh`), para que apt las instale del sistema. Es más portable
entre distros que empaquetar los `.so` concretos en el bundle.

### 2. `pynput` no introspeccionado (DISPLAY vacío en CI)

```
WARNING: Failed to collect submodules for 'pynput' because importing 'pynput'
raised: ImportError: this platform is not supported: ('failed to acquire X
connection: Bad display name ""', ...)
```

En CI no hay servidor X, así que PyInstaller no recolectó los submódulos de
pynput → el hotkey global podría no quedar en el bundle.

**Solución aplicada**: forzar hidden-imports en el comando PyInstaller
(`build.yml` y `build-deb.sh`):
`pynput.keyboard`, `pynput.mouse`, `pynput.keyboard._xorg`,
`pynput.mouse._xorg`.

> Nota: los warnings de `libxcb-* not found` y de pynput **seguirán apareciendo**
> en el log de CI (las libs no están en el runner). Ya no rompen el runtime
> porque se resuelven al instalar el `.deb`.

## Pendiente / a tener en cuenta (multiplataforma)

Objetivo: la app debe usarse bien en Ubuntu, otras distros Linux, Windows y Mac.

### Otras distros Linux (Fedora, Arch, ...)
- Un `.deb` no sirve fuera de Debian/Ubuntu.
- El `.tar.gz` ya generado lleva el bundle, pero el usuario debe tener las libs
  del sistema.
- Mejor opción portable: **AppImage** o **Flatpak**, que incluyen las libs
  dentro y funcionan en cualquier distro sin gestionar `Depends`.

### Wayland vs X11
- pynput (hotkey) y la inyección de texto necesitan backend X11.
- En Wayland puro el hotkey/paste puede no funcionar.
- Fallback a evaluar: `ydotool` o portales del escritorio.
- (Ver nota de memoria sobre pynput deshabilitado en el dev-container Wayland.)

### Windows
- Job `build-windows` está comentado en `build.yml`; reactivar.
- Verificar hidden-imports equivalentes: `pynput.keyboard._win32`,
  `pynput.mouse._win32`.
- Usa Inno Setup (`installer.iss`) para el instalador `.exe`.

### macOS
- No hay job. Necesita runner `macos-latest`.
- Build `--windowed` → `.app`, empaquetar en `.dmg`.
- Firma + notarización de Apple.
- Backend `pynput.keyboard._darwin` + permisos de Accesibilidad del sistema.
