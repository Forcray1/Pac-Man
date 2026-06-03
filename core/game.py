from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pygame

from core.sounds import get_sounds

if TYPE_CHECKING:
    from core.monitor import Monitor
    from display.pygame_viewer import PygameViewer


class Game:
    """
    Owns the per-level game loop: input, state updates, win/lose logic.
    Display is delegated back to the viewer via render_frame().
    """

    def __init__(
        self,
        monitor: Monitor,
        config: dict[str, Any],
        viewer: PygameViewer,
        level: int = 1,
    ) -> None:
        """
        Initialize the game loop for a single level using the shared
        monitor, config and viewer.
        """
        self.monitor = monitor
        self.config = config
        self.viewer = viewer
        self.level = level

    def run(self) -> str:
        """
        Run one level. Returns 'win', 'lose', or 'quit'.
        """
        clock = pygame.time.Clock()
        fps = 30
        max_time_ms: int = int(self.config.get("level_max_time", 90)) * 1000
        elapsed_ms = 0
        death_ms = 0
        maze_swapped = False
        spawn_x = self.monitor.player.x
        spawn_y = self.monitor.player.y

        self.viewer._first_frame = True
        self.viewer.render_frame(elapsed_ms, max_time_ms, self.level)
        last_tick = pygame.time.get_ticks()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    get_sounds().stop_all_loops()
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        get_sounds().stop_all_loops()
                        if self.viewer._run_pause_menu() == "quit":
                            get_sounds().stop_all_loops()
                            return "quit"
                        last_tick = pygame.time.get_ticks()
                    cheat_enabled = self.config.get("cheat_mode")
                    if cheat_enabled and event.key == pygame.K_c:
                        get_sounds().stop_all_loops()
                        if self.viewer._run_cheat_menu() == "next_level":
                            get_sounds().stop_all_loops()
                            return "win"
                        last_tick = pygame.time.get_ticks()
                    if not self.monitor.player.is_dying:
                        if event.key in (pygame.K_UP, pygame.K_w):
                            self.monitor.request_player_direction(0, -1)
                        elif event.key in (pygame.K_DOWN, pygame.K_s):
                            self.monitor.request_player_direction(0, 1)
                        elif event.key in (pygame.K_LEFT, pygame.K_a):
                            self.monitor.request_player_direction(-1, 0)
                        elif event.key in (pygame.K_RIGHT, pygame.K_d):
                            self.monitor.request_player_direction(1, 0)

            now = pygame.time.get_ticks()
            dt_ms = now - last_tick
            last_tick = now
            elapsed_ms += dt_ms

            self.monitor.update(dt_ms)

            if self.monitor.is_cleared():
                get_sounds().stop_all_loops()
                return "win"
            if self.monitor.difficulty == 5 and not maze_swapped:
                if elapsed_ms >= max_time_ms // 2:
                    maze_swapped = True
                    self.monitor._change_maze()
            if (elapsed_ms >= max_time_ms
                    and not self.monitor.player.is_dying):
                self.monitor.player.die()

            if self.monitor.player.is_dying:
                death_ms += dt_ms
                if death_ms >= 1300:
                    death_ms = 0
                    if self.monitor.player.lives <= 0:
                        get_sounds().stop_all_loops()
                        return "lose"
                    elapsed_ms = 0
                    maze_swapped = False
                    self._reset_level(spawn_x, spawn_y)

            blocked_ms = self.viewer.render_frame(
                elapsed_ms, max_time_ms, self.level)
            if blocked_ms:
                last_tick = pygame.time.get_ticks()
            clock.tick(fps)

    def _reset_level(self, spawn_x: int, spawn_y: int) -> None:
        """
        Reset state after losing a life.
        """
        self.viewer.reset = True
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
