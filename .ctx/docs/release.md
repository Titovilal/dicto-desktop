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

> **Un `.deb` construido en local no es publicable.** PyInstaller empaqueta
> contra la glibc del sistema de build, así que un build hecho en una distro más
> nueva que Ubuntu 22.04 (el devcontainer es Debian 12 → glibc 2.36; una Ubuntu
> 26.04 → 2.43) produce binarios que **no arrancan** en 22.04, aunque el
> `Depends` declare `libc6 (>= 2.35)`. El script te avisa cuando detecta este
> caso. Para desarrollo y pruebas vale; para publicar, usa el build del CI
> (`ubuntu-22.04`). Ver [Suelo de glibc](#suelo-de-glibc).

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

### El spec manda también en Windows

`make exe` y `make installer` invocan `uv run pyinstaller --noconfirm
dicto.spec`, igual que el CI. Antes pasaban flags sueltos (`--name`,
`--add-data`, `--icon`) **ignorando el spec**: exactamente el mismo fallo que
rompió el micro en Linux, pero al revés (allí el roto era el CI). Si necesitas
tocar una opción de build, va **en el spec**, que es lo único que ejecutan los
dos caminos.

Notas relacionadas:

- Se eliminaron los targets `exe-onefile` **y `build-onefile`**: nadie los
  usaba, el instalador solo consume el layout onedir (`dist/Dicto/`) y un
  onefile arranca lento y da más falsos positivos de antivirus.
  `build-onefile` era además el **último sitio que llamaba a PyInstaller con
  flags sueltos** en vez del spec, así que se saltaba las exclusiones de audio
  de `dicto-linux.spec` (el bug del micro muerto de v2.8.2, otra vez), y el
  último que regeneraba el `Dicto.spec` fantasma vía `--name "Dicto"`.
- Se borró `Dicto.spec`, que era **byte a byte idéntico** a `dicto.spec` y se
  colaba al correr PyInstaller con `--name Dicto`. En Windows, con filesystem
  *case-insensitive*, ambos son **el mismo fichero**, así que git lo veía
  modificado sin parar.
- Se quitó también la regla `/Dicto.spec` del `.gitignore`, que era
  **contraproducente**: en un filesystem case-insensitive git aplica el patrón
  sin distinguir mayúsculas, así que `/Dicto.spec` casa igualmente con
  `dicto.spec`, el spec de verdad (comprobado con `core.ignorecase=true`:
  `git check-ignore -v dicto.spec` lo daba por ignorado). Con `dicto.spec`
  trackeado no rompía nada, pero si alguna vez se destrackeaba en Windows se
  volvería invisible a `git add`. Ya no hace falta: no queda ninguna invocación
  con `--name Dicto` que pueda recrear el duplicado.

### La versión del instalador sale de pyproject.toml

`installer.iss` tenía `MyAppVersion` clavada a mano y se quedó en **2.5.1** con
el proyecto ya en 2.8.4. El CI la parcheaba al vuelo, así que el desfase solo
se veía en builds locales: `make installer` generaba un
`Dicto-2.5.1-setup.exe` que **el updater daba por bueno**, instalando una
"actualización" con número más bajo que la que ya corría.

Ahora `scripts/sync-installer-version.py` reescribe la línea desde
`pyproject.toml`, y lo llaman **tanto `make installer` como el CI** (el
workflow ya no lleva su propio regex de PowerShell). Es idempotente. No edites
`MyAppVersion` a mano.

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

El `libportaudio.so.2` que acaba en el bundle es el **del sistema de build**
(en Linux el wheel de `sounddevice` es `py3-none-any` y no trae ninguno:
PyInstaller lo recoge como dependencia de la libreria del sistema). En los
runners de CI ese PortAudio esta compilado **sin backend de PulseAudio**, y el
`libasound.so.2` que lo acompaña viaja sin sus modulos de `alsa-lib`. Si se
empaquetan, desaparecen los PCM `pulse`, `pipewire` y `default`: solo quedan
los `hw:` en acceso exclusivo, PipeWire ya tiene el micro cogido y grabar falla
con `Invalid sample rate [PaErrorCode -9997]`. En `uv run` no se nota porque
ahi se usa el PortAudio del sistema.

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

### Smoke tests en CI (lo que habría cazado el bug de v2.8.2)

El CI estuvo verde mientras publicaba un `.deb` con el micro muerto porque
**nunca ejecutaba lo que construía**. El job `build-linux` ahora corre tres
comprobaciones sobre el bundle, **antes** de empaquetar el `.deb`:

1. **`find dist/dicto -name 'libportaudio*'` (y `libasound*`, `libjack*`) debe
   salir vacío.** Es la aserción principal: determinista, no necesita servidor
   de audio y comprueba exactamente la regresión. Si el spec deja de excluir
   esas libs, el job falla aquí.
2. **`PulseAudio` entre los host APIs**, con la carpeta del bundle primera en
   `LD_LIBRARY_PATH`. Ojo: `Pa_Initialize()` **aborta** con `PaErrorCode -9999`
   si no hay servidor escuchando, así que el step arranca antes un daemon
   PulseAudio de mentira (`module-null-sink` + `module-null-source`, sin
   hardware). Es defensa en profundidad, **no** el guard principal: si el
   bundle vuelve a llevar un PortAudio copiado de una máquina cuyo PortAudio
   *sí* tiene Pulse, este check pasa aunque el `.deb` esté roto para el
   usuario. Por eso manda el punto 1.
3. **El binario arranca de verdad** bajo `xvfb-run`. La app abre una GUI y no
   termina sola, así que corre en background y se busca el banner
   `Dicto started!` (que `main.py` solo emite tras cablear settings,
   controller, tray, overlay y hotkeys). En cuanto aparece se la mata: un
   arranque sano tarda segundos. Hay `timeout --kill-after` y
   `timeout-minutes` en el job para que un Qt colgado no ocupe un runner 6h.

   El check negativo busca **`Failed to initialize components`**. Antes buscaba
   `Failed to start application`, que **no puede aparecer nunca**: esa cadena la
   loguea un `except Exception` de `main()`, pero el fallo de inicialización
   llama a `sys.exit(1)` → `SystemExit`, que no hereda de `Exception` y por tanto
   escapa a ese handler. Era un check muerto.

   El step corre desde un directorio temporal solo por higiene. El comentario
   decía que era porque la app escribe `config.yaml` en `$PWD`, y **es falso**:
   un build congelado resuelve la config a `~/.config/dicto/config.yaml` (ver
   `get_config_dir()` en `src/config/settings.py`).

## Tests en CI

El job `test` ejecuta `pytest -m "not api"` bajo `xvfb-run` (las suites de
`tests/ui` necesitan display). Hasta hace poco los tests **no se ejecutaban en
ningún workflow** pese a instalarse los dev extras.

El job es **obligatorio**: está en `release.needs`, así que una suite roja
**bloquea la release**. Llevó un `continue-on-error: true` temporal mientras
había 9 tests en rojo alrededor de v2.8.4; ya están arreglados y la suite pasa
entera (233 tests), así que el flag se ha quitado. No lo reintroduzcas para tapar
una regresión: arregla el test.

Se mantiene `timeout-minutes: 15` en el job. No es por los fallos, sino porque un
*cuelgue* no produce ningún exit code de error: sin el tope, un deadlock
ocuparía un runner las 6 h por defecto. Hoy la suite tarda ~33 s.

También se creía que `tests/unit/test_controller.py` se colgaba. **No se
reproduce**: pasa solo (23 tests) en unos segundos. Lo único que queda es una
línea benigna en stderr, `_pythonToCppCopy: Cannot copy-convert ... (MagicMock)
to C++`, que aparece al pasar un mock a la capa C++ de Qt y no falla ni bloquea
nada.

## Suelo de glibc

PyInstaller enlaza contra la glibc de la máquina de build y glibc solo es
compatible **hacia atrás**: la versión de quien construye es el suelo real de
quien instala.

- `build-linux` corre en **`ubuntu-22.04` fijo, no `ubuntu-latest`**.
  `ubuntu-latest` ya apunta a 24.04 (glibc 2.39), lo que dejaba fuera a Ubuntu
  22.04 (glibc 2.35) con un **segfault** en vez de un error de apt. Compilar en
  22.04 no cuesta nada (no usamos símbolos de 2.36+) y cubre ambas. Al subir
  este pin, hazlo a una versión concreta: nunca a una etiqueta flotante.
- `scripts/build-deb.sh` **declara el suelo en `Depends`** como
  `libc6 (>= 2.35)`, **clavado** en la constante `GLIBC_FLOOR`, que documenta la
  glibc del runner de CI. Así apt rechaza el paquete con un mensaje legible en
  vez de instalarlo para que reviente al arrancar.

### Por qué está clavado y no se calcula

Se probaron las dos alternativas "automáticas" y **las dos generan un `.deb`
peor**:

1. **Máximo de los tags `GLIBC_x.y` del bundle** (lo que se hacía hasta ahora).
   Asume que toda `.so` empaquetada se compiló contra la glibc más antigua
   soportada, y eso es falso para las libs que PyInstaller copia del sistema de
   build. Medido en Ubuntu 26.04: daba `libc6 (>= 2.43)`, y el
   `dicto_2.8.4_amd64.deb` resultante **no instalaba en 22.04, 24.04 ni 25.10**.
   Los tags 2.43 venían de `liblcms2`, `libglib-2.0` y sobre todo `libmvec.so.1`
   — que es la propia libm de glibc: sus tags solo reflejan la glibc del host,
   no lo que la app necesita. En CI el resultado era correcto **por casualidad**
   (en 22.04 nada puede declarar más de 2.35), así que el bug solo aparecía en
   `make deb` local: justo la divergencia local/CI que queríamos eliminar.
2. **`dpkg-shlibdeps`.** Es lo correcto para un paquete Debian normal, pero no
   para un bundle de PyInstaller, que es autocontenido por diseño. Ejecutado
   sobre este bundle: falla en duro con `cannot find library libtiff.so.5 needed
   by libqtiff.so` (Qt trae el plugin TIFF y ningún Ubuntu moderno tiene ya
   libtiff5); emite `libc6 (>> 2.43), libc6 (<< 2.44)`, o sea un **techo** que
   ata el paquete a la glibc exacta del host; y añade ~110 dependencias del host
   (`libqt6core6t64 (>= 6.10.2)`, `qt6-base-private-abi (= 6.10.2)`, …) para
   librerías que ya viajan **dentro** del bundle.

Conclusión: el suelo es un dato de **política de release** (en qué runner
compilamos), no algo inferible del artefacto. `GLIBC_FLOOR` y el `runs-on` del
job son el mismo hecho escrito en dos sitios; **si subes uno, sube el otro**.

Para builds locales en distros más nuevas el script emite un **aviso** (no un
error): ese `.deb` instalará en 22.04 y reventará al arrancar, porque sus
binarios sí necesitan una glibc mayor que la declarada. Sirve para probar en tu
máquina; lo que se publica sale del CI.
