from typing import Any, TYPE_CHECKING

from entities.ghost import Ghost

if TYPE_CHECKING:
    from core.monitor import Monitor


class Blinky(Ghost):
    """
    Red ghost — directly chases Pac-Man.
    """

    def __init__(self,
                 pos: tuple[int, int],
                 cooldown: int = 2,
                 sprite: Any = None):
        super().__init__(score=200, pos=pos, cooldown=cooldown)
        self.sprite = sprite

    def choose_target(self, monitor: "Monitor") -> tuple[int, int]:
        return (monitor.player.x, monitor.player.y)


class Pinky(Ghost):
    """
    Pink ghost — targets 4 cells ahead of Pac-Man.
    """

    def __init__(self,
                 pos: tuple[int, int],
                 cooldown: int = 2,
                 sprite: Any = None):
        super().__init__(score=400, pos=pos, cooldown=cooldown)
        self.sprite = sprite

    def choose_target(self, monitor: "Monitor") -> tuple[int, int]:
        dx, dy = monitor.player.direction
        # Original Pac-Man bug: when moving UP, it also targets LEFT
        dx_offset = dx
        if dx == 0 and dy == -1:
            dx_offset = -1

        tx = monitor.player.x + dx_offset * 4
        ty = monitor.player.y + dy * 4
        # If the projected cell is unreachable, fallback to direct chase
        rows = len(monitor.grid)
        cols = len(monitor.grid[0]) if rows else 0
        if not (
                0 <= ty < rows and 0 <= tx < cols
                ) or monitor.grid[ty][tx] != 0:
            return (monitor.player.x, monitor.player.y)
        return (tx, ty)


class Inky(Ghost):
    """
    Blue ghost — targets a point reflected through Blinky relative to
    2 cells ahead of Pac-Man.
    """

    def __init__(self,
                 pos: tuple[int, int],
                 cooldown: int = 2,
                 sprite: Any = None):
        super().__init__(score=800, pos=pos, cooldown=cooldown)
        self.sprite = sprite

    def choose_target(self, monitor: "Monitor") -> tuple[int, int]:
        blinky = monitor.get_ghost(Blinky)
        if blinky is not None and blinky.active:
            dx, dy = monitor.player.direction
            # Original Pac-Man bug: when moving UP, it also offsets LEFT
            dx_offset = dx
            if dx == 0 and dy == -1:
                dx_offset = -1

            pivot_x = monitor.player.x + dx_offset * 2
            pivot_y = monitor.player.y + dy * 2

            # Reflect Blinky through the pivot
            target_x = pivot_x + (pivot_x - blinky.x)
            target_y = pivot_y + (pivot_y - blinky.y)

            # Clamp to grid bounds
            rows = monitor.rows
            cols = monitor.cols
            target_x = max(0, min(cols - 1, target_x))
            target_y = max(0, min(rows - 1, target_y))

            # Fall back to player if target is a wall
            if monitor.grid[target_y][target_x] == 1:
                return (monitor.player.x, monitor.player.y)
            return (target_x, target_y)
        else:
            return (monitor.player.x, monitor.player.y)


class Clyde(Ghost):
    """
    Orange ghost — chases when far (>8 tiles), retreats to spawn when close.
    """
    CHASE_THRESHOLD = 8

    def __init__(self,
                 pos: tuple[int, int],
                 cooldown: int = 2,
                 sprite: Any = None):
        super().__init__(score=200, pos=pos, cooldown=cooldown)
        self.sprite = sprite

    def choose_target(self, monitor: "Monitor") -> tuple[int, int]:
        # Using heuristic to determine if we should chase or scatter
        dist = Ghost._heuristic((self.x, self.y),
                                (monitor.player.x, monitor.player.y))

        # When scattering, pick a static flee corner (bottom-left) instead
        # of their exact spawn which might be dynamic, or they might get
        # stuck dancing if distance toggles at 8.
        if dist > self.CHASE_THRESHOLD:
            return (monitor.player.x, monitor.player.y)

        # Scatter corner for Clyde is bottom left
        rows = len(monitor.grid)
        return (1, rows - 2)
