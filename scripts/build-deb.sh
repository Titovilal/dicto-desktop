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
  uv run pyinstaller --noconfirm dicto-linux.spec
fi

# El bundle se llama "Dicto" con dicto-linux.spec (build local) pero "dicto" en
# CI, que exporta DICTO_BUNDLE_NAME=dicto (el spec lo lee) para que el .tar.gz
# portable conserve ese nombre. Acepta ambos en vez de imponer una sola grafía.
BUNDLE=""
for candidate in "dist/Dicto/Dicto" "dist/dicto/dicto"; do
  if [[ -x "$candidate" ]]; then
    BUNDLE="$(dirname "$candidate")"
    BIN="$(basename "$candidate")"
    break
  fi
done

if [[ -z "$BUNDLE" ]]; then
  echo "ERROR: no existe dist/Dicto/Dicto ni dist/dicto/dicto. Ejecuta sin SKIP_PYINSTALLER." >&2
  exit 1
fi

# --- 2. staging del árbol del paquete ---------------------------------------
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

install -d "$STAGE/opt"
cp -a "$BUNDLE" "$STAGE/opt/dicto"

install -d "$STAGE/usr/bin"
ln -sf "/opt/dicto/$BIN" "$STAGE/usr/bin/dicto"

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

# --- suelo de glibc ----------------------------------------------------------
# PyInstaller enlaza contra la glibc de la máquina de build y glibc solo es
# compatible hacia atrás: la versión de quien CONSTRUYE es el suelo real para
# quien instala. Sin declararlo, apt instala feliz y la app *segfaultea* al
# arrancar; con el Depends, apt rechaza el paquete con un error legible.
#
# El suelo se CLAVA a la glibc del runner de CI (ubuntu-22.04 → 2.35), que es
# el único build que se publica. Ver GLIBC_FLOOR abajo.
#
# Por qué clavarlo y no derivarlo del bundle -- se probaron las dos vías que
# parecen "más automáticas" y ambas producen un .deb PEOR:
#
#   1. Máximo de los tags `GLIBC_x.y` de todo el bundle (lo que se hacía antes).
#      Asume que toda .so empaquetada se compiló contra la glibc más antigua
#      soportada, y eso es FALSO para las libs que PyInstaller copia del
#      sistema de build. En Ubuntu 26.04 daba `libc6 (>= 2.43)` -- un .deb que
#      no instala en 22.04, 24.04 NI 25.10 -- y los tags 2.43 venían de
#      `libmvec.so.1`, que es la propia libm de glibc: sus tags solo reflejan
#      la glibc del host, no lo que la app necesita. En CI salía bien por
#      casualidad (en 22.04 nada puede declarar más de 2.35), así que el bug
#      solo se veía en `make deb` local: justo la divergencia local/CI que
#      esta tanda venía a eliminar.
#
#   2. `dpkg-shlibdeps` (resuelve por símbolo contra los paquetes instalados).
#      Es lo correcto para un paquete Debian normal, pero NO para un bundle de
#      PyInstaller, que es autocontenido por diseño. Comprobado sobre este
#      bundle: (a) falla en duro con "cannot find library libtiff.so.5 needed
#      by libqtiff.so" -- Qt trae el plugin TIFF y ningún Ubuntu moderno tiene
#      ya libtiff5; (b) emite `libc6 (>> 2.43), libc6 (<< 2.44)`, es decir un
#      TECHO que ata el paquete a la glibc exacta del host, peor todavía que el
#      máximo; (c) añade ~110 dependencias del host (`libqt6core6t64 (>= 6.10.2)`,
#      `qt6-base-private-abi (= 6.10.2)`, …) para librerías que ya viajan
#      DENTRO del bundle, porque no puede distinguir vendorizado de sistema.
#
# Así que el suelo es un dato de POLÍTICA de release (en qué runner compilamos),
# no algo inferible del artefacto. Se declara como tal.
#
# Si algún día se sube el pin del runner en .github/workflows/build.yml, sube
# este número a la vez. Son el mismo hecho escrito en dos sitios y no hay forma
# de derivar uno del otro (el .deb se empaqueta en el mismo job que compila,
# pero el script también corre en local sobre distros distintas).
GLIBC_FLOOR="2.35"   # = glibc de ubuntu-22.04, el runner de `build-linux`
LIBC_DEP="libc6 (>= $GLIBC_FLOOR), "
echo ">> suelo de glibc declarado: $GLIBC_FLOOR (runner de CI: ubuntu-22.04)"

# Aviso, no error: un build LOCAL en una distro más nueva produce binarios que
# de verdad necesitan una glibc mayor que la declarada, así que ese .deb
# instalará en 22.04 y reventará al arrancar. Sirve para probar en tu máquina;
# lo que se publica sale del CI.
if command -v ldd >/dev/null 2>&1; then
  HOST_GLIBC="$(ldd --version 2>/dev/null | sed -nE '1s/.*[^0-9]([0-9]+\.[0-9]+)$/\1/p')"
  if [[ -n "$HOST_GLIBC" ]] \
     && [[ "$(printf '%s\n%s\n' "$GLIBC_FLOOR" "$HOST_GLIBC" | sort -V | tail -1)" != "$GLIBC_FLOOR" ]]; then
    echo ">> AVISO: compilas con glibc $HOST_GLIBC pero se declara >= $GLIBC_FLOOR." >&2
    echo ">>        Este .deb es para pruebas locales; el que se publica lo compila" >&2
    echo ">>        el CI en ubuntu-22.04. No lo subas a una release." >&2
  fi
fi
install -d "$STAGE/DEBIAN"
cat > "$STAGE/DEBIAN/control" <<EOF
Package: $PKG
Version: $VERSION
Section: sound
Priority: optional
Architecture: $ARCH
Maintainer: $MAINTAINER
Installed-Size: $INSTALLED_KB
Depends: ${LIBC_DEP}libgl1, libegl1, libxkbcommon0, libxkbcommon-x11-0, libfontconfig1, libportaudio2, libasound2, libpulse0, libxcb-cursor0, libxcb-icccm4, libxcb-image0, libxcb-keysyms1, libxcb-render-util0, libxcb-shape0, libxcb-util1, libxcb-xkb1
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
