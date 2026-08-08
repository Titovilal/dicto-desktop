# Releasing

Guia para crear nuevos releases de Dicto Desktop.

## Proceso de release

### 1. Actualizar la version

Edita el campo `version` en `pyproject.toml`:

```toml
[project]
version = "2.2.0"
```

### 2. Hacer commit y push a main

```bash
git add pyproject.toml
git commit -m "bump version to 2.2.0"
git push origin main
```

### 3. Crear el release

Hay dos formas de disparar el workflow de release:

#### Opcion A: Disparar el workflow manualmente

```bash
gh workflow run build.yml -f create_release=true
```

#### Opcion B: Crear un tag manualmente

```bash
git tag v2.2.0
git push origin v2.2.0
```

> **Nota:** El workflow NO se ejecuta automaticamente con cada push a main. Solo se dispara manualmente o al pushear un tag `v*`.

## Que hace el workflow

El workflow (`.github/workflows/build.yml`) ejecuta estos pasos:

1. **version** — Lee la version de `pyproject.toml` y verifica si ya existe un tag `v{version}`
2. **test** — Ejecuta `pytest -m "not api"` bajo `xvfb-run`. **Bloquea la release**: esta en `release.needs`, asi que si la suite se pone roja no se publica nada
3. **build** — Compila el ejecutable con PyInstaller en paralelo para:
   - **Windows** — instalador `.exe` (Inno Setup)
   - **Linux** — bundle `.tar.gz` portable y paquete `.deb` instalable. Antes de empaquetar corre unos smoke tests sobre el bundle (ver `.ctx/docs/release.md`)
4. **release** — Si corresponde, crea un GitHub Release con tag `v{version}` y adjunta los binarios

## Artefactos generados

| Plataforma | Archivo                          | Uso                              |
|------------|----------------------------------|----------------------------------|
| Windows    | `Dicto-<version>-setup.exe`      | Instalador                       |
| Linux      | `dicto-linux-amd64.tar.gz`       | Portable (descomprimir y ejecutar)|
| Linux      | `dicto_<version>_amd64.deb`      | Instalable con `sudo apt install`|

## Build local

Para generar el ejecutable localmente ver los comandos en `COMMANDS.md` (o usa el `Makefile`: `make exe` en Windows, `make deb` en Linux). Los builds son **onedir**, asi que en Windows el binario queda en `dist/Dicto/Dicto.exe` (dentro de su carpeta, no suelto en `dist/`); en Linux el paquete queda en `dist/dicto_<version>_amd64.deb`.

## Checklist pre-release

- [ ] Version actualizada en `pyproject.toml`
- [ ] Tests pasan (`uv run pytest -m "not api"`, o `make test`) — el marcador `api` excluye los tests que llaman a la API real, que necesitan credenciales y red

- [ ] Linting limpio (`uvx ruff check`)
- [ ] Formato correcto (`uvx ruff format`)
- [ ] Cambios commiteados y pusheados a `main`

## Versionado

El proyecto usa [Semantic Versioning](https://semver.org/):

- **MAJOR** — cambios incompatibles en la API o funcionalidad
- **MINOR** — nueva funcionalidad compatible hacia atras
- **PATCH** — correcciones de bugs
