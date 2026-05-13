import random

from entities.player import PacMan
from entities.ghost import Ghost
from entities.ghost_types import Blinky, Inky, Pinky, Clyde
from entities.items import Pacgum, SuperPacgum


EMPTY = 0
WALL = 1
PACGUM = 2
SUPER_PACGUM = 3


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
        config: dict | None = None,
    ) -> None:
        self.grid: list[list[int]] = grid
        self.rows: int = len(grid)
        self.cols: int = len(grid[0]) if self.rows else 0

        self.player: PacMan = player
        self.ghosts: list[Ghost] = ghosts if ghosts is not None else []
        self.config: dict = config if config is not None else {}

        self.pacgums: list[Pacgum] = []
        self.super_pacgums: list[SuperPacgum] = []
        self._parse_items()
        self.start_pacgums: int = len(self.pacgums)

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def from_maze(
        cls,
        raw_maze: list[list[int]],
        maze_width: int,
        maze_height: int,
        config: dict | None = None,
    ) -> "Monitor":
        """
        Build a Monitor directly from a MazeGenerator raw maze.
        """
        if config is None:
            config = {}

        w_ext = 2 * maze_width + 1
        h_ext = 2 * maze_height + 1

        # 1. Build boolean wall grid (True = wall) — same logic as AsciiViewer
        bool_grid = [[True for _ in range(w_ext)] for _ in range(h_ext)]
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

        # 2. Assign Spawn Positions
        all_walkable = [
            (x, y) for y in range(h_ext)
            for x in range(w_ext)
            if not bool_grid[y][x]
        ]

        # Player spawn: closest to center
        cx, cy = w_ext // 2, h_ext // 2
        player_pos = min(
            all_walkable,
            key=lambda c: abs(c[0] - cx) + abs(c[1] - cy)
        )

        # Ghosts spawn: 4 corners
        c1 = min(
            all_walkable,
            key=lambda c: abs(c[0] - 1) + abs(c[1] - 1)
        )
        c2 = min(
            all_walkable,
            key=lambda c: abs(c[0] - (w_ext - 2)) + abs(c[1] - 1)
        )
        c3 = min(
            all_walkable,
            key=lambda c: abs(c[0] - 1) + abs(c[1] - (h_ext - 2))
        )
        c4 = min(
            all_walkable,
            key=lambda c: (
                abs(c[0] - (w_ext - 2))
                + abs(c[1] - (h_ext - 2))
            )
        )
        ghost_points = [c1, c2, c3, c4]

        # Keep the rest for pac-gums (YES on ghost spawns)
        reserved_spawns = {player_pos}
        empty_cells = [
            c for c in all_walkable if c not in reserved_spawns
        ]

        # 3. Pick random super-pac-gum positions
        nb_super = min(
            config.get("super_pacgums", 4), len(empty_cells)
        )
        super_positions = set(
            map(tuple, random.sample(empty_cells, nb_super))
        )

        # 4. Convert to int grid with pac-gum markers
        int_grid = [
            [WALL if bool_grid[y][x] else EMPTY for x in range(w_ext)]
            for y in range(h_ext)
        ]
        for (x, y) in empty_cells:
            if (x, y) in super_positions:
                int_grid[y][x] = SUPER_PACGUM
            else:
                int_grid[y][x] = PACGUM

        # 5. Initialization
        ghosts = [
            Blinky(ghost_points[0], sprite="&"),
            Pinky(ghost_points[1], sprite="&"),
            Inky(ghost_points[2], sprite="&"),
            Clyde(ghost_points[3], sprite="&")
        ]

        super_duration = int(config.get("super_time", 8)) * 30
        player = PacMan(player_pos[0],
                        player_pos[1],
                        power_duration=super_duration)
        monitor = cls(int_grid, player, ghosts=ghosts, config=config)

        for gum in monitor.pacgums:
            gum.points = config.get("p_pacgums", 10)
        for sgum in monitor.super_pacgums:
            sgum.points = config.get("p_Spacgums", 50)

        return monitor

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
    def all_items(self) -> list:
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

    def update(self) -> None:
        """
        Tick every entity managed by the monitor.
        """
        # --- SPEED SETTINGS ---
        # 0.12 means it takes about 8 frames to cross a tile.
        # The smaller this value, the slower the game.
        base_speed = 0.15

        self.player.prev_pos = self.player.pos
        for ghost in self.active_ghosts:
            ghost.prev_pos = ghost.pos

        # Update timers and angle
        self.player.update()
        for ghost in self.ghosts:
            ghost.update()

        if not self.player.is_powered_up:
            for ghost in self.ghosts:
                ghost.eatable = False

        # --- PLAYER SPEED ---
        # Apply base_speed (with a slight boost in Super mode)
        boost = 1.2 if self.player.is_powered_up else 1.0
        self.player.speed_multiplier = base_speed * boost

        self.player.move_accumulator += self.player.speed_multiplier
        while self.player.move_accumulator >= 1.0:
            self._move_player()
            self.player.move_accumulator -= 1.0

        remaining_ratio = (
            len([g for g in self.pacgums if g.active]) / self.start_pacgums
            if self.start_pacgums else 1.0
        )

        # --- GHOSTS SPEED ---
        for ghost in self.active_ghosts:
            if ghost.is_dead:
                # Returns very fast to spawn
                ghost.speed_multiplier = base_speed * 2.0
            elif ghost.eatable:
                # Frighten ghosts are slowed
                ghost.speed_multiplier = base_speed * 0.75
            else:
                # Default speed
                ghost.speed_multiplier = base_speed

                # Elroy mode for Blinky
                from entities.ghost_types import Blinky as _Blinky
                if isinstance(ghost, _Blinky):
                    if remaining_ratio <= 0.10:   # 90% eaten
                        ghost.speed_multiplier = base_speed * 1.20
                    elif remaining_ratio <= 0.25:  # 75% eaten
                        ghost.speed_multiplier = base_speed * 1.10

            ghost.move_accumulator += ghost.speed_multiplier
            while ghost.move_accumulator >= 1.0:
                try:
                    ghost.move(self.grid, self)
                except Exception:
                    raise Exception
                ghost.move_accumulator -= 1.0

        for item in self.all_items:
            item.update()

        self._check_collisions()

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

        # 2. Cornering: adopt next_direction if the way is clear
        # from this new tile
        nx_dx, nx_dy = self.player.next_direction
        if nx_dx != 0 or nx_dy != 0:
            test_x = self.player.x + nx_dx
            test_y = self.player.y + nx_dy
            if self.grid[test_y][test_x] != WALL:
                self.player.direction = self.player.next_direction

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

        # Eat super pac-gum
        for sgum in self.super_pacgums:
            if sgum.active and sgum.x == px and sgum.y == py:
                sgum.active = False
                self.player.eat(sgum.points)
                fps_jeu = 30
                config_secondes = self.config.get("super_time", 8)
                duration = int(config_secondes * fps_jeu)
                self.player.trigger_power_up(duration)
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
                    self.player.eat_ghost()
                    ghost.is_eaten()
                else:
                    self.player.die()

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
