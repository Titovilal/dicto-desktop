# Release

Cómo publicar una release de Dicto Desktop. El instalador de Windows lo produce
GitHub Actions; no hay build local de releases.

## Cómo se dispara el CI

El workflow (`.github/workflows/build.yml`) se dispara al hacer `push` de un tag `v*`:

```yaml
on:
  push:
    tags: ['v*']
```

El job `build-windows` compila el ejecutable con PyInstaller y lo empaqueta en el
instalador `Dicto-<ver>-setup.exe` (Inno Setup), y la release lo adjunta. El
[updater](services.md) (`src/services/updater.py`) consume el asset `setup.exe`
de la release `latest`.

## Pasos

### 1. Sube la versión

El tag y la release salen de `pyproject.toml`. Edita:

```toml
version = "2.7.3"
```

Sincroniza también `src/version.py` si aplica, y commitea antes de publicar.

### 2. Publica

```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

El push del tag dispara el CI, que construye el `setup.exe` y crea la release.
Alternativamente, dispara el workflow manualmente:

```bash
gh workflow run build.yml -f create_release=true
```

### 3. Verifica desde la app

La app instalada detecta la nueva `latest`, descarga el `setup.exe` y lo ejecuta
en modo silencioso. Ver flujo en [`services.md`](services.md) y
`src/ui/main_window_updates.py`.

## Re-publicar la misma versión

`gh release create` falla si el tag ya existe. Para rehacerla:

```bash
gh release delete vX.Y.Z --repo Titovilal/dicto-desktop --cleanup-tag --yes
git tag vX.Y.Z
git push origin vX.Y.Z
```
