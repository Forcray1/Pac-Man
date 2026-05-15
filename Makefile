CODE = entities display core

install:
	uv sync

run:$
	uv run python -m pac-man config.json

debug:
	uv run python -m pdb pac-man config.json

clean:
	rm -rf .venv
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +

lint:
	uv run flake8 $(CODE) pac-man.py
	uv run mypy $(CODE) pac-man.py --explicit-package-bases --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	uv run flake8 $(CODE) pac-man.py
	uv run mypy $(CODE) pac-man.py --strict

%:
	@:

.PHONY: install run debug clean lint lint-strict