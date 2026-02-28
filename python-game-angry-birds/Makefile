# Angry Birds (Python) — lint and test
# Run from project root: make lint, make test

.PHONY: lint test install-dev

# Lint: check and format with Ruff (line length 88)
lint:
	ruff check src/
	ruff format --check src/

# Test: run pytest with src on PYTHONPATH so game modules are importable
test:
	PYTHONPATH=src pytest tests/ -v

# Install dev dependencies (ruff, pytest)
install-dev:
	pip install -r requirements-dev.txt
