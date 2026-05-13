from __future__ import annotations  # to avoid circular import
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
import random

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

    def __init__(self, score: int, pos: tuple[int, int], cooldown: int = 2):
        super().__init__(pos)
        self.score: int = score
        self.spawn: tuple[int, int] = pos
        self.eatable: bool = False
        self.is_dead: bool = False
        self.cooldown: int = cooldown
        self._respawn_timer: int = 0
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
        if not self.active:
            if self._respawn_timer > 0:
                self._respawn_timer -= 1
            if self._respawn_timer == 0:
                self.active = True

        # If dead and has reached spawn, reactivate
        if self.is_dead and (self.x, self.y) == self.spawn:
            self.is_dead = False
            self.active = True
            self.eatable = False

    def reset(self) -> None:
        """
        Reset the ghost to its original state.
        """
        self.set_position(*self.spawn)
        self.eatable = False
        self.is_dead = False
        self.active = True

    @staticmethod
    def _heuristic(a: tuple[int, int], b: tuple[int, int]) -> float:
        """
        Manhattan distance between two positions.
        """
        return float(abs(a[0] - b[0]) + abs(a[1] - b[1]))

    @staticmethod
    def _reconstruct_path(
        came_from: dict[tuple, tuple],
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
        """
        if start == goal:
            return [start]

        rows = len(map)
        cols = len(map[0]) if rows else 0

        open_set: set[tuple[int, int]] = {start}
        came_from: dict[tuple, tuple] = {}

        g_score: dict[tuple, float] = {start: 0.0}
        f_score: dict[tuple, float] = {start: Ghost._heuristic(start, goal)}

        while open_set:
            current = min(open_set, key=lambda n: f_score.get(n, float("inf")))

            if current == goal:
                return Ghost._reconstruct_path(came_from, current)

            open_set.remove(current)

            cx, cy = current
            for (dx, dy) in _MASK:
                nx, ny = cx + dx, cy + dy

                # Forbid U-turn on the very first step
                if (current == start and forbidden_first_step and
                        (nx, ny) == forbidden_first_step):
                    continue

                if not (0 <= ny < rows and 0 <= nx < cols):
                    continue
                if map[ny][nx] == 1:  # Avoid strictly walls (1 = WALL)
                    continue
                neighbor = (nx, ny)
                tentative_g = g_score.get(current, float("inf")) + 1

                if tentative_g < g_score.get(neighbor, float("inf")):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + Ghost._heuristic(
                        neighbor,
                        goal)
                    open_set.add(neighbor)

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
                      ) -> list:
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
        # 1. First physically advance in the previous direction
        # (the one we just finished interpolating visually)
        rev_mask = {v: k for k, v in _MASK.items()}
        current_offset = rev_mask.get(self.direction)
        if current_offset:
            dx, dy = current_offset
            next_x, next_y = self.x + dx, self.y + dy
            # Make sure we don't walk into a wall (safety check)
            if map[next_y][next_x] != 1:
                self.set_position(next_x, next_y)
        else:
            return False

        # 2. Now compute the NEXT step from this new position
        forbidden_first_step = None

        if self.eatable and not self.is_dead:
            target = self.choose_target_feared(monitor)
            # choose_target_feared already updates self.direction
            # no need to recompute the path
            return True

        if self.is_dead:
            # If dead, it must rush back to spawn
            target = self.spawn
        else:
            try:
                target = self.choose_target(monitor)
            except Exception:
                raise Exception

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
            # If the ghost is stuck (e.g. dead-end), exceptionally allow
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

        # 3. Update self.direction for the NEXT interpolation
        ndx, ndy = nx - self.x, ny - self.y
        dir_str = _MASK.get((ndx, ndy))
        if dir_str:
            self.direction = dir_str

        self.current_path = path

        return True

    def draw(self) -> None:
        """
        Print the ghost each frame, to actualize the position in pygame window
        """
        pass
