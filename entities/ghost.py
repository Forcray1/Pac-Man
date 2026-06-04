from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
import random
import sys

from entities.entity import Entity

if TYPE_CHECKING:
    from core.monitor import Monitor

_OPPOSITE: dict[str, str] = {
    "N": "S",
    "S": "N",
    "E": "W",
    "W": "E"
    }

_MASK: dict[tuple[int, int], str] = {
    (0, -1): "N",
    (0,  1): "S",
    (1,  0): "E",
    (-1, 0): "W",
}


class Ghost(Entity, ABC):
    """
    Abstract class for the four ghosts
    """

    def __init__(self, score: int, pos: tuple[int, int]):
        """
        Initialize a ghost at pos, which is also its spawn point.
        """
        super().__init__(pos)
        self.score: int = score
        self.spawn: tuple[int, int] = pos
        self.eatable: bool = False
        self.is_dead: bool = False
        self.direction: str = "S"
        self.current_path: list[tuple[int, int]] = []

    def is_eaten(self) -> None:
        """
        Called when Pac-Man eats this ghost.
        Deactivates eatable mode, marks as dead to rush back to spawn.
        """
        self.eatable = False
        self.is_dead = True
        # Keep active=True so it can move back to spawn

    def update(self) -> None:
        """
        Tick: check if reached spawn while dead, then reactivate.
        """
        if self.is_dead and (self.x, self.y) == self.spawn:
            self.is_dead = False
            self.active = True
            self.eatable = False

    def reset(self) -> None:
        """
        Reset the ghost to its original state, centred on its spawn tile
        with no leftover interpolation so it never drifts off the tile on
        the next READY! screen.
        """
        self.set_position(*self.spawn)
        self.eatable = False
        self.is_dead = False
        self.active = True
        self.direction = "S"
        self.move_accumulator = 0.0
        self.current_path = []

    @staticmethod
    def _heuristic(a: tuple[int, int], b: tuple[int, int]) -> float:
        """
        Manhattan distance between two positions.
        """
        return float(abs(a[0] - b[0]) + abs(a[1] - b[1]))

    @staticmethod
    def _reconstruct_path(
        came_from: dict[tuple[int, int], tuple[int, int]],
        current: tuple[int, int],
    ) -> list[tuple[int, int]]:
        """
        Reconstruct the path from the came_from dictionary.
        """
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        return path[::-1]

    @staticmethod
    def next_case(
        map: list[list[int]],
        start: tuple[int, int],
        goal: tuple[int, int],
        forbidden_first_step: tuple[int, int] | None = None
    ) -> list[tuple[int, int]]:
        """
        Return the shortest path to target through the map using A*.

        The result is the list of tiles from start to goal inclusive, or an
        empty list if goal is unreachable. forbidden_first_step blocks one
        specific neighbour of start (used to stop ghosts U-turning).
        """
        if start == goal:
            return [start]

        rows = len(map)
        cols = len(map[0]) if rows else 0

        # open_set: tiles discovered but not yet expanded (the A* frontier).
        # came_from: best predecessor of each tile, used to rebuild the path.
        open_set: set[tuple[int, int]] = {start}
        came_from: dict[tuple[int, int], tuple[int, int]] = {}

        # g_score: known cost from start to a tile (1 per step).
        # f_score: g_score + heuristic estimate of the cost left to the goal.
        g_score: dict[tuple[int, int], float] = {start: 0.0}
        f_score: dict[tuple[int, int], float] = {
            start: Ghost._heuristic(start, goal)
        }

        while open_set:
            # Expand the frontier tile that looks cheapest overall (lowest f).
            current = min(open_set, key=lambda n: f_score.get(n, float("inf")))

            # Reached the goal: walk came_from backwards into a path.
            if current == goal:
                return Ghost._reconstruct_path(came_from, current)

            open_set.remove(current)

            # Try each of the 4 orthogonal neighbours.
            cx, cy = current
            for (dx, dy) in _MASK:
                nx, ny = cx + dx, cy + dy

                # Forbid the banned U-turn, but only on the first step.
                if (current == start and forbidden_first_step and
                        (nx, ny) == forbidden_first_step):
                    continue

                # Skip out-of-bounds and wall tiles.
                if not (0 <= ny < rows and 0 <= nx < cols):
                    continue
                if map[ny][nx] == 1:  # Avoid strictly walls
                    continue
                neighbor = (nx, ny)
                # Cost to reach this neighbour through current (+1 step).
                tentative_g = g_score.get(current, float("inf")) + 1

                # Keep this route only if it beats any path found so far.
                if tentative_g < g_score.get(neighbor, float("inf")):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + Ghost._heuristic(
                        neighbor,
                        goal)
                    open_set.add(neighbor)

        # Frontier exhausted without reaching the goal: no path exists.
        return []

    @abstractmethod
    def choose_target(self, monitor: "Monitor") -> tuple[int, int]:
        """
        Choose the target cell: player pos, spawn, or flee position.
        """
        pass

    def possible_move(self,
                      pos: tuple[int, int],
                      monitor: "Monitor",
                      current: str | None = None
                      ) -> list[tuple[int, int]]:
        """
        Return the walkable neighbour tiles around pos. A U-turn against
        current is forbidden unless it is the only option available.
        """
        cx, cy = pos
        forbidden_dir = _OPPOSITE.get(current) if current else None
        reachable = []
        for (dx, dy), dir_str in _MASK.items():
            if dir_str == forbidden_dir:
                continue  # forbid the U turn
            nx, ny = cx + dx, cy + dy
            if not (0 <= ny < monitor.rows and 0 <= nx < monitor.cols):
                continue
            if monitor.grid[ny][nx] == 1:  # Avoid strictly walls (1 = WALL)
                continue
            reachable.append((nx, ny))
        # If U turn only possibility, fallback to it
        if not reachable:
            for (dx, dy) in _MASK:
                nx, ny = cx + dx, cy + dy
                if not (0 <= ny < monitor.rows and 0 <= nx < monitor.cols):
                    continue
                if monitor.grid[ny][nx] == 1:
                    continue
                reachable.append((nx, ny))
        return reachable

    def turn_back(self) -> None:
        """
        Immediately reverse the ghost's current direction.
        """
        rev_mask = {v: k for k, v in _MASK.items()}
        current_offset = rev_mask.get(self.direction)

        if current_offset:
            dx, dy = current_offset
            self.set_position(self.x + dx, self.y + dy)
            self.move_accumulator = max(0.0, 1.0 - self.move_accumulator)

        self.direction = _OPPOSITE.get(self.direction, self.direction)
        self.current_path = []

    def choose_target_feared(self, monitor: "Monitor") -> tuple[int, int]:
        """
        Pick a random walkable neighbour while the ghost is edible and update
        the current direction accordingly.
        """
        valid_neighbors = self.possible_move(self.pos, monitor, self.direction)
        if not valid_neighbors:
            return self.pos

        valid_dirs = []
        for nx, ny in valid_neighbors:
            dx, dy = nx - self.x, ny - self.y
            dir_str = _MASK.get((dx, dy))
            if dir_str:
                valid_dirs.append((dir_str, nx, ny))

        if not valid_dirs:
            return self.pos

        chosen = random.choice(valid_dirs)
        self.direction = chosen[0]
        return (chosen[1], chosen[2])

    def move(self, map: list[list[int]], monitor: "Monitor") -> bool:
        """
        Move one cell toward the target returned by choose_target.
        """
        # First physically advance in the previous direction
        rev_mask = {v: k for k, v in _MASK.items()}
        current_offset = rev_mask.get(self.direction)
        if current_offset:
            dx, dy = current_offset
            next_x, next_y = self.x + dx, self.y + dy
            # Make sure we don't walk into a wall
            if map[next_y][next_x] != 1:
                self.set_position(next_x, next_y)
        else:
            return False

        # Compute the next step from this new position
        forbidden_first_step = None

        if self.eatable and not self.is_dead:
            target = self.choose_target_feared(monitor)
            # choose_target_feared already updates self.direction
            return True

        if self.is_dead:
            # If dead, it must rush back to spawn
            target = self.spawn
        else:
            try:
                target = self.choose_target(monitor)
            except Exception as e:
                print(f"ERROR: Ghost target selection failed: {e}\n",
                      file=sys.stderr)
                return False

        if target is None:
            return False

        # Avoid U-turning immediately after advancing
        rev_dir = _OPPOSITE.get(self.direction)
        rev_offset = rev_mask.get(rev_dir) if rev_dir is not None else None

        if rev_offset and not self.is_dead:
            # dead ghost can U-turn immediately if needed to reach spawn faster
            rdx, rdy = rev_offset
            forbidden_first_step = (self.x + rdx, self.y + rdy)

        path = Ghost.next_case(map,
                               (self.x, self.y),
                               target,
                               forbidden_first_step)

        if not path or len(path) < 2:
            # If the ghost is stuck, exceptionally allow
            # a U-turn to escape.
            if forbidden_first_step is not None:
                path = Ghost.next_case(map, (self.x, self.y), target, None)

            if len(path) < 2:
                # If no path is found even with a U-turn,
                # try moving randomly to unblock it
                valid_neighbors = self.possible_move(self.pos, monitor, None)
                if valid_neighbors:
                    import random
                    nx, ny = random.choice(valid_neighbors)
                    path = [self.pos, (nx, ny)]
                else:
                    return False

        nx, ny = path[1]

        # Update self.direction for the next interpolation
        ndx, ndy = nx - self.x, ny - self.y
        dir_str = _MASK.get((ndx, ndy))
        if dir_str:
            self.direction = dir_str

        self.current_path = path

        return True
