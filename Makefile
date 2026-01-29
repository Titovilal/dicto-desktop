# Comandos: make run | make build | make clean | make format | make lint | make type

run:
	uv run voice-to-clipboard

build:
	uv run pyinstaller --name "VoiceToClipboard" --windowed --onefile --clean src/main.py

clean:
	rmdir /s /q build dist 2>nul & del /q *.spec 2>nul & echo Done

format:
	uvx ruff format

lint:
	uvx ruff check

type:
	uvx ty check
