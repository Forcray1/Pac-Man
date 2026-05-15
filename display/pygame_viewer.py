from __future__ import annotations

import time

import pygame

from core.monitor import Monitor
from core.scores import ScoreManager
from display._maze_utils import _FastMazeGenerator, _maze_cache
from display.hud_mixin import HudMixin
from display.renderer_mixin import RendererMixin
from display.screens_mixin import ScreensMixin
from display.sprite_mixin import SpritesMixin


class PygameViewer(SpritesMixin, RendererMixin, HudMixin, ScreensMixin):
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
                    elif (
                        result == "win"
                        and current_level == self.monitor.level
                    ):
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
