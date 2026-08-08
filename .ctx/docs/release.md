# Build & Release local (sin disparar el CI)

Cómo construir el `.deb` y publicar una release de Dicto **desde tu máquina o desde
el devcontainer**, sin que se ejecute `.github/workflows/build.yml`. Sirve para
iterar rápido y probar en producción a través del updater de la app.

## Por qué no salta GitHub Actions

El workflow se dispara con:

```yaml
on:
  push:
    tags: ['v*']
```

`scripts/release.sh` **no hace `git push` de un tag**. Crea el tag y la release
con `gh release create vX.Y.Z --target <sha>`, es decir vía la **API de GitHub**.
Los tags/releases creados por la API **no generan el evento `push`**, así que el
job de build no se ejecuta. El [updater](services.md) (`src/services/updater.py`)
solo necesita el release `latest` con un asset `.deb`, que es justo lo que sube
este script. Resultado: build una sola vez (aquí), cero duplicado en Actions.

## Requisitos (ya cubiertos en el devcontainer)

- `uv`, `dpkg-deb` → vienen en la imagen base.
- `fakeroot` → si falta: `sudo apt-get install -y fakeroot`.
- `gh` autenticado. Una de:
  - `gh auth login` (interactivo, una vez), o
  - exportar un token con scope `repo`: `export GH_TOKEN=ghp_...`

> El devcontainer es **Debian 12 (glibc 2.36)**, no Ubuntu. PyInstaller empaqueta
> contra la glibc del sistema de build, así que el `.deb` requiere **glibc ≥ 2.36**
> en destino: funciona en Ubuntu 24.04 (glibc 2.39) pero puede fallar en Ubuntu
> 22.04 (glibc 2.35). El CI compila en `ubuntu-latest`; si necesitas máxima
> compatibilidad, deja ese build para Actions. Para tu uso de desarrollo/pruebas
> el build local vale.

## Pasos

### 1. Sube la versión

El tag y la release salen de `pyproject.toml`. Edita:

```toml
version = "2.7.3"
```

Sincroniza también `src/version.py` si aplica, y commitea. La release apunta a
`HEAD`, así que commitea antes de publicar.

### 2. Publica

```bash
bash scripts/release.sh
```

Esto:
1. Construye el bundle PyInstaller + `.deb` (`scripts/build-deb.sh`).
2. Empaqueta `dist/dicto-linux-amd64.tar.gz`.
3. Crea la release `vX.Y.Z` con `gh` (tag por API → sin CI) y sube
   `dicto_<version>_amd64.deb` + el `tar.gz`.

Variables útiles:

| Variable        | Efecto                                                       |
|-----------------|--------------------------------------------------------------|
| `DRAFT=1`       | Crea la release como borrador (no la verá el updater aún).   |
| `SKIP_BUILD=1`  | Reusa `dist/*.deb` y `dist/*.tar.gz` ya construidos.         |
| `DICTO_RELEASE_REPO` | Publica en otro repo (por defecto `Titovilal/dicto-desktop`). |

### 3. Verifica desde la app

La app instalada (`/opt/dicto`) detecta la nueva `latest`, descarga el `.deb` y
lo instala con `pkexec apt-get install`. Ver flujo en
[`services.md`](services.md) y `src/ui/main_window_updates.py`.

## Windows: el instalador sale del CI

`scripts/release.sh` solo construye y sube el artefacto **Linux** (`.deb` +
`.tar.gz`). El instalador de Windows (`Dicto-<ver>-setup.exe`, Inno Setup) lo
produce **GitHub Actions** (job `build-windows` en `.github/workflows/build.yml`),
que se dispara al hacer `push` de un tag `v*`.

Implicación para el updater de Windows: una release creada solo con
`scripts/release.sh` (tag por API, sin CI) **no** llevará el `setup.exe`, así que
la app Windows caerá al fallback de "abrir página de release". Para que la
auto-actualización en Windows funcione, publica con un tag pusheado (que dispara
el CI) o adjunta el `setup.exe` a la release manualmente.

## Re-publicar la misma versión

`gh release create` falla si el tag ya existe. Para rehacerla:

```bash
gh release delete vX.Y.Z --repo Titovilal/dicto-desktop --cleanup-tag --yes
bash scripts/release.sh
```

## Solo el .deb (sin release)

```bash
bash scripts/build-deb.sh          # build PyInstaller + empaqueta
SKIP_PYINSTALLER=1 bash scripts/build-deb.sh   # reusa dist/dicto/ existente
```

## Audio: librerías del sistema, no del bundle

`dicto-linux.spec` **excluye** del bundle `libportaudio.so*`, `libasound.so*` y
`libjack.so*` para que la app enlace contra las del sistema (el `.deb` ya las
exige en `Depends`: `libportaudio2`, `libasound2`, `libpulse0`).

El PortAudio que PyInstaller recoge del wheel de `sounddevice` viene compilado
**sin backend de PulseAudio**, y el `libasound.so.2` que arrastra viaja sin sus
módulos de `alsa-lib`. Si se empaquetan, desaparecen los PCM `pulse`, `pipewire`
y `default`: solo quedan los `hw:` en acceso exclusivo, PipeWire ya tiene el
micro cogido y grabar falla con `Invalid sample rate [PaErrorCode -9997]`. En
`uv run` no se nota porque ahí se usa el PortAudio del sistema.

El CI (`.github/workflows/build.yml`) **también usa el spec**, con
`DICTO_BUNDLE_NAME=dicto` para que el bundle salga en `dist/dicto/dicto` (que es
lo que espera el `.tar.gz` portable). Antes invocaba PyInstaller con flags
sueltos y se saltaba el spec, así que el arreglo solo llegaba al build local y
el `.deb` publicado seguía roto: si añades algo al spec, no lo dupliques en el
workflow.

Para comprobarlo tras un build, `PulseAudio` debe salir en la lista:

```bash
LD_LIBRARY_PATH=dist/Dicto/_internal .venv/bin/python -c \
  "import sounddevice as sd; print([h['name'] for h in sd.query_hostapis()])"
```
