CODE = entities display core

# PyInstaller's --add-data separator: ':' on macOS/Linux, ';' on Windows.
# Detected via the OS env var, which Windows sets to 'Windows_NT'.
ifeq ($(OS),Windows_NT)
DATA_SEP := ;
else
DATA_SEP := :
endif

install:
	uv sync

run:
	uv run python pac-man.py config.json

debug:
	uv run python -m pdb pac-man.py config.json

clean:
	rm -rf .venv build dist
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +

lint:
	uv run flake8 $(CODE) pac-man.py
	uv run mypy $(CODE) pac-man.py --explicit-package-bases --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	uv run flake8 $(CODE) pac-man.py
	uv run mypy $(CODE) pac-man.py --strict --explicit-package-bases

package:
	uv run pyinstaller \
		--name pac-man \
		--onedir \
		--windowed \
		--clean \
		--noconfirm \
		--paths mazegenerator-00001-py3-none-any \
		--add-data "assets$(DATA_SEP)assets" \
		--add-data "animation$(DATA_SEP)animation" \
		--add-data "config$(DATA_SEP)config" \
		--add-data "scores$(DATA_SEP)scores" \
		pac-man.py

%:
	@:

.PHONY: install run debug clean lint lint-strict package