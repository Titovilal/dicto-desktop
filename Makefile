# Dicto — task runner. Mirrors COMMANDS.md (Linux/macOS).
# Windows builds: see COMMANDS.md.

.DEFAULT_GOAL := help

# Windows sets OS=Windows_NT; used to guard the .exe targets.
IS_WINDOWS := $(filter Windows_NT,$(OS))

.PHONY: help run format lint typecheck dev-deps test \
        build deb exe installer clean clean-deb release

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

# ── Dev ──────────────────────────────────────────────────────
run: ## Run the app
	uv run dicto

format: ## Format code
	uvx ruff format

lint: ## Lint code
	uvx ruff check

typecheck: ## Type check
	uvx ty check

test: ## Run the test suite (skips tests that hit the real API)
	uv run pytest -m "not api"

dev-deps: ## Install dev dependencies (required before building)
	uv pip install -e ".[dev]"

# ── Build (PyInstaller, Linux/macOS) ─────────────────────────
build: dev-deps ## Build onedir bundle (recommended)
	uv run pyinstaller --noconfirm dicto-linux.spec

# `build-onefile` was removed, like its Windows twin `exe-onefile`. It was the
# last caller of PyInstaller with loose flags instead of the spec, which is the
# exact pattern that shipped a dead microphone in v2.8.2: it bypassed
# dicto-linux.spec and therefore its libportaudio/libasound exclusions. It was
# also the last thing that regenerated the phantom `Dicto.spec` (via
# `--name "Dicto"`). Nothing consumed the onefile output -- the .deb and the
# portable tarball are both built from the onedir bundle. If a onefile build is
# ever needed again, add it as a spec, not as flags.

# ── Linux .deb ───────────────────────────────────────────────
deb: ## Build the Linux .deb (PyInstaller + package) into dist/
	bash scripts/build-deb.sh

# ── Windows .exe (must run ON Windows — PyInstaller has no cross-compile) ──
# Uses the committed dicto.spec, exactly like the CI does. Passing loose flags
# here instead silently diverged from the spec: that is how the Linux .deb
# shipped with a dead microphone in v2.8.2, just mirrored to Windows.
# If a build option is needed, it goes in the spec so both paths inherit it.
#
# `exe-onefile` was removed rather than ported: nothing referenced it, the
# installer only consumes the onedir layout (dist/Dicto/), and a onefile build
# has slow startup plus more antivirus false positives. One less build path to
# keep in sync is worth more than a target nobody ran.
#
# El guard es la receta ENTERA bajo `ifndef`, con los comandos reales en el
# `else`. Tenerlo como primeras líneas de una receta única no aborta: `@exit 1`
# falla ese comando, pero make sigue ejecutando el resto de la receta, así que
# en Linux se llegaba a `uv run pyinstaller --noconfirm dicto.spec` y se
# intentaba un build de Windows con la ruta `src\main.py` del spec en vez de
# fallar limpiamente. Verificado con `make -n installer`.
exe: ## Build the Windows .exe (onedir) — run on Windows
ifndef IS_WINDOWS
	@echo "ERROR: 'make exe' must run on Windows. PyInstaller cannot cross-compile a Windows .exe from Linux/macOS."
	@echo "       Use 'make deb' on Linux, or let GitHub Actions build it ('make release')."
	@exit 1
else
	$(MAKE) dev-deps
	uv run pyinstaller --noconfirm dicto.spec
endif

installer: exe ## Build the Windows installer (.exe via Inno Setup) — run on Windows
ifndef IS_WINDOWS
	@echo "ERROR: 'make installer' must run on Windows (needs Inno Setup ISCC.exe)."
	@exit 1
else
	uv run python scripts/sync-installer-version.py
	"C:/Program Files (x86)/Inno Setup 6/ISCC.exe" installer.iss
endif

# ── Clean ────────────────────────────────────────────────────
clean: ## Remove build artifacts
	rm -rf build dist

clean-deb: ## Remove only the .deb artifacts
	rm -f dist/*.deb

# ── Release ──────────────────────────────────────────────────
release: ## Trigger the GitHub Actions release workflow
	gh workflow run build.yml -f create_release=true
