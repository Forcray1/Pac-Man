from __future__ import annotations

import pygame


class HudMixin:
    """Handles on-screen text helpers and the in-game HUD."""

    def _draw_centered(
        self,
        text: str,
        font: pygame.font.Font,
        color: tuple,
        y: int,
    ) -> None:
        """Draw text horizontally centred at vertical position y."""
        surf = font.render(text, True, color)
        x = (self.screen.get_width() - surf.get_width()) // 2
        self.screen.blit(surf, (x, y))

    def _draw_hud(
        self, elapsed: int, fps: int, max_time: int, level: int = 1
    ) -> None:
        """Draw score, lives, level and remaining time at the top."""
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
                color = (0, 255, 0)
            else:
                god_status = "OFF"
                color = (255, 255, 255)

            cheat_text = f"Cheats: [G] God Mode ({god_status})"
            self.screen.blit(
                hud_font.render(cheat_text, True, color), (10, bottom_y)
            )
