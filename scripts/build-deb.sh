#!/usr/bin/env bash
# Construye un paquete .deb de Dicto a partir del bundle onedir de PyInstaller.
#
# Uso:
#   bash scripts/build-deb.sh            # build PyInstaller + empaqueta .deb
#   SKIP_PYINSTALLER=1 bash scripts/build-deb.sh   # reusa dist/dicto existente
#
# Salida: dist/dicto_<version>_<arch>.deb
#
# Instala con:  sudo apt install ./dist/dicto_<version>_amd64.deb
# Desinstala:   sudo apt remove dicto
#
# Layout del paquete:
#   /opt/dicto/                     -> bundle PyInstaller (ejecutable + _internal)
#   /usr/bin/dicto                  -> symlink al ejecutable
#   /usr/share/applications/dicto.desktop
#   /usr/share/icons/hicolor/256x256/apps/dicto.png
set -euo pipefail

cd "$(dirname "$0")/.."
ROOT="$(pwd)"

# --- metadatos ---------------------------------------------------------------
VERSION="$(grep -m1 '^version' pyproject.toml | sed -E 's/.*"([^"]+)".*/\1/')"
ARCH="$(dpkg --print-architecture)"   # p.ej. amd64
PKG="dicto"
MAINTAINER="Titovilal <terturionsland@gmail.com>"
DESC="Minimalist desktop app for voice-to-text transcription with global hotkey"

echo ">> Dicto $VERSION ($ARCH)"

# --- 1. build PyInstaller (onedir) ------------------------------------------
if [[ "${SKIP_PYINSTALLER:-0}" != "1" ]]; then
  echo ">> PyInstaller build..."
  uv run pyinstaller --name "dicto" --onedir --windowed --noconfirm \
    --copy-metadata dicto \
    --add-data "assets:assets" --add-data "src/ui/assets:src/ui/assets" \
    --hidden-import dbus_next \
    src/main.py
fi

if [[ ! -x "dist/dicto/dicto" ]]; then
  echo "ERROR: no existe dist/dicto/dicto. Ejecuta sin SKIP_PYINSTALLER." >&2
  exit 1
fi

# --- 2. staging del árbol del paquete ---------------------------------------
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

install -d "$STAGE/opt"
cp -a "dist/dicto" "$STAGE/opt/dicto"

install -d "$STAGE/usr/bin"
ln -sf "/opt/dicto/dicto" "$STAGE/usr/bin/dicto"

install -d "$STAGE/usr/share/icons/hicolor/256x256/apps"
cp "assets/icons/icon.png" "$STAGE/usr/share/icons/hicolor/256x256/apps/dicto.png"

install -d "$STAGE/usr/share/applications"
cat > "$STAGE/usr/share/applications/dicto.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Dicto
Comment=$DESC
Exec=/usr/bin/dicto
Icon=dicto
Terminal=false
Categories=AudioVideo;Audio;Utility;
StartupNotify=true
EOF

# --- 3. metadatos DEBIAN/control --------------------------------------------
INSTALLED_KB="$(du -sk "$STAGE" | cut -f1)"
install -d "$STAGE/DEBIAN"
cat > "$STAGE/DEBIAN/control" <<EOF
Package: $PKG
Version: $VERSION
Section: sound
Priority: optional
Architecture: $ARCH
Maintainer: $MAINTAINER
Installed-Size: $INSTALLED_KB
Depends: libgl1, libegl1, libxkbcommon0, libfontconfig1, libportaudio2, libasound2, libpulse0
Description: $DESC
 Dicto records voice via a global hotkey, transcribes it through the Dicto
 API and pastes the result into the focused application.
EOF

# refresca caches de iconos/desktop al instalar/desinstalar
cat > "$STAGE/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -e
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database -q /usr/share/applications || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
fi
EOF
cp "$STAGE/DEBIAN/postinst" "$STAGE/DEBIAN/postrm"
chmod 0755 "$STAGE/DEBIAN/postinst" "$STAGE/DEBIAN/postrm"

# --- 4. construir el .deb ----------------------------------------------------
OUT="dist/${PKG}_${VERSION}_${ARCH}.deb"
fakeroot dpkg-deb --build --root-owner-group "$STAGE" "$OUT"

echo
echo ">> Paquete creado: $OUT"
echo ">> Instalar:   sudo apt install ./$OUT"
echo ">> Desinstalar: sudo apt remove $PKG"
