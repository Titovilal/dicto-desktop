# Dicto — task runner. Mirrors COMMANDS.md (Windows).

.DEFAULT_GOAL := help

.PHONY: help run format lint typecheck dev-deps \
        exe exe-onefile installer clean release

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

# ── Windows .exe ─────────────────────────────────────────────
exe: dev-deps ## Build the Windows .exe (onedir)
	uv run pyinstaller --name "Dicto" --onedir --windowed --noconfirm --copy-metadata dicto \
		--add-data "assets;assets" --add-data "src/ui/assets;src/ui/assets" \
		--icon "assets/icons/icon.ico" src/main.py

exe-onefile: dev-deps ## Build the Windows .exe (single file)
	uv run pyinstaller --name "Dicto" --onefile --windowed --noconfirm --copy-metadata dicto \
		--add-data "assets;assets" --add-data "src/ui/assets;src/ui/assets" \
		--icon "assets/icons/icon.ico" src/main.py

installer: exe ## Build the Windows installer (.exe via Inno Setup)
	"C:/Program Files (x86)/Inno Setup 6/ISCC.exe" installer.iss

# ── Clean ────────────────────────────────────────────────────
clean: ## Remove build artifacts (keeps tracked dicto.spec)
	rm -rf build dist

# ── Release ──────────────────────────────────────────────────
release: ## Trigger the GitHub Actions release workflow
	gh workflow run build.yml -f create_release=true
