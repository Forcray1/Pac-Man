from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "mazegenerator-00001-py3-none-any"))

from mazegenerator.mazegenerator import MazeGenerator  # noqa: E402


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
