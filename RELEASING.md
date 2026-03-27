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

#### Opcion A: Usando el Makefile (recomendado)

```bash
make release
```

Esto ejecuta `gh workflow run build.yml -f create_release=true` para disparar el workflow manualmente.

#### Opcion B: Crear un tag manualmente

```bash
git tag v2.2.0
git push origin v2.2.0
```

> **Nota:** El workflow NO se ejecuta automaticamente con cada push a main. Solo se dispara manualmente o al pushear un tag `v*`.

## Que hace el workflow

El workflow (`.github/workflows/build.yml`) ejecuta estos pasos:

1. **version** — Lee la version de `pyproject.toml` y verifica si ya existe un tag `v{version}`
2. **build** — Compila el ejecutable con PyInstaller en paralelo para:
   - **Windows** (`dicto-windows-amd64.exe`)
   - **Linux** (`dicto-linux-amd64`)
3. **release** — Si corresponde, crea un GitHub Release con tag `v{version}` y adjunta los binarios

## Artefactos generados

| Plataforma | Archivo                    |
|------------|----------------------------|
| Windows    | `dicto-windows-amd64.exe`  |
| Linux      | `dicto-linux-amd64`        |

## Build local

Para generar el ejecutable localmente (solo Windows):

```bash
make build
```

Esto instala las dependencias de desarrollo y ejecuta PyInstaller. El binario queda en `dist/Dicto.exe`.

## Checklist pre-release

- [ ] Version actualizada en `pyproject.toml`
- [ ] Tests pasan (`pytest`)
- [ ] Linting limpio (`make lint`)
- [ ] Formato correcto (`make format`)
- [ ] Cambios commiteados y pusheados a `main`

## Versionado

El proyecto usa [Semantic Versioning](https://semver.org/):

- **MAJOR** — cambios incompatibles en la API o funcionalidad
- **MINOR** — nueva funcionalidad compatible hacia atras
- **PATCH** — correcciones de bugs
