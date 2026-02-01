run:
	uv run dicto

clean:
	rmdir /s /q build dist 2>nul & del /q *.spec 2>nul & echo Done

format:
	uvx ruff format

lint:
	uvx ruff check

type:
	uvx ty check

build:
	uv pip install -e ".[dev]"
	pyinstaller --name "Dicto" --onefile --windowed --noconfirm --add-data "assets;assets" --icon "assets/icons/icon.ico" src/main.py

# Create release using version from pyproject.toml
release:
	gh workflow run build.yml -f create_release=true
	@echo "Release workflow triggered. Check GitHub Actions for progress."
