run:
	uv run voice-to-clipboard

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
	pyinstaller --name "Voice-to-Clipboard" --onefile --windowed --noconfirm src/main.py

# Create release using version from pyproject.toml
release:
	gh workflow run build.yml -f create_release=true
	@echo "Release workflow triggered. Check GitHub Actions for progress."
