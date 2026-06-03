from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

import pygame

from display._maze_utils import _ROOT, _safe_font

_TYPO_PATH = os.path.join(_ROOT, "assets", "Typo", "ByteBounce.ttf")

if TYPE_CHECKING:
    from core.monitor import Monitor


class HudMixin:
    """
    Handles on-screen text helpers and the in-game HUD.
    """

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
        """
        Draw text horizontally centred at vertical position y.
        """
        surf = font.render(text, True, color)
        x = (self.screen.get_width() - surf.get_width()) // 2
        self.screen.blit(surf, (x, y))

    def _draw_hud(
        self, elapsed_ms: int, max_time_ms: int, level: int = 1
    ) -> None:
        """
        Draw score, lives, level and remaining time at the top.
        """
        _h = self.screen.get_height()
        font = _safe_font(_TYPO_PATH, max(10, _h * 20 // 1080))
        player = self.monitor.player
        remaining = max(0, (max_time_ms - elapsed_ms) // 1000)
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
            active: list[str] = []
            if not self.monitor.collision:
                active.append("NO COLLISION")
            if self.monitor.ghosts_frozen:
                active.append("PAUSE GHOSTS")
            if active:
                hud_font = _safe_font(
                    _TYPO_PATH, max(8, _h * 16 // 1080)
                )
                bottom_y = (
                    self.screen.get_height() - max(12, _h * 25 // 1080)
                )
                text = "Active cheats: " + ", ".join(active)
                self.screen.blit(
                    hud_font.render(text, True, (0, 255, 0)),
                    (10, bottom_y),
                )
