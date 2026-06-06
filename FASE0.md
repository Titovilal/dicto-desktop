# Fase 0 — Andamiaje ✅

Reconstrucción desde cero. Código viejo en `Antiguo/` (ignorado en Git).

## Estructura `src/dicto/`

```
core/      lógica pura (sin Qt): state, events, models
config/    settings (pydantic) → %APPDATA%\dicto\config.yaml
i18n/      t() + locales en/es + señal languageChanged
ui/theme/  tokens → palettes (light/dark) → ThemeManager (sigue a Windows)
ui/        tray (ancla) + ventana vacía
app.py     DictoApp: arranca Qt, DI, wiring
utils/     logger (ring-buffer p/ reportes) + rutas Windows
```

**Principios:** capas no tipos · core sin Qt · color e idioma vía tokens, nunca hardcodeados.

## Levantar la app

```powershell
uv run dicto
```
## Verificado

- Arranca, abre ventana + bandeja, cierra limpio.
- Tema (claro/oscuro/sistema) e idioma (en/es) se refrescan **en caliente**.
- **25 tests verdes**: `pytest tests/unit/{test_state,test_theme,test_i18n}.py`

## Pendiente

- `webrtcvad`: necesita compilador C → usar wheel precompilada en Fase 1.
- `dicto.spec` / `installer.iss` / `build.yml` → Fase 7 (fuentes en `Antiguo/`).
