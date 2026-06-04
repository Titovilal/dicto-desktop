#!/usr/bin/env bash
# Publica una release de Dicto en GitHub DESDE LOCAL (o desde el devcontainer)
# sin disparar el workflow de GitHub Actions (.github/workflows/build.yml).
#
# Por qué no salta el CI:
#   El workflow se dispara con `on: push: tags: v*`. Aquí NO hacemos push de un
#   tag con `git push`: dejamos que `gh release create vX.Y.Z` cree el tag vía la
#   API de GitHub. Los tags/releases creados por la API NO generan el evento
#   `push`, así que el job de build NO se ejecuta. El updater de la app solo
#   necesita el release "latest" con el asset .deb, que es lo que subimos aquí.
#
# Uso:
#   bash scripts/release.sh                 # build + crea release vX.Y.Z (X.Y.Z = pyproject)
#   DRAFT=1 bash scripts/release.sh         # crea la release como borrador
#   SKIP_BUILD=1 bash scripts/release.sh    # reusa dist/*.deb y dist/*.tar.gz ya construidos
#
# Requisitos en el contenedor/host:
#   - gh autenticado (gh auth login)  o  GH_TOKEN/GITHUB_TOKEN exportado con scope `repo`
#   - uv, fakeroot, dpkg-deb  (ver .ctx/docs/release.md)
#
# Salida: release v<version> en Titovilal/dicto-desktop con:
#   dist/dicto_<version>_amd64.deb   (lo que consume el updater)
#   dist/dicto-linux-amd64.tar.gz
set -euo pipefail

cd "$(dirname "$0")/.."
ROOT="$(pwd)"

VERSION="$(grep -m1 '^version' pyproject.toml | sed -E 's/.*"([^"]+)".*/\1/')"
TAG="v$VERSION"
REPO="${DICTO_RELEASE_REPO:-Titovilal/dicto-desktop}"

echo ">> Release $TAG -> $REPO"

# --- 0. comprobaciones previas ----------------------------------------------
command -v gh >/dev/null || { echo "ERROR: falta 'gh' (GitHub CLI)." >&2; exit 1; }
if ! gh auth status >/dev/null 2>&1 && [[ -z "${GH_TOKEN:-${GITHUB_TOKEN:-}}" ]]; then
  echo "ERROR: gh no autenticado. Ejecuta 'gh auth login' o exporta GH_TOKEN." >&2
  exit 1
fi

if gh release view "$TAG" --repo "$REPO" >/dev/null 2>&1; then
  echo "ERROR: la release $TAG ya existe en $REPO." >&2
  echo "       Sube la versión en pyproject.toml o borra la release antes de re-publicar:" >&2
  echo "       gh release delete $TAG --repo $REPO --cleanup-tag --yes" >&2
  exit 1
fi

# --- 1. build de artefactos --------------------------------------------------
if [[ "${SKIP_BUILD:-0}" != "1" ]]; then
  echo ">> Construyendo bundle PyInstaller + .deb..."
  bash scripts/build-deb.sh
  echo ">> Empaquetando tar.gz..."
  tar -czf "dist/dicto-linux-amd64.tar.gz" -C dist dicto
fi

DEB="dist/dicto_${VERSION}_amd64.deb"
TARBALL="dist/dicto-linux-amd64.tar.gz"
[[ -f "$DEB" ]] || { echo "ERROR: no existe $DEB (ejecuta sin SKIP_BUILD)." >&2; exit 1; }
[[ -f "$TARBALL" ]] || { echo "ERROR: no existe $TARBALL (ejecuta sin SKIP_BUILD)." >&2; exit 1; }

# --- 2. crear la release (crea el tag por API -> NO dispara el CI) -----------
DRAFT_FLAG=()
[[ "${DRAFT:-0}" == "1" ]] && DRAFT_FLAG=(--draft)

echo ">> Creando release $TAG (tag vía API, sin disparar Actions)..."
gh release create "$TAG" \
  --repo "$REPO" \
  --target "$(git rev-parse HEAD)" \
  --title "$TAG" \
  --generate-notes \
  "${DRAFT_FLAG[@]}" \
  "$DEB" "$TARBALL"

echo
echo ">> Release publicada: https://github.com/$REPO/releases/tag/$TAG"
echo ">> El updater de la app la verá como 'latest' y ofrecerá el .deb."
