from __future__ import annotations

from mazegenerator.mazegenerator import MazeGenerator
import pygame
import os
import sys
from typing import List, Tuple
import time

from core.monitor import Monitor, WALL
from core.scores import ScoreManager
from entities.ghost_types import Blinky, Pinky, Inky, Clyde
from entities.items import SuperPacgum

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "mazegenerator-00001-py3-none-any"))


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


class PygameViewer:
    def __init__(self, config: dict):
        pygame.init()

        # --- 1. SCREEN BOUNDS DETECTION ---
        info = pygame.display.Info()
        # Get the current monitor resolution (e.g. 1920x1080)
        screen_max_w = info.current_w
        screen_max_h = info.current_h
        self.reset = False

        # Define a safety margin to avoid touching the screen edges
        # (e.g. taskbar)
        self.margin = 60

        if config:
            self.maze_width = int(config.get("width", 15))
            self.maze_height = int(config.get("height", 15))
            self._seed = int(config.get("seed", 0))
            self.config = {
                "super_pacgums": 4,
                "p_pacgums": int(config.get("points_per_pacgum", 10)),
                "p_Spacgums": int(
                    config.get("points_per_super_pacgum", 50)
                ),
                "super_time": int(config.get("super_time", 30)),
                "level_max_time": int(
                    config.get("level_max_time", 90)
                ),
                "cheat_mode": config.get("cheat_mode", False),
                "level": int(config.get("level", 1)),
            }
            practice_raw = str(
                config.get("practice", "False")
            ).lower()
            self.practice: bool = practice_raw == "true"
            self.score_manager: ScoreManager = ScoreManager(
                str(config.get("highscore_filename", "highscores.json"))
            )
        else:
            self.maze_width = 15
            self.maze_height = 15
            self._seed = 0
            self.config = {
                "super_pacgums": 4,
                "p_pacgums": 10,
                "p_Spacgums": 50,
                "super_time": 30,
                "level_max_time": 90,
            }
            self.practice = False
            self.score_manager = ScoreManager("highscores.json")

        self.monitor = self._build_monitor()
        self.rows = len(self.monitor.grid)
        self.cols = len(self.monitor.grid[0])

        # --- 2. AUTO-COMPUTE TILE SIZE ---
        # We want the maze to occupy at most 85% of the screen height
        available_w = screen_max_w * 0.85
        available_h = screen_max_h * 0.85
        # Compute the maximum tile size that fits in HEIGHT
        tile_h = int((available_h - (2 * self.margin)) // self.rows)
        # Compute the maximum tile size that fits in WIDTH
        tile_w = int((available_w - (2 * self.margin)) // self.cols)

        # TAKE THE MINIMUM OF THE TWO
        # Crucial step: by taking the minimum, we ensure the maze fits
        # both the width AND the height of the screen.
        self.TILE_SIZE = max(12, min(tile_h, tile_w, 48))

        # --- 3. WINDOW DIMENSIONS ---
        self.screen_width = (self.cols * self.TILE_SIZE) + (2 * self.margin)
        self.screen_height = (self.rows * self.TILE_SIZE) + (2 * self.margin)

        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height), pygame.RESIZABLE
        )
        pygame.display.set_caption("Pac-Man - Pygame Viewer")

        # --- 4. DYNAMIC CENTERING ---
        # Use get_size() in case the OS forced a slightly different size
        actual_w, actual_h = self.screen.get_size()
        self.offset_x = (actual_w - (self.cols * self.TILE_SIZE)) // 2
        self.offset_y = (actual_h - (self.rows * self.TILE_SIZE)) // 2

        self._preload_raw_images()
        self.scale_sprites()

    def _build_monitor(self) -> Monitor:
        cache_key = (self.maze_width, self.maze_height, self._seed)
        if self._seed > 0 and cache_key in _maze_cache:
            raw_maze = _maze_cache[cache_key]
        else:
            generator = _FastMazeGenerator(
                size=(self.maze_width, self.maze_height),
                perfect=False,
                seed=self._seed,
            )
            raw_maze = generator.maze
            if self._seed > 0:
                # Store a copy so the cache is unaffected by later mutation
                _maze_cache[cache_key] = [row[:] for row in raw_maze]
        return Monitor.from_maze(
            raw_maze, self.maze_width, self.maze_height, self.config
        )

    def _load_raw(self, rel_path: str) -> pygame.Surface | None:
        path = os.path.join(_ROOT, "assets", rel_path)
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            return img
        return None

    def _preload_raw_images(self) -> None:
        self.raw_images: dict[
            str, pygame.Surface | list[pygame.Surface | None] | None
        ] = {
            "floor": self._load_raw("Maze/MazePart/Tile/BlackTile.png"),
            # Borders
            "Border_TopHorizontal": self._load_raw(
                "Maze/MazePart/Wall/Border/TopHorizontal.png"
            ),
            "Border_BottomHorizontal": self._load_raw(
                "Maze/MazePart/Wall/Border/BottomHorizontal.png"
            ),
            "Border_LeftVertical": self._load_raw(
                "Maze/MazePart/Wall/Border/LeftVertical.png"
            ),
            "Border_RightVertical": self._load_raw(
                "Maze/MazePart/Wall/Border/RightVertical.png"
            ),
            "Border_TopToRight": self._load_raw(
                "Maze/MazePart/Wall/Border/TopToRight.png"
            ),
            "Border_BottomToRight": self._load_raw(
                "Maze/MazePart/Wall/Border/BottomToRight.png"
            ),
            "Border_LeftToTop": self._load_raw(
                "Maze/MazePart/Wall/Border/LeftToTop.png"
            ),
            "Border_LeftToBottom": self._load_raw(
                "Maze/MazePart/Wall/Border/LeftToBottom.png"
            ),
            # Straight inner walls
            "Inside_HorizontalTop": self._load_raw(
                "Maze/MazePart/Wall/Inside/HorizontalTop.png"
            ),
            "Inside_VerticalLeft": self._load_raw(
                "Maze/MazePart/Wall/Inside/VerticalLeft.png"
            ),
            # Pac-gums
            "Pacgum": self._load_raw("Maze/Pacgum.png"),
            "Super_Pacgum": self._load_raw("Maze/Super-Pacgum_2.png"),
        }

        # Ghosts
        for entity in ["Blinky", "Pinky", "Inky", "Clyde"]:
            for d in ["Up", "Down", "Left", "Right"]:
                self.raw_images[f"{entity}_{d}"] = [
                    self._load_raw(
                        f"Sprites/sprites/ghosts/{entity}/{d}/{d}_0.png"
                    ),
                    self._load_raw(
                        f"Sprites/sprites/ghosts/{entity}/{d}/{d}_1.png"
                    ),
                ]

        # Frighten
        self.raw_images["Frighten"] = [
            self._load_raw("Sprites/sprites/ghosts/Frighten/Frighten_0.png"),
            self._load_raw("Sprites/sprites/ghosts/Frighten/Frighten_1.png"),
        ]

        self.raw_images["Dead_Down"] = [
            self._load_raw("Sprites/sprites/ghosts/Dead/DeadBottom.png")
        ]
        self.raw_images["Dead_Up"] = [
            self._load_raw("Sprites/sprites/ghosts/Dead/DeadTop.png")
        ]
        self.raw_images["Dead_Left"] = [
            self._load_raw("Sprites/sprites/ghosts/Dead/DeadLeft.png")
        ]
        self.raw_images["Dead_Right"] = [
            self._load_raw("Sprites/sprites/ghosts/Dead/DeadRight.png")
        ]

        self.raw_images["Frighten_End"] = [
            self._load_raw(
                "Sprites/sprites/ghosts/Frighten/EndFrighten_0.png"
            ),
            self._load_raw(
                "Sprites/sprites/ghosts/Frighten/EndFrighten_1.png"
            ),
            self._load_raw("Sprites/sprites/ghosts/Frighten/Frighten_0.png"),
            self._load_raw("Sprites/sprites/ghosts/Frighten/Frighten_1.png"),
        ]

        # Pacman
        for d in ["Up", "Down", "Left", "Right"]:
            self.raw_images[f"Pacman_{d}"] = [
                self._load_raw(
                    f"Sprites/sprites/Pacman/animations/{d}/{d}_{i}.png"
                )
                for i in range(4)
            ]

        self.raw_images["Pacman_Death"] = [
            self._load_raw(
                f"Sprites/sprites/Pacman/animations/Death/Death_{i}.png"
            )
            for i in range(13)
        ]

    def scale_sprites(self) -> None:
        self.sprites: dict[str,
                           pygame.Surface | list[pygame.Surface | None] | None
                           ] = {}
        for key, item in self.raw_images.items():
            if isinstance(item, list):
                scaled_list: list[pygame.Surface | None] = []
                for img in item:
                    if img:
                        scaled = pygame.transform.scale(
                            img, (self.TILE_SIZE, self.TILE_SIZE)
                        )
                        scaled_list.append(scaled)
                    else:
                        scaled_list.append(None)
                self.sprites[key] = scaled_list
            else:
                img = item
                if img:
                    # Set a specific size for items
                    if key == "Pacgum":
                        size = int(self.TILE_SIZE * 0.3)  # Small dot
                    elif key == "Super_Pacgum":
                        size = int(self.TILE_SIZE * 0.6)  # Large dot
                    else:
                        size = self.TILE_SIZE

                    scaled = pygame.transform.scale(img, (size, size))
                    if key.startswith("Inside_"):
                        scaled.set_colorkey((0, 0, 0))
                    self.sprites[key] = scaled
                else:
                    self.sprites[key] = None

    def get_wall_mask(self, grid: list[list[int]], x: int, y: int) -> int:
        mask = 0
        if y > 0 and grid[y - 1][x] == WALL:
            mask += 1  # Top = 1
        if x < self.cols - 1 and grid[y][x + 1] == WALL:
            mask += 2  # Right = 2
        if y < self.rows - 1 and grid[y + 1][x] == WALL:
            mask += 4  # Bottom = 4
        if x > 0 and grid[y][x - 1] == WALL:
            mask += 8  # Left = 8
        return mask

    def get_sprites_for_wall(
        self, mask: int, x: int, y: int
    ) -> list[pygame.Surface]:
        sprites_to_draw: list[pygame.Surface] = []
        is_border = False
        is_corner = False

        # --- 1. BORDER AND CORNER IDENTIFICATION ---
        border_sprite = None

        # Corner detection (no inside wall sprites here)
        if y == 0 and x == 0:
            border_sprite = self.sprites.get("Border_BottomToRight")
            is_corner = True
        elif y == 0 and x == self.cols - 1:
            border_sprite = self.sprites.get("Border_LeftToBottom")
            is_corner = True
        elif y == self.rows - 1 and x == 0:
            border_sprite = self.sprites.get("Border_TopToRight")
            is_corner = True
        elif y == self.rows - 1 and x == self.cols - 1:
            border_sprite = self.sprites.get("Border_LeftToTop")
            is_corner = True

        # Straight border detection (if not a corner)
        elif y == 0:
            border_sprite = self.sprites.get("Border_TopHorizontal")
        elif y == self.rows - 1:
            border_sprite = self.sprites.get("Border_BottomHorizontal")
        elif x == 0:
            border_sprite = self.sprites.get("Border_LeftVertical")
        elif x == self.cols - 1:
            border_sprite = self.sprites.get("Border_RightVertical")

        if border_sprite and isinstance(border_sprite, pygame.Surface):
            sprites_to_draw.append(border_sprite)
            is_border = True

        # If it's a corner, stop here: don't draw any blue lines
        if is_corner:
            return sprites_to_draw

        # --- 2. DRAWING JUNCTIONS WITH OFFSET ---
        temp_surface = pygame.Surface(
            (self.TILE_SIZE, self.TILE_SIZE), pygame.SRCALPHA
        )
        mid = self.TILE_SIZE // 2
        color = (33, 33, 255)  # Pac-Man blue

        # OFFSET: double border thickness.
        # Adjust this value (4, 5 or 6) so the line stops exactly on
        # the sprite edge.
        offset = 5

        if not is_border:
            # Normal cell inside the maze
            if mask == 0:
                # Isolated wall (surrounded by empty cells)
                pygame.draw.rect(
                    temp_surface, color, (mid - 2, mid - 2, 4, 4), 2
                )
            if mask & 1:
                pygame.draw.line(temp_surface, color, (mid, mid), (mid, 0), 2)
            if mask & 2:
                pygame.draw.line(
                    temp_surface, color, (mid, mid), (self.TILE_SIZE, mid), 2
                )
            if mask & 4:
                pygame.draw.line(
                    temp_surface, color, (mid, mid), (mid, self.TILE_SIZE), 2
                )
            if mask & 8:
                pygame.draw.line(temp_surface, color, (mid, mid), (0, mid), 2)
        else:
            # BORDER cell: connect the interior toward the inner edge
            # of the sprite

            # TOP border: draw a line coming from the bottom up to offset
            if y == 0 and (mask & 4):
                pygame.draw.line(
                    temp_surface,
                    color,
                    (mid, self.TILE_SIZE),
                    (mid, offset),
                    2,
                )

            # BOTTOM border: draw a line coming from the top down to
            # (size - offset)
            if y == self.rows - 1 and (mask & 1):
                pygame.draw.line(
                    temp_surface,
                    color,
                    (mid, 0),
                    (mid, self.TILE_SIZE - offset),
                    2,
                )

            # LEFT border: draw a line coming from the right up to offset
            if x == 0 and (mask & 2):
                pygame.draw.line(
                    temp_surface,
                    color,
                    (self.TILE_SIZE, mid),
                    (offset, mid),
                    2,
                )

            # RIGHT border: draw a line coming from the left up to
            # (size - offset)
            if x == self.cols - 1 and (mask & 8):
                pygame.draw.line(
                    temp_surface,
                    color,
                    (0, mid),
                    (self.TILE_SIZE - offset, mid),
                    2,
                )

        sprites_to_draw.append(temp_surface)
        return sprites_to_draw

    def draw_maze(self) -> None:
        actual_w, actual_h = self.screen.get_size()
        self.offset_x = (actual_w - (self.cols * self.TILE_SIZE)) // 2
        self.offset_y = (actual_h - (self.rows * self.TILE_SIZE)) // 2
        grid = self.monitor.grid
        for y in range(self.rows):
            for x in range(self.cols):
                rect = pygame.Rect(
                    self.offset_x + x * self.TILE_SIZE,
                    self.offset_y + y * self.TILE_SIZE,
                    self.TILE_SIZE,
                    self.TILE_SIZE,
                )

                if grid[y][x] == WALL:
                    mask = self.get_wall_mask(grid, x, y)
                    sprites = self.get_sprites_for_wall(mask, x, y)

                    # Always paint a pure black background under the wall
                    # before drawing its transparent lines
                    pygame.draw.rect(self.screen, (0, 0, 0), rect)

                    if sprites:
                        for sprite in sprites:
                            self.screen.blit(sprite, rect.topleft)
                    else:
                        pygame.draw.rect(self.screen, (0, 0, 200), rect)
                        # Fallback blue
                else:
                    floor = self.sprites.get("floor")
                    if floor and isinstance(floor, pygame.Surface):
                        self.screen.blit(floor, rect.topleft)
                    else:
                        pygame.draw.rect(self.screen, (0, 0, 0), rect)
                        # Fallback floor

    def _update_dimensions(self, new_tile_size: int) -> None:
        """
        Update the tile size and resize the window accordingly.
        """
        # Safety guard to avoid tiny tiles
        self.TILE_SIZE = max(4, new_tile_size)

        # Recompute screen size
        self.screen_width = (self.cols * self.TILE_SIZE) + (2 * self.margin)
        self.screen_height = (self.rows * self.TILE_SIZE) + (2 * self.margin)

        # Apply the new video mode
        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height), pygame.RESIZABLE
        )

        # Re-centre and rescale sprites
        self.offset_x = (self.screen_width - (self.cols * self.TILE_SIZE)) // 2
        self.offset_y = (
            self.screen_height - (self.rows * self.TILE_SIZE)
        ) // 2
        self.scale_sprites()

    def draw_items(self) -> None:
        """
        Draw the active pac-gums and super pac-gums.
        """
        # Group all gums together
        all_gums = self.monitor.pacgums + self.monitor.super_pacgums

        for gum in all_gums:
            if gum.active:
                sprite_key = (
                    "Super_Pacgum"
                    if isinstance(gum, SuperPacgum)
                    else "Pacgum"
                )
                sprite = self.sprites.get(sprite_key)

                if sprite and isinstance(sprite, pygame.Surface):
                    # Compute position to centre the sprite in the cell
                    pos_x = (
                        self.offset_x
                        + (gum.x * self.TILE_SIZE)
                        + (self.TILE_SIZE - sprite.get_width()) // 2
                    )
                    pos_y = (
                        self.offset_y
                        + (gum.y * self.TILE_SIZE)
                        + (self.TILE_SIZE - sprite.get_height()) // 2
                    )
                    self.screen.blit(sprite, (pos_x, pos_y))

    def draw_player(self) -> None:
        """
        Draw Pac-Man with interpolation for smooth movement.
        """
        player = self.monitor.player
        if not player.active:
            return

        render_x, render_y = float(player.x), float(player.y)

        # Normal movement
        if not player.is_dying:
            dx, dy = player.direction
            grid = self.monitor.grid
            if (0 <= player.y + dy < self.rows and
                    0 <= player.x + dx < self.cols and
                    grid[player.y + dy][player.x + dx] != 1):
                render_x += dx * player.move_accumulator
                render_y += dy * player.move_accumulator

            # Animation selection
            dir_map = {0: "Right", 90: "Up", 180: "Left", 270: "Down"}
            anim_dir = dir_map.get(player.angle, "Right")

            frames = self.sprites.get(f"Pacman_{anim_dir}")
            if frames and isinstance(frames, list):
                # 4 frames per animation, ~100 ms per frame
                frame_index = (pygame.time.get_ticks() // 100) % 4
                base_sprite = frames[frame_index]
            else:
                base_sprite = None
        else:
            # Death sequence
            if player.death_start_time == 0:
                player.death_start_time = pygame.time.get_ticks()

            elapsed = pygame.time.get_ticks() - player.death_start_time
            frames = self.sprites.get("Pacman_Death")
            if frames and isinstance(frames, list):
                frame_index = elapsed // 100
                if frame_index >= len(frames):
                    # Hold on the last frame
                    frame_index = len(frames) - 1
                base_sprite = frames[frame_index]
            else:
                base_sprite = None

        if base_sprite:
            # Convert to pixel coordinates
            pos_x = self.offset_x + render_x * self.TILE_SIZE
            pos_y = self.offset_y + render_y * self.TILE_SIZE

            rect = base_sprite.get_rect(
                center=(
                    pos_x + self.TILE_SIZE // 2,
                    pos_y + self.TILE_SIZE // 2,
                )
            )
            self.screen.blit(base_sprite, rect.topleft)

    def draw_ghost_paths(self) -> None:
        """
        Draw each ghost's current path (practice mode only).
        """
        if not self.practice:
            return

        color_map = {
            "Blinky": (255, 0, 0),
            "Pinky": (255, 184, 255),
            "Inky": (0, 255, 255),
            "Clyde": (255, 184, 82),
            "Eatable": (0, 0, 255),
        }
        ts = self.TILE_SIZE
        half = ts // 2

        for ghost in self.monitor.ghosts:
            if not ghost.active or not ghost.current_path:
                continue

            c_name = ghost.__class__.__name__
            key = "Eatable" if ghost.eatable else c_name
            color = color_map.get(key, (200, 200, 200))
            path = ghost.current_path

            dir_vec = {
                "N": (0, -1), "S": (0, 1),
                "E": (1, 0), "W": (-1, 0),
            }
            dx, dy = dir_vec.get(ghost.direction, (0, 0))
            rx = float(ghost.x)
            ry = float(ghost.y)
            grid = self.monitor.grid
            if (0 <= ghost.y + dy < self.rows and
                    0 <= ghost.x + dx < self.cols and
                    grid[ghost.y + dy][ghost.x + dx] != 1):
                rx += dx * ghost.move_accumulator
                ry += dy * ghost.move_accumulator

            points = [
                (
                    self.offset_x + rx * ts + half,
                    self.offset_y + ry * ts + half,
                )
            ]
            for px, py in path:
                points.append((
                    self.offset_x + px * ts + half,
                    self.offset_y + py * ts + half,
                ))

            if len(points) >= 2:
                pygame.draw.lines(
                    self.screen, color, False, points, 3
                )
                last_px, last_py = path[-1]
                end_x = self.offset_x + last_px * ts + half
                end_y = self.offset_y + last_py * ts + half
                pygame.draw.circle(
                    self.screen, color, (end_x, end_y), 6
                )

    def draw_ghosts(self) -> None:
        """
        Draw all ghosts with smooth interpolation and blink effect.
        """
        dir_map_vectors = {
            "N": (0, -1),
            "S": (0, 1),
            "E": (1, 0),
            "W": (-1, 0),
        }
        dir_map_str = {"N": "Up", "S": "Down", "E": "Right", "W": "Left"}
        player = self.monitor.player

        for ghost in self.monitor.ghosts:
            if not ghost.active:
                continue

            # --- POSITION COMPUTATION (Interpolation) ---
            dx, dy = dir_map_vectors.get(ghost.direction, (0, 0))
            render_x, render_y = float(ghost.x), float(ghost.y)
            render_x += dx * ghost.move_accumulator
            render_y += dy * ghost.move_accumulator

            # --- FRAME SELECTION ---
            ghost_dir = dir_map_str.get(ghost.direction, "Down")

            if ghost.is_dead:
                frames = self.sprites.get(f"Dead_{ghost_dir}")

            elif ghost.eatable:
                # Blink threshold: 3 seconds * 30 FPS = 90
                if player.power_timer < 90:
                    # Alternate between blue and white every 5 frames
                    # (player.power_timer // 5) % 2 gives 0 or 1
                    if (player.power_timer // 5) % 2 == 0:
                        frames = self.sprites.get("Frighten_End")
                    else:
                        frames = self.sprites.get("Frighten")
                else:
                    frames = self.sprites.get("Frighten")

            elif isinstance(ghost, Blinky):
                frames = self.sprites.get(f"Blinky_{ghost_dir}")
            elif isinstance(ghost, Pinky):
                frames = self.sprites.get(f"Pinky_{ghost_dir}")
            elif isinstance(ghost, Inky):
                frames = self.sprites.get(f"Inky_{ghost_dir}")
            elif isinstance(ghost, Clyde):
                frames = self.sprites.get(f"Clyde_{ghost_dir}")
            else:
                frames = None

            # --- Drawing with double validation ---
            if frames and isinstance(frames,
                                     list):  # Ensure it is a list of frames
                frame_index = (pygame.time.get_ticks() // 150) % len(frames)
                sprite = frames[frame_index]

                if sprite:  # CRITICAL: only blit if the sprite is valid
                    pos_x = self.offset_x + render_x * self.TILE_SIZE
                    pos_y = self.offset_y + render_y * self.TILE_SIZE
                    self.screen.blit(sprite, (pos_x, pos_y))
                else:
                    # Optional: draw a coloured square for missing images
                    pass

    def display(self) -> None:
        """
        Show the main menu and run the game flow.
        """
        while True:
            action = self._run_menu()
            if action == "quit":
                break
            elif action == "highscores":
                self._run_highscores()
            elif action == "instructions":
                self._run_instructions()
            elif action == "play":
                # Build fresh maze before each game
                self._seed = int(self.config.get("seed", 0))
                self.monitor = self._build_monitor()
                current_level = 1

                while True:
                    result = self._run_game(current_level)
                    if result == "quit":
                        break
                    elif result == "win" and current_level == self.monitor.level:
                        self._run_end_screen("win", self.monitor.player.score)
                        break
                    elif result == "win":
                        score = self.monitor.player.score
                        lives = self.monitor.player.lives
                        current_level += 1

                        self._seed = 0
                        self.monitor = self._build_monitor()

                        self.monitor.player.score = score
                        self.monitor.player.lives = lives
                        continue
                    elif result == "lose":
                        self._run_end_screen("lose", self.monitor.player.score)
                        break
        pygame.quit()

    def _run_menu(self) -> str:
        """
        Main menu. Returns 'play', 'highscores', 'instructions', 'quit'.
        """
        font_title = pygame.font.SysFont("Arial", 56, bold=True)
        font_item = pygame.font.SysFont("Arial", 34)
        items = [
            "Start Game", "View Highscores",
            "Instructions", "Exit",
        ]
        actions = ["play", "highscores", "instructions", "quit"]
        selected = 0
        clock = pygame.time.Clock()

        anim_x = -250

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        selected = (selected - 1) % len(items)
                    elif event.key == pygame.K_DOWN:
                        selected = (selected + 1) % len(items)
                    elif event.key in (
                        pygame.K_RETURN, pygame.K_SPACE
                    ):
                        return actions[selected]

            self.screen.fill((0, 0, 0))
            w, h = self.screen.get_size()

            # --- Animation at the bottom ---
            anim_x += 5
            if anim_x > w + 100:
                anim_x = -450

            anim_y = h - 60
            time_ticks = pygame.time.get_ticks()
            pac_frame = (time_ticks // 100) % 4
            ghost_frame = (time_ticks // 150) % 2

            pacman_sprite_list = self.sprites.get("Pacman_Right")
            if isinstance(pacman_sprite_list, list):
                pac_sprite = pacman_sprite_list[pac_frame]
                if pac_sprite:
                    self.screen.blit(
                        pac_sprite, (anim_x, anim_y)
                    )

            for i, name in enumerate(["Blinky", "Pinky", "Inky", "Clyde"]):
                ghost_sprite_list = self.sprites.get(f"{name}_Right")
                if isinstance(ghost_sprite_list, list):
                    ghost_sprite = ghost_sprite_list[ghost_frame]
                    if ghost_sprite:
                        ghost_x = anim_x + 100 + 60 * i
                        self.screen.blit(
                            ghost_sprite, (ghost_x, anim_y)
                        )
            # -------------------------------

            self._draw_centered(
                "PAC-MAN", font_title, (255, 255, 0), h // 5
            )
            for i, label in enumerate(items):
                color = (
                    (255, 255, 0) if i == selected else (200, 200, 200)
                )
                prefix = "> " if i == selected else "  "
                self._draw_centered(
                    f"{prefix}{label}",
                    font_item, color, h // 2 + i * 52,
                )
            pygame.display.flip()
            clock.tick(30)

    def _run_highscores(self) -> None:
        """
        Show top-10 leaderboard. ENTER or ESC to go back.
        """
        font_title = pygame.font.SysFont("Arial", 44, bold=True)
        font_row = pygame.font.SysFont("Courier New", 26)
        font_hint = pygame.font.SysFont("Arial", 22)
        clock = pygame.time.Clock()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key in (
                        pygame.K_ESCAPE, pygame.K_RETURN
                    ):
                        return

            self.screen.fill((0, 0, 0))
            _, h = self.screen.get_size()
            self._draw_centered(
                "HIGH SCORES", font_title, (255, 255, 0), 30
            )
            scores = self.score_manager.top_scores()
            if not scores:
                self._draw_centered(
                    "No scores yet!",
                    font_row, (180, 180, 180), h // 2,
                )
            else:
                for i, (name, score) in enumerate(scores):
                    line = f"{i + 1:2}.  {name:<10}  {score:>8}"
                    self._draw_centered(
                        line, font_row,
                        (255, 255, 255), 100 + i * 36,
                    )
            self._draw_centered(
                "ENTER or ESC  -  back",
                font_hint, (120, 120, 120), h - 50,
            )
            pygame.display.flip()
            clock.tick(30)

    def _run_instructions(self) -> None:
        """
        Show controls and rules. ENTER or ESC to go back.
        """
        font_title = pygame.font.SysFont("Arial", 44, bold=True)
        font_body = pygame.font.SysFont("Arial", 24)
        clock = pygame.time.Clock()
        # Each entry: (text, colour)
        lines: List[Tuple[str, Tuple[int, int, int]]] = [
            ("CONTROLS", (255, 255, 0)),
            ("Arrow keys / WASD  -  Move", (200, 200, 200)),
            ("ESC  -  Back to menu", (200, 200, 200)),
            ("", (0, 0, 0)),
            ("RULES", (255, 255, 0)),
            ("Eat all pac-gums to win.", (200, 200, 200)),
            ("Ghosts kill you on touch.", (200, 200, 200)),
            ("Super pac-gum makes ghosts edible.", (200, 200, 200)),
            ("3 lives total.", (200, 200, 200)),
            ("", (0, 0, 0)),
            ("ENTER or ESC  -  back", (120, 120, 120)),
        ]

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key in (
                        pygame.K_ESCAPE, pygame.K_RETURN
                    ):
                        return

            self.screen.fill((0, 0, 0))
            self._draw_centered(
                "INSTRUCTIONS", font_title, (255, 255, 0), 30
            )
            for i, (text, color) in enumerate(lines):
                self._draw_centered(
                    text, font_body, color, 110 + i * 38
                )
            pygame.display.flip()
            clock.tick(30)

    def _run_end_screen(
        self, result: str, final_score: int
    ) -> None:
        """
        Game-over or victory: show score, ask name, save it.
        """
        font_title = pygame.font.SysFont("Arial", 52, bold=True)
        font_score = pygame.font.SysFont("Arial", 32)
        font_label = pygame.font.SysFont("Arial", 26)
        font_input = pygame.font.SysFont("Courier New", 38, bold=True)
        clock = pygame.time.Clock()

        title = "YOU WIN!" if result == "win" else "GAME OVER"
        t_color = (
            (0, 255, 100) if result == "win" else (255, 50, 50)
        )
        name = ""

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.score_manager.add(
                            name or "Anonymous", final_score
                        )
                        return
                    elif event.key == pygame.K_ESCAPE:
                        return
                    elif event.key == pygame.K_BACKSPACE:
                        name = name[:-1]
                    else:
                        ch = event.unicode
                        if (
                            ch
                            and (ch.isalnum() or ch == " ")
                            and len(name) < 10
                        ):
                            name += ch

            self.screen.fill((0, 0, 0))
            _, h = self.screen.get_size()
            self._draw_centered(title, font_title, t_color, h // 5)
            self._draw_centered(
                f"Final Score: {final_score}",
                font_score, (255, 255, 255), h // 3,
            )
            self._draw_centered(
                "Enter your name:",
                font_label, (180, 180, 180), h // 2 - 30,
            )
            self._draw_centered(
                name + "_", font_input, (255, 255, 0), h // 2 + 20,
            )
            self._draw_centered(
                "ENTER to save  |  ESC to skip",
                font_label, (100, 100, 100), h - 60,
            )
            pygame.display.flip()
            clock.tick(30)

    def _draw_centered(
        self,
        text: str,
        font: pygame.font.Font,
        color: tuple,
        y: int,
    ) -> None:
        """
        Draw text horizontally centred at vertical position y.
        """
        surf = font.render(text, True, color)
        x = (self.screen.get_width() - surf.get_width()) // 2
        self.screen.blit(surf, (x, y))

    def _draw_hud(
        self, elapsed: int, fps: int, max_time: int, level: int = 1
    ) -> None:
        """
        Draw score, lives, level and remaining time at the top.
        """
        font = pygame.font.SysFont("Arial", 20, bold=True)
        player = self.monitor.player
        remaining = max(0, max_time - elapsed // fps)
        text = (
            f"SCORE: {player.score}    "
            f"LIVES: {player.lives}    "
            f"LEVEL: {level}    "
            f"TIME: {remaining}s"
        )
        self.screen.blit(
            font.render(text, True, (255, 255, 0)), (10, 5)
        )

        cheat_enabled = self.config.get("cheat_mode", False)
        if cheat_enabled:
            hud_font = pygame.font.SysFont("Arial", 16)
            bottom_y = self.screen.get_height() - 25

            if self.monitor.player.god_mode:
                god_status = "ON"
            else:
                god_status = "OFF"
            if self.monitor.player.god_mode:
                color = (0, 255, 0)
            else:
                color = (255, 255, 255)

            cheat_text = f"Cheats: [G] God Mode ({god_status})"
            self.screen.blit(
                hud_font.render(cheat_text, True, color), (10, bottom_y)
            )

    def _reset_level(self, spawn_x: int, spawn_y: int) -> None:
        """
        Reset state after losing a life.

        need to implement full reset.
        """
        self.reset = True
        p = self.monitor.player
        p.is_dying = False
        p.direction = (0, 0)
        p.next_direction = (0, 0)
        p.move_accumulator = 0.0
        p.death_start_time = 0
        p.is_powered_up = False
        p.power_timer = 0
        p.set_position(spawn_x, spawn_y)
        for ghost in self.monitor.ghosts:
            ghost.reset()

    def _run_game(self, level: int = 1) -> str:
        """
        Game loop. Returns 'win', 'lose', or 'quit'.
        """
        clock = pygame.time.Clock()
        fps = 30
        max_time: int = int(self.config.get("level_max_time", 90))
        elapsed = 0
        death_timer = 0
        spawn_x = self.monitor.player.x
        spawn_y = self.monitor.player.y

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "quit"
                    cheat_enabled = self.config.get(
                        "cheat_mode", False)
                    if cheat_enabled and event.key == pygame.K_g:
                        self.monitor.player.god_mode = (
                            not self.monitor.player.god_mode)

            if not self.monitor.player.is_dying:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_UP] or keys[pygame.K_w]:
                    self.monitor.player.set_direction(0, -1)
                if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                    self.monitor.player.set_direction(0, 1)
                if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                    self.monitor.player.set_direction(-1, 0)
                if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                    self.monitor.player.set_direction(1, 0)

            self.monitor.update()
            elapsed += 1

            if self.monitor.is_cleared():
                return "win"
            if elapsed >= max_time * fps:
                # Time is up: lose a life, then reset or game over
                self.monitor.player.die()
                if self.monitor.player.lives <= 0:
                    return "lose"
                elapsed = 0
                self._reset_level(spawn_x, spawn_y)
                continue

            if self.monitor.player.is_dying:
                death_timer += 1
                if death_timer >= 40:  # ~1.3 s at 30 FPS
                    death_timer = 0
                    if self.monitor.player.lives <= 0:
                        return "lose"
                    self._reset_level(spawn_x, spawn_y)

            self.screen.fill((0, 0, 0))
            self.draw_maze()
            self.draw_items()
            if self.practice:
                self.draw_ghost_paths()
            self.draw_ghosts()
            self.draw_player()
            self._draw_hud(elapsed, fps, max_time, level)
            pygame.display.flip()
            if elapsed == 1 or self.reset:
                time.sleep(2)
            self.reset = False
            clock.tick(fps)
