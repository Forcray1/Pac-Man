from __future__ import annotations

import time
from typing import Any

import pygame

from core.game import Game
from core.monitor import Monitor
from core.scores import ScoreManager
from display._maze_utils import _FastMazeGenerator, _maze_cache
from display.hud_mixin import HudMixin
from display.renderer_mixin import RendererMixin
from display.screens_mixin import ScreensMixin
from display.sprite_mixin import SpritesMixin


class PygameViewer(SpritesMixin, RendererMixin, HudMixin, ScreensMixin):
    def __init__(self, config: dict[str, Any]):
        pygame.init()

        # --- 1. SCREEN BOUNDS DETECTION ---
        info = pygame.display.Info()
        # Get the current monitor resolution (e.g. 1920x1080)
        self.screen_max_w = info.current_w
        self.screen_max_h = info.current_h
        screen_max_w = self.screen_max_w
        screen_max_h = self.screen_max_h
        self.reset = False

        # Define a safety margin to avoid touching the screen edges
        # (e.g. taskbar)
        self.margin = 60

        if config:
            self.maze_width = int(config.get("width", 15))
            self.maze_height = int(config.get("height", 15))
            self._seed = int(config.get("seed", 0))
            self._base_maze_width = self.maze_width
            self._base_maze_height = self.maze_height
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
                "difficulty": int(config.get("difficulty", 1)),
                "points_per_ghost": int(
                    config.get("points_per_ghost", 200)
                ),
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
        # Tile size is computed so the maze fits inside the full screen,
        # leaving a margin on each side.
        available_w = screen_max_w - (2 * self.margin)
        available_h = screen_max_h - (2 * self.margin)
        # Compute the maximum tile size that fits in HEIGHT
        tile_h = int(available_h // self.rows)
        # Compute the maximum tile size that fits in WIDTH
        tile_w = int(available_w // self.cols)

        # TAKE THE MINIMUM OF THE TWO
        # Crucial step: by taking the minimum, we ensure the maze fits
        # both the width AND the height of the screen.
        self.TILE_SIZE = max(12, min(tile_h, tile_w, 48))

        # --- 3. FULLSCREEN WINDOW ---
        # Pass (0, 0) so pygame uses the current desktop resolution.
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption("Pac-Man - Pygame Viewer")

        # Store the actual fullscreen dimensions for later reuse.
        actual_w, actual_h = self.screen.get_size()
        self.screen_width = actual_w
        self.screen_height = actual_h

        # --- 4. DYNAMIC CENTERING ---
        self.offset_x = (actual_w - (self.cols * self.TILE_SIZE)) // 2
        self.offset_y = (actual_h - (self.rows * self.TILE_SIZE)) // 2

        self._preload_raw_images()
        self.scale_sprites()

    def _refit_window(self) -> None:
        """Recompute rows/cols, tile size, and resize the window."""
        self.rows = len(self.monitor.grid)
        self.cols = len(self.monitor.grid[0])
        available_w = self.screen_max_w * 0.85
        available_h = self.screen_max_h * 0.85
        tile_h = int((available_h - (2 * self.margin)) // self.rows)
        tile_w = int((available_w - (2 * self.margin)) // self.cols)
        new_tile = max(12, min(tile_h, tile_w, 48))
        self._update_dimensions(new_tile)

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
                self.maze_width = self._base_maze_width
                self.maze_height = self._base_maze_height
                self.monitor = self._build_monitor()
                current_level = 1

                while True:
                    result = self._run_game(current_level)
                    if result == "quit":
                        break
                    elif (
                        result == "win"
                        and current_level == self.monitor.level
                    ):
                        self._run_end_screen("win", self.monitor.player.score)
                        break
                    elif result == "win":
                        score = self.monitor.player.score
                        lives = self.monitor.player.lives
                        god_mode = self.monitor.player.god_mode
                        ghosts_frozen = self.monitor.ghosts_frozen
                        collision = self.monitor.collision
                        current_level += 1

                        self._seed = 0
                        self.maze_width += 3
                        self.maze_height += 3
                        self.monitor = self._build_monitor()
                        self._refit_window()

                        self.monitor.player.score = score
                        self.monitor.player.lives = lives
                        self.monitor.player.god_mode = god_mode
                        self.monitor.ghosts_frozen = ghosts_frozen
                        self.monitor.collision = collision
                        continue
                    elif result == "lose":
                        self._run_end_screen("lose", self.monitor.player.score)
                        break

    def _run_game(self, level: int = 1) -> str:
        """Delegate the game loop to Game and return its result."""
        return Game(self.monitor, self.config, self, level).run()

    def render_frame(
        self, elapsed: int, fps: int, max_time: int, level: int
    ) -> None:
        """Draw one frame to the screen."""
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
