MODULE = pac-man
CODE = entities display core

install:
	uv sync

run:$
	uv run python -m $(MODULE) config.json

debug:
	uv run python -m pdb $(MODULE) config.json

clean:
	rm -rf .venv
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +

lint:
	uv run flake8 $(CODE) $(MODULE)
	uv run mypy $(CODE) $(MODULE) --explicit-package-bases --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	uv run flake8 $(CODE) $(MODULE)
	uv run mypy $(CODE) $(MODULE) --strict

%:
	@:

.PHONY: install run debug clean lint lint-strict