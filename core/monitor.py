import sys
from typing import Any

from entities.player import PacMan
from entities.ghost import Ghost
from entities.ghost_types import Blinky, Inky, Pinky, Clyde
from entities.items import Pacgum, SuperPacgum
from display._maze_utils import MazeGenerator
from core.sounds import get_sounds

EMPTY = 0
WALL = 1
PACGUM = 2
SUPER_PACGUM = 3

BASE_SPEED = 0.15
POWER_BOOST = 1.2
GHOST_DEAD_SPEED = 2.0
GHOST_EATABLE_SPEED = 0.75
ELROY_CRITICAL = 0.10
ELROY_CRITICAL_SPEED = 1.20
ELROY_WARN = 0.25
ELROY_WARN_SPEED = 1.10


def _build_bool_wall_grid(
    raw_maze: list[list[int]],
    maze_width: int,
    maze_height: int,
    w_ext: int,
    h_ext: int,
) -> list[list[bool]]:
    """
    Convert a MazeGenerator raw maze into a True-is-wall boolean grid
    sized (h_ext x w_ext). Cells in raw_maze are 4-bit bitmasks: bit
    0=N, 1=E, 2=S, 3=W indicating a closed wall on that side.
    """
    bool_grid = [[True] * w_ext for _ in range(h_ext)]
    for y in range(maze_height):
        for x in range(maze_width):
            cell_val = raw_maze[y][x]
            gx, gy = x * 2 + 1, y * 2 + 1
            bool_grid[gy][gx] = (cell_val == 15)
            if (cell_val & 1) == 0:
                bool_grid[gy - 1][gx] = False  # N
            if (cell_val & 2) == 0:
                bool_grid[gy][gx + 1] = False  # E
            if (cell_val & 4) == 0:
                bool_grid[gy + 1][gx] = False  # S
            if (cell_val & 8) == 0:
                bool_grid[gy][gx - 1] = False  # W
    return bool_grid


def _closest(
    cells: list[tuple[int, int]], target: tuple[int, int]
) -> tuple[int, int]:
    """
    Return the cell from cells with the smallest Manhattan distance
    to target.
    """
    tx, ty = target
    return min(cells, key=lambda c: abs(c[0] - tx) + abs(c[1] - ty))


class Monitor:
    """
    Central manager for the entire game state.

    Holds the maze grid, all pac-gums, all ghosts and the player.
    Every system (renderer, game loop, AI) should go through Monitor
    rather than manipulating entities directly.
    """

    def __init__(
        self,
        grid: list[list[int]],
        player: PacMan,
        ghosts: list[Ghost] | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize the monitor with the maze *grid*, the *player*, and the
        optional list of *ghosts*. Pac-gum and super pac-gum objects are
        extracted from the grid on the fly.
        """
        self.grid: list[list[int]] = grid
        self.rows: int = len(grid)
        self.cols: int = len(grid[0]) if self.rows else 0

        self.player: PacMan = player
        self.ghosts: list[Ghost] = ghosts if ghosts is not None else []
        self.config: dict[str, Any] = config if config is not None else {}

        self.pacgums: list[Pacgum] = []
        self.super_pacgums: list[SuperPacgum] = []
        self._parse_items()
        self.start_pacgums: int = len(self.pacgums)
        self.difficulty: int = self.config.get("difficulty", 0)
        self.level: int = self.config.get("level", 0)
        self.ghosts_frozen: bool = False
        self.collision: bool = True
        self._dot_toggle: int = 0

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def from_maze(
        cls,
        raw_maze: list[list[int]],
        maze_width: int,
        maze_height: int,
        config: dict[str, Any] | None = None,
    ) -> "Monitor":
        """
        Build a Monitor directly from a MazeGenerator raw maze.
        """
        if config is None:
            config = {}

        w_ext = 2 * maze_width + 1
        h_ext = 2 * maze_height + 1

        bool_grid = _build_bool_wall_grid(
            raw_maze, maze_width, maze_height, w_ext, h_ext)

        all_walkable = [
            (x, y) for y in range(h_ext) for x in range(w_ext)
            if not bool_grid[y][x]
        ]

        # Player spawn at the centre; ghosts at the four corners.
        player_pos = _closest(all_walkable, (w_ext // 2, h_ext // 2))
        corner_targets = [
            (1, 1), (w_ext - 2, 1),
            (1, h_ext - 2), (w_ext - 2, h_ext - 2),
        ]
        ghost_points = [_closest(all_walkable, t) for t in corner_targets]

        empty_cells = [c for c in all_walkable if c != player_pos]
        super_positions = {_closest(empty_cells, t) for t in corner_targets}

        int_grid = [
            [WALL if bool_grid[y][x] else EMPTY for x in range(w_ext)]
            for y in range(h_ext)
        ]
        for (x, y) in empty_cells:
            int_grid[y][x] = (
                SUPER_PACGUM if (x, y) in super_positions else PACGUM)

        ghosts = [
            Blinky(ghost_points[0], sprite="&"),
            Pinky(ghost_points[1], sprite="&"),
            Inky(ghost_points[2], sprite="&"),
            Clyde(ghost_points[3], sprite="&"),
        ]

        super_duration = int(config.get("super_time", 8)) * 1000
        player = PacMan(
            player_pos[0], player_pos[1], power_duration=super_duration)
        monitor = cls(int_grid, player, ghosts=ghosts, config=config)

        pacgum_points = config.get("p_pacgums", 10)
        super_points = config.get("p_Spacgums", 50)
        for gum in monitor.pacgums:
            gum.points = pacgum_points
        for sgum in monitor.super_pacgums:
            sgum.points = super_points

        return monitor

    def _change_maze(self) -> None:
        """
        Regenerate the maze in place while preserving the position of every
        entity and remaining pac-gum.
        """
        import random

        maze_width = (self.cols - 1) // 2
        maze_height = (self.rows - 1) // 2

        generator = MazeGenerator(
            size=(maze_width, maze_height),
            perfect=False,
            seed=random.randint(1, 999_999),
        )
        bool_grid = _build_bool_wall_grid(
            generator.maze, maze_width, maze_height, self.cols, self.rows)

        # Force every occupied tile to remain walkable so nothing gets stuck.
        active_gums = [g for g in self.pacgums if g.active]
        active_sgums = [g for g in self.super_pacgums if g.active]
        occupied = (
            [(self.player.x, self.player.y)]
            + [(g.x, g.y) for g in self.ghosts]
            + [(g.x, g.y) for g in active_gums]
            + [(g.x, g.y) for g in active_sgums]
        )
        for x, y in occupied:
            bool_grid[y][x] = False

        new_grid = [
            [WALL if bool_grid[y][x] else EMPTY for x in range(self.cols)]
            for y in range(self.rows)
        ]
        for gum in active_gums:
            new_grid[gum.y][gum.x] = PACGUM
        for sgum in active_sgums:
            new_grid[sgum.y][sgum.x] = SUPER_PACGUM

        self.grid = new_grid

    def _parse_items(self) -> None:
        """
        Scan the grid and instantiate pac-gum objects for every matching cell.
        """
        for row in range(self.rows):
            for col in range(self.cols):
                if self.grid[row][col] == PACGUM:
                    self.pacgums.append(Pacgum(col, row))
                elif self.grid[row][col] == SUPER_PACGUM:
                    self.super_pacgums.append(SuperPacgum(col, row))

    def get_ghost(self, ghost_type: type) -> Ghost | None:
        """
        Return the first ghost instance of the given type, or None.
        """
        for ghost in self.ghosts:
            if isinstance(ghost, ghost_type):
                return ghost
        return None

    @property
    def all_items(self) -> list[Pacgum | SuperPacgum]:
        """
        All remaining active pac-gums and super pac-gums.
        """
        return [g for g in self.pacgums + self.super_pacgums if g.active]

    @property
    def active_ghosts(self) -> list[Ghost]:
        """
        Ghosts that are currently active (not waiting to respawn).
        """
        return [g for g in self.ghosts if g.active]

    def _difficulty_factor(self) -> float:
        """
        Multiplier applied to every ghost's speed based on difficulty.
        """
        if self.difficulty == 1:
            return 1.0
        if self.difficulty <= 3:
            return 1.10
        return 1.25

    def _ghost_speed(self, ghost: Ghost, remaining_ratio: float) -> float:
        """
        Compute the per-frame speed multiplier for a ghost given the
        share of pac-gums still on the board.
        """
        factor = self._difficulty_factor()
        if ghost.is_dead:
            return BASE_SPEED * GHOST_DEAD_SPEED * factor
        if ghost.eatable:
            return BASE_SPEED * GHOST_EATABLE_SPEED * factor
        if isinstance(ghost, Blinky):
            if remaining_ratio <= ELROY_CRITICAL:
                return BASE_SPEED * ELROY_CRITICAL_SPEED
            if remaining_ratio <= ELROY_WARN:
                return BASE_SPEED * ELROY_WARN_SPEED
        return BASE_SPEED * factor

    def _advance_ghost(self, ghost: Ghost) -> None:
        """
        Step a ghost forward by its current speed multiplier, consuming
        as many whole-tile moves as the accumulator allows.
        """
        ghost.move_accumulator += ghost.speed_multiplier
        while ghost.move_accumulator >= 1.0:
            try:
                ghost.move(self.grid, self)
            except Exception as e:
                print(f"ERROR: Ghost movement failed: {e}\n",
                      file=sys.stderr)
                break
            ghost.move_accumulator -= 1.0

    def update(self, dt_ms: int = 0) -> None:
        """
        Tick every entity managed by the monitor. *dt_ms* is the real time
        elapsed since the previous tick (milliseconds); it is forwarded to
        every entity so timers count down in wall-clock time, not in frames.
        """
        self.player.prev_pos = self.player.pos
        for ghost in self.active_ghosts:
            ghost.prev_pos = ghost.pos

        self.player.update(dt_ms)
        for ghost in self.ghosts:
            ghost.update()

        if not self.player.is_powered_up:
            for ghost in self.ghosts:
                ghost.eatable = False

        any_eatable = any(g.eatable for g in self.ghosts)
        in_frighten = (
            self.player.is_powered_up
            and not self.player.is_dying
            and any_eatable
        )
        if in_frighten:
            get_sounds().music_play_loop("frighten", volume=0.6)
        elif not self.player.is_dying:
            get_sounds().music_play_chain(
                "siren0_firstloop", "siren0", volume=0.7,
            )
        else:
            get_sounds().music_stop()

        # Player movement
        boost = POWER_BOOST if self.player.is_powered_up else 1.0
        self.player.speed_multiplier = BASE_SPEED * boost
        self.player.move_accumulator += self.player.speed_multiplier
        while self.player.move_accumulator >= 1.0:
            self._move_player()
            self.player.move_accumulator -= 1.0

        # Ghost movement
        if not self.ghosts_frozen:
            remaining_ratio = (
                sum(1 for g in self.pacgums if g.active) / self.start_pacgums
                if self.start_pacgums else 1.0
            )
            for ghost in self.active_ghosts:
                ghost.speed_multiplier = self._ghost_speed(
                    ghost, remaining_ratio)
                self._advance_ghost(ghost)

        for item in self.all_items:
            item.update(dt_ms)

        self._check_collisions()

    def request_player_direction(self, dx: int, dy: int) -> None:
        """
        Register the player's requested direction.

        A perpendicular turn is buffered and taken at the next tile where
        the way opens up (see :meth:`_move_player`). A reversal of the
        current heading, however, is applied *immediately* so Pac-Man turns
        back from the tile he visually occupies right now instead of
        overshooting to the tile ahead first. The move accumulator is
        inverted on reversal so the on-screen sprite never jumps.
        """
        p = self.player
        p.next_direction = (dx, dy)

        cur_dx, cur_dy = p.direction
        is_reversal = (
            (cur_dx, cur_dy) != (0, 0)
            and (dx, dy) == (-cur_dx, -cur_dy)
        )
        if not is_reversal:
            return

        ahead_x, ahead_y = p.x + cur_dx, p.y + cur_dy
        if (
            0 <= ahead_y < self.rows
            and 0 <= ahead_x < self.cols
            and self.grid[ahead_y][ahead_x] != WALL
        ):
            # We were partway into the tile ahead: commit to it and invert
            # the progress so the sprite keeps its exact screen position.
            p.set_position(ahead_x, ahead_y)
            p.move_accumulator = max(0.0, 1.0 - p.move_accumulator)
        p.direction = (dx, dy)
        p.next_direction = (0, 0)

    def _move_player(self) -> None:
        """
        Movement for PacMan against the grid.
        First we physically advance to the tile we were moving towards.
        Then we check if we can corner (change direction) for the next
        movement phase.
        """
        # 1. Advance in the current direction if the cell ahead is free
        dx, dy = self.player.direction
        if dx != 0 or dy != 0:
            next_x = self.player.x + dx
            next_y = self.player.y + dy
            if self.grid[next_y][next_x] != WALL:
                self.player.set_position(next_x, next_y)
        else:
            # If the player was idle, let them start instantly
            pass

        # 2. Cornering: adopt next_direction if the way is clear from the
        # tile we now stand on, then consume the buffered input so a stale
        # turn cannot fire again at a later intersection.
        nx_dx, nx_dy = self.player.next_direction
        if nx_dx != 0 or nx_dy != 0:
            test_x = self.player.x + nx_dx
            test_y = self.player.y + nx_dy
            if self.grid[test_y][test_x] != WALL:
                self.player.direction = self.player.next_direction
                self.player.next_direction = (0, 0)

    def _check_collisions(self) -> None:
        """
        Check and resolve all entity collisions for this tick.
        """
        px, py = self.player.x, self.player.y

        # Eat pac-gum
        for gum in self.pacgums:
            if gum.active and gum.x == px and gum.y == py:
                gum.active = False
                self.player.eat(gum.points)
                get_sounds().play(
                    f"eat_dot_{self._dot_toggle}", volume=0.5,
                )
                self._dot_toggle ^= 1

        # Eat super pac-gum
        for sgum in self.super_pacgums:
            if sgum.active and sgum.x == px and sgum.y == py:
                sgum.active = False
                self.player.eat(sgum.points)
                get_sounds().play(
                    f"eat_dot_{self._dot_toggle}", volume=0.8,
                )
                self._dot_toggle ^= 1
                config_secondes = self.config.get("super_time", 8)
                duration_ms = int(config_secondes * 1000)
                self.player.trigger_power_up(duration_ms)
                for ghost in self.active_ghosts:
                    ghost.eatable = True
                    dist = abs(ghost.x - px) + abs(ghost.y - py)
                    if dist <= 5:
                        ghost.turn_back()

        # encounter ghost
        if self.player.is_dying:
            return
        for ghost in self.active_ghosts:
            if ghost.is_dead:
                continue
            # Check if the player and ghost are on the same tile
            # or if they crossed (swapped positions) between two ticks.
            if (ghost.x == px and ghost.y == py) or (
                ghost.prev_pos == self.player.pos and
                ghost.pos == self.player.prev_pos
            ):
                if ghost.eatable:
                    base = int(self.config.get("points_per_ghost", 200))
                    self.player.eat_ghost(base)
                    ghost.is_eaten()
                    get_sounds().play("eat_ghost", volume=0.8)
                elif self.collision:
                    self.player.die()
                    get_sounds().play("death", volume=0.9)

    def is_cleared(self) -> bool:
        """
        True when every pac-gum has been eaten.
        """
        return not self.all_items

    def reset(self) -> None:
        """
        Reset all entities to their initial state.
        """
        self.player.pos = (int(self.player.px), int(self.player.py))

        for ghost in self.ghosts:
            ghost.reset()

        for gum in self.pacgums + self.super_pacgums:
            gum.active = True
