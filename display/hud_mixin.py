from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pygame

if TYPE_CHECKING:
    from core.monitor import Monitor


class HudMixin:
    """Handles on-screen text helpers and the in-game HUD."""

    if TYPE_CHECKING:
        screen: pygame.Surface
        monitor: Monitor
        config: dict[str, Any]

    def _draw_centered(
        self,
        text: str,
        font: pygame.font.Font,
        color: tuple[int, int, int],
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
        _h = self.screen.get_height()
        font = pygame.font.SysFont(
            "Arial", max(10, _h * 20 // 1080), bold=True)
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
            hud_font = pygame.font.SysFont("Arial", max(8, _h * 16 // 1080))
            bottom_y = self.screen.get_height() - max(12, _h * 25 // 1080)

            if self.monitor.player.god_mode:
                god_status = "ON"
                color = (0, 255, 0)
            else:
                god_status = "OFF"
                color = (255, 255, 255)

            if self.monitor.collision:
                collision_status = "OFF"
            else:
                collision_status = "ON"

            if self.monitor.ghosts_frozen:
                frozen_status = "ON"
            else:
                frozen_status = "OFF"

            cheat_list = {"collision": collision_status,
                          "frozen": frozen_status
                          }

            if "ON" in cheat_list.values():
                cheat_on = True
                lists = [x for x in cheat_list if cheat_list[x] == "ON"]
            else:
                cheat_on = False

            cheat_text = f"Cheats: [G] God Mode ({god_status})"
            self.screen.blit(
                hud_font.render(cheat_text, True, color), (10, bottom_y)
            )
            if cheat_on:
                active_cheat_text = f"Active cheats: ({', '.join(lists)})"
                self.screen.blit(
                    hud_font.render(active_cheat_text, True, color),
                    (225, bottom_y)
                )
