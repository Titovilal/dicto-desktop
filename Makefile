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
