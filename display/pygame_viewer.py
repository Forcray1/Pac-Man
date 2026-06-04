from __future__ import annotations

from typing import Any

import pygame

from core.game import Game
from core.monitor import Monitor
from core.scores import ScoreManager
from core.sounds import get_sounds
from display._maze_utils import _maze_cache, MazeGenerator
from display.hud_mixin import HudMixin
from display.renderer_mixin import RendererMixin
from display.menu_screens_mixin import MenuScreensMixin
from display.overlay_screens_mixin import OverlayScreensMixin
from display.sprite_mixin import SpritesMixin
from display.helper import get_helper


class PygameViewer(
    SpritesMixin,
    RendererMixin,
    HudMixin,
    MenuScreensMixin,
    OverlayScreensMixin,
):
    def __init__(self, config: dict[str, Any]):
        """
        Build the Pygame window, load assets, and instantiate the monitor
        for the first level from config.
        """
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        get_sounds().preload_all()

        # SCREEN BOUNDS DETECTION
        info = pygame.display.Info()
        # Get the current monitor resolution
        self.screen_max_w = info.current_w
        self.screen_max_h = info.current_h
        screen_max_w = self.screen_max_w
        screen_max_h = self.screen_max_h
        self.reset = False
        self._skip_next_ready = False  # prevents double READY! after death
        self._first_frame = False  # set by Game at the start of each level

        self.margin = 60

        if config:
            self.maze_width = int(config.get("width", 15))
            self.maze_height = int(config.get("height", 15))
            self._seed = int(config.get("seed", 0))
            self._base_maze_width = self.maze_width
            self._base_maze_height = self.maze_height
            self.config = {
                "seed": self._seed,
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
            self._base_maze_width = self.maze_width
            self._base_maze_height = self.maze_height
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

        # AUTO-COMPUTE TILE SIZE
        # Tile size is computed so the maze fits inside the full screen,
        # leaving a margin on each side.
        available_w = screen_max_w - (2 * self.margin)
        available_h = screen_max_h - (2 * self.margin)
        # Compute the maximum tile size that fits in HEIGHT
        tile_h = int(available_h // self.rows)
        # Compute the maximum tile size that fits in WIDTH
        tile_w = int(available_w // self.cols)

        # Take the minimum so the maze fits both dimensions; no upper cap
        # so that large mazes still fill the screen.
        self.TILE_SIZE = max(4, min(tile_h, tile_w))

        # FULLSCREEN WINDOW
        _existing = pygame.display.get_surface()
        if _existing is not None:
            self.screen = _existing
        else:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption("Pac-Man - Pygame Viewer")

        # Use the actual fullscreen surface size to centre the maze.
        actual_w, actual_h = self.screen.get_size()

        # DYNAMIC CENTERING
        self.offset_x = (actual_w - (self.cols * self.TILE_SIZE)) // 2
        self.offset_y = (actual_h - (self.rows * self.TILE_SIZE)) // 2

        self._preload_raw_images()
        self.scale_sprites()

    def _fit_maze_to_screen(self) -> None:
        """
        Recompute rows, columns and tile size so the (possibly resized)
        maze still fits inside the fullscreen window.
        """
        self.rows = len(self.monitor.grid)
        self.cols = len(self.monitor.grid[0])
        available_w = self.screen_max_w - (2 * self.margin)
        available_h = self.screen_max_h - (2 * self.margin)
        tile_h = int(available_h // self.rows)
        tile_w = int(available_w // self.cols)
        new_tile = max(4, min(tile_h, tile_w))
        self._update_dimensions(new_tile)

    def _build_monitor(self) -> Monitor:
        """
        Build the Monitor for the current maze size and seed.
        """
        cache_key = (self.maze_width, self.maze_height, self._seed)
        if self._seed > 0 and cache_key in _maze_cache:
            raw_maze = _maze_cache[cache_key]
        else:
            generator = MazeGenerator(
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
        get_helper(self.screen).show("Point and click or arrows")
        while True:
            # Reset maze dimensions for the menu and first level
            self.maze_width = self._base_maze_width
            self.maze_height = self._base_maze_height
            self.monitor = self._build_monitor()
            self._fit_maze_to_screen()

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
                self.rows = len(self.monitor.grid)
                self.cols = len(self.monitor.grid[0])
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
                        ghosts_frozen = self.monitor.ghosts_frozen
                        collision = self.monitor.collision
                        current_level += 1

                        self._seed = 0
                        self.maze_width += 3
                        self.maze_height += 3
                        self.monitor = self._build_monitor()
                        self._fit_maze_to_screen()

                        self.monitor.player.score = score
                        self.monitor.player.lives = lives
                        self.monitor.ghosts_frozen = ghosts_frozen
                        self.monitor.collision = collision
                        continue
                    elif result == "lose":
                        self._run_screamer()
                        self._run_end_screen("lose", self.monitor.player.score)
                        break

    def _run_game(self, level: int = 1) -> str:
        """
        Delegate the game loop to Game and return its result.
        """
        return Game(self.monitor, self.config, self, level).run()

    def render_frame(
        self, elapsed_ms: int, max_time_ms: int, level: int
    ) -> int:
        """
        Draw one frame to the screen. Returns the number of milliseconds
        spent blocking on the READY! overlay, so the caller can keep its
        game clock from counting that pause.
        """
        self.screen.fill((0, 0, 0))
        self.draw_maze()
        self.draw_items()
        if self.practice:
            self.draw_ghost_paths()
        self.draw_ghosts()
        self.draw_player()
        self._draw_hud(elapsed_ms, max_time_ms, level)
        pygame.display.flip()
        # Determine whether to show the READY! overlay.
        # After a death-reset self.reset is set; the first frame of a fresh
        # level is flagged by Game via self._first_frame.
        _trigger_ready = self.reset
        if self._first_frame:
            self._first_frame = False
            if self._skip_next_ready:
                self._skip_next_ready = False
            else:
                _trigger_ready = True
        if self.reset:
            self._skip_next_ready = True
        if not _trigger_ready:
            return 0
        return self._show_ready_overlay(elapsed_ms, max_time_ms, level)

    def _show_ready_overlay(
        self, elapsed_ms: int, max_time_ms: int, level: int
    ) -> int:
        """
        Play the start jingle and hold the frozen scene under a centred
        "READY!" banner for 1s. Returns the milliseconds spent blocking so
        the caller can exclude them from the game clock.
        """
        overlay_start = pygame.time.get_ticks()
        get_sounds().stop_all_loops()
        get_sounds().play("start", volume=0.7)
        pygame.event.set_blocked(None)

        ready_surf = self.render_text("READY!")

        duration_ms = 1000
        clock = pygame.time.Clock()
        start = pygame.time.get_ticks()
        while pygame.time.get_ticks() - start < duration_ms:
            self.screen.fill((0, 0, 0))
            self.draw_maze()
            self.draw_items()
            if self.practice:
                self.draw_ghost_paths()
            self.draw_ghosts()
            self.draw_player()
            self._draw_hud(elapsed_ms, max_time_ms, level)
            if ready_surf is not None:
                w, h = self.screen.get_size()
                self.screen.blit(ready_surf, ready_surf.get_rect(
                    center=(w // 2, h // 2 + self.TILE_SIZE)
                ))
            pygame.display.flip()
            clock.tick(30)

        pygame.event.set_allowed(None)
        pygame.event.pump()
        pygame.event.clear()
        self.reset = False
        return pygame.time.get_ticks() - overlay_start
