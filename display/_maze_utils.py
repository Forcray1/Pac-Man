from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pygame

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "mazegenerator-00001-py3-none-any"))

# The maze generator uses recursion up to width*height deep.
# Raise the limit so large mazes don't hit Python's default cap of 1000.
sys.setrecursionlimit(10000)

_MAZE_PKG_DIR = os.path.join(_ROOT, "mazegenerator-00001-py3-none-any")
_MAZE_WHL = os.path.join(_ROOT, "mazegenerator-00001-py3-none-any.whl")

try:
    from mazegenerator.mazegenerator import MazeGenerator  # noqa: E402
except ModuleNotFoundError:
    # Not installed and not unpacked — try to unpack from the bundled wheel.
    if os.path.isfile(_MAZE_WHL):
        import zipfile
        print(
            f"[INFO] Unpacking mazegenerator from bundled wheel: {_MAZE_WHL}",
            file=sys.stderr,
        )
        try:
            with zipfile.ZipFile(_MAZE_WHL, "r") as zf:
                zf.extractall(_MAZE_PKG_DIR)
        except (zipfile.BadZipFile, OSError) as _exc:
            print(
                f"ERROR: Failed to unpack mazegenerator wheel: {_exc}",
                file=sys.stderr,
            )
            sys.exit(1)
        # The dir is now populated; sys.path already includes it (line above).
        try:
            from mazegenerator.mazegenerator import MazeGenerator  # noqa: E402
        except ImportError:
            print(
                "ERROR: mazegenerator was unpacked but 'MazeGenerator' "
                "could not be imported.\n"
                "  The wheel may be corrupted.",
                file=sys.stderr,
            )
            sys.exit(1)
    else:
        print(
            "ERROR: The 'mazegenerator' package was not found.\n"
            f"  Looked for unpacked dir : {_MAZE_PKG_DIR}\n"
            f"  Looked for wheel        : {_MAZE_WHL}\n"
            "  Restore one of those files to the project root.",
            file=sys.stderr,
        )
        sys.exit(1)
except ImportError:
    print(
        "ERROR: Could not import 'MazeGenerator' from the mazegenerator "
        "package.\n"
        f"  File: {os.path.join(_MAZE_PKG_DIR, 'mazegenerator', 'mazegenerator.py')}\n"
        "  The file may be empty or corrupted.",
        file=sys.stderr,
    )
    sys.exit(1)


class _FastMazeGenerator(MazeGenerator):
    """
    Subclass that skips the expensive iterative-deepening shortest-path
    search. The game never reads ``shortest_path``, so skipping it has no
    effect on gameplay while reducing large-maze generation from
    exponential time to linear.
    """

    def _find_short_path(self) -> None:
        pass  # Not used by the game; skip the costly IDDFS


# Cache for deterministic mazes: (width, height, seed) -> raw maze grid.
# Only populated when seed > 0 (seed = 0 means random, so not cacheable).
_maze_cache: dict[tuple[int, int, int], list[list[int]]] = {}


def _safe_font(path: str, size: int) -> "pygame.font.Font":
    """
    Load *path* as a pygame font at *size* points.
    Falls back to the system default font with a WARNING on stderr when
    the file is absent or unreadable.
    """
    import pygame
    try:
        return pygame.font.Font(path, size)
    except (FileNotFoundError, OSError, pygame.error) as exc:
        print(
            f"[WARNING] Font file not accessible: {path!r} "
            f"({type(exc).__name__}: {exc}) — using system fallback.",
            file=sys.stderr,
        )
        return pygame.font.SysFont(None, size)
