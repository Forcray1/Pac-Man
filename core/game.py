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
        Initialize the game loop for a single *level* using the shared
        *monitor*, *config* and *viewer*.
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
        max_time: int = int(self.config.get("level_max_time", 90))
        elapsed = 0
        death_timer = 0
        spawn_x = self.monitor.player.x
        spawn_y = self.monitor.player.y

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
                    cheat_enabled = self.config.get("cheat_mode", False)
                    if cheat_enabled and event.key == pygame.K_c:
                        get_sounds().stop_all_loops()
                        if self.viewer._run_cheat_menu() == "next_level":
                            get_sounds().stop_all_loops()
                            return "win"

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
                get_sounds().stop_all_loops()
                return "win"
            if self.monitor.difficulty == 5:
                if elapsed == (max_time * fps) // 2:
                    self.monitor._change_maze()
            if elapsed >= max_time * fps and not self.monitor.player.is_dying:
                self.monitor.player.die()

            if self.monitor.player.is_dying:
                death_timer += 1
                if death_timer >= 40:  # ~1.3 s at 30 FPS
                    death_timer = 0
                    if self.monitor.player.lives <= 0:
                        get_sounds().stop_all_loops()
                        return "lose"
                    elapsed = 0
                    self._reset_level(spawn_x, spawn_y)

            self.viewer.render_frame(elapsed, fps, max_time, self.level)
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
