#!/usr/bin/env bash
# Arranca el bundle de PyInstaller en un HOME desechable y comprueba que llega
# a "Dicto started!".
#
# Por qué existe: la app guarda su config en $XDG_CONFIG_HOME/dicto (o
# ~/.config/dicto), así que lanzar el bundle a pelo para "ver si arranca"
# SOBRESCRIBE el config.yaml del usuario -- incluida su API key, que se pierde
# sin aviso porque no hay backup. Pasó de verdad. Usa siempre este script en
# vez de ejecutar dist/dicto/dicto directamente.
#
# Uso:
#   bash scripts/smoke-run-bundle.sh [ruta-al-binario]
#
# Por defecto prueba dist/dicto/dicto, y si no existe, dist/Dicto/Dicto.
set -euo pipefail

cd "$(dirname "$0")/.."

BIN="${1:-}"
if [[ -z "$BIN" ]]; then
  for candidate in dist/dicto/dicto dist/Dicto/Dicto; do
    [[ -x "$candidate" ]] && BIN="$candidate" && break
  done
fi
if [[ -z "$BIN" || ! -x "$BIN" ]]; then
  echo "ERROR: no encuentro el binario. Construye antes:" >&2
  echo "  DICTO_BUNDLE_NAME=dicto uv run pyinstaller --noconfirm dicto-linux.spec" >&2
  exit 1
fi
BIN="$(realpath "$BIN")"

# HOME y XDG desechables: el arranque escribe su config aquí y no en el tuyo.
FAKE_HOME="$(mktemp -d)"
LOG="$FAKE_HOME/startup.log"
trap 'rm -rf "$FAKE_HOME"' EXIT

echo ">> binario: $BIN"
echo ">> HOME desechable: $FAKE_HOME"

RUNNER=(env "HOME=$FAKE_HOME" "XDG_CONFIG_HOME=$FAKE_HOME/.config" \
            "DICTO_API_KEY=smoke-test-not-a-real-key")
# xvfb-run si está y no hay display; si no, tal cual.
if [[ -z "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]] && command -v xvfb-run >/dev/null; then
  RUNNER+=(xvfb-run -a)
fi

( cd "$FAKE_HOME" && timeout --signal=TERM --kill-after=15s 60s \
    "${RUNNER[@]}" "$BIN" ) >"$LOG" 2>&1 &
app_pid=$!

for _ in $(seq 60); do
  grep -q "Dicto started!" "$LOG" && break
  kill -0 "$app_pid" 2>/dev/null || break   # murió antes de arrancar
  sleep 1
done
kill "$app_pid" 2>/dev/null || true
wait "$app_pid" 2>/dev/null || true

echo "----- log de arranque -----"
cat "$LOG"
echo "---------------------------"

if ! grep -q "Dicto started!" "$LOG"; then
  echo ">> FALLO: el binario no llegó a arrancar." >&2
  exit 1
fi
if grep -qi "Failed to initialize components" "$LOG"; then
  echo ">> FALLO: componentes sin inicializar." >&2
  exit 1
fi

echo ">> OK: el bundle arranca (y tu config real está intacta)."
