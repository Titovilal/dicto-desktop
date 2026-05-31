# Dicto — task runner. Mirrors COMMANDS.md (Linux/macOS).
# Windows builds: see COMMANDS.md.

.DEFAULT_GOAL := help

# Windows sets OS=Windows_NT; used to guard the .exe targets.
IS_WINDOWS := $(filter Windows_NT,$(OS))

.PHONY: help run format lint typecheck dev-deps \
        build build-onefile deb exe exe-onefile installer clean clean-deb release

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

dev-deps: ## Install dev dependencies (required before building)
	uv pip install -e ".[dev]"

# ── Build (PyInstaller, Linux/macOS) ─────────────────────────
build: dev-deps ## Build onedir bundle (recommended)
	uv run pyinstaller --name "Dicto" --onedir --windowed --noconfirm --copy-metadata dicto \
		--add-data "assets:assets" --add-data "src/ui/assets:src/ui/assets" \
		--hidden-import dbus_next src/main.py

build-onefile: dev-deps ## Build single-file executable
	uv run pyinstaller --name "Dicto" --onefile --windowed --noconfirm --copy-metadata dicto \
		--add-data "assets:assets" --add-data "src/ui/assets:src/ui/assets" \
		--hidden-import dbus_next src/main.py

# ── Linux .deb ───────────────────────────────────────────────
deb: ## Build the Linux .deb (PyInstaller + package) into dist/
	bash scripts/build-deb.sh

# ── Windows .exe (must run ON Windows — PyInstaller has no cross-compile) ──
exe: ## Build the Windows .exe (onedir) — run on Windows
ifndef IS_WINDOWS
	@echo "ERROR: 'make exe' must run on Windows. PyInstaller cannot cross-compile a Windows .exe from Linux/macOS."
	@echo "       Use 'make deb' on Linux, or let GitHub Actions build it ('make release')."
	@exit 1
endif
	$(MAKE) dev-deps
	uv run pyinstaller --name "Dicto" --onedir --windowed --noconfirm --copy-metadata dicto \
		--add-data "assets;assets" --add-data "src/ui/assets;src/ui/assets" \
		--icon "assets/icons/icon.ico" src/main.py

exe-onefile: ## Build the Windows .exe (single file) — run on Windows
ifndef IS_WINDOWS
	@echo "ERROR: 'make exe-onefile' must run on Windows (no cross-compile)."
	@exit 1
endif
	$(MAKE) dev-deps
	uv run pyinstaller --name "Dicto" --onefile --windowed --noconfirm --copy-metadata dicto \
		--add-data "assets;assets" --add-data "src/ui/assets;src/ui/assets" \
		--icon "assets/icons/icon.ico" src/main.py

installer: exe ## Build the Windows installer (.exe via Inno Setup) — run on Windows
ifndef IS_WINDOWS
	@echo "ERROR: 'make installer' must run on Windows (needs Inno Setup ISCC.exe)."
	@exit 1
endif
	"C:/Program Files (x86)/Inno Setup 6/ISCC.exe" installer.iss

# ── Clean ────────────────────────────────────────────────────
clean: ## Remove build artifacts (keeps tracked Dicto.spec)
	rm -rf build dist

clean-deb: ## Remove only the .deb artifacts
	rm -f dist/*.deb

# ── Release ──────────────────────────────────────────────────
release: ## Trigger the GitHub Actions release workflow
	gh workflow run build.yml -f create_release=true
