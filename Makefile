run:
	uv run dicto

clean:
ifeq ($(OS),Windows_NT)
	rmdir /s /q build dist 2>nul & del /q *.spec 2>nul & echo Done
else
	rm -rf build dist *.spec && echo Done
endif

format:
	uvx ruff format

lint:
	uvx ruff check

type:
	uvx ty check

build:
	uv pip install -e ".[dev]"
ifeq ($(OS),Windows_NT)
	pyinstaller --name "Dicto" --onefile --windowed --noconfirm --add-data "assets;assets" --add-data "src/ui/assets;src/ui/assets" --icon "assets/icons/icon.ico" src/main.py
else
	pyinstaller --name "Dicto" --onefile --windowed --noconfirm --add-data "assets:assets" --add-data "src/ui/assets:src/ui/assets" --icon "assets/icons/icon.svg" src/main.py
endif

# Create release using version from pyproject.toml
release:
	gh workflow run build.yml -f create_release=true
	@echo "Release workflow triggered. Check GitHub Actions for progress."
