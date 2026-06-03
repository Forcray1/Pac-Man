from __future__ import annotations

import os
from typing import TYPE_CHECKING, Callable, List, Tuple

import pygame

from core.sounds import get_sounds
from display._maze_utils import _ROOT, _safe_font
from display.helper import get_helper
from display.menu import MenuNav

_TYPO_PATH = os.path.join(_ROOT, "assets", "Typo", "ByteBounce.ttf")

if TYPE_CHECKING:
    from core.scores import ScoreManager


class MenuScreensMixin:
    """
    Pre-game menu screens: main menu, highscores and instructions.
    """

    if TYPE_CHECKING:
        screen: pygame.Surface
        sprites: dict[str, pygame.Surface | list[pygame.Surface | None] | None]
        score_manager: ScoreManager
        _draw_centered: Callable[..., None]

    def _run_menu(self) -> str:
        """
        Main menu. Returns 'play', 'highscores', 'instructions', 'quit'.
        """
        _w, _h = self.screen.get_size()
        font_item = _safe_font(_TYPO_PATH, max(40, _h * 72 // 1080))

        LOGO_CENTER_X_RATIO = 0.527  # 0.0 = left edge, 1.0 = right edge
        LOGO_CENTER_Y = 180  # pixels from the top of the screen
        LOGO_WIDTH_RATIO = 0.35  # logo width as a fraction of screen width

        _logo_path = os.path.join(_ROOT, "assets", "Utils", "Logo.png")
        _logo_raw = (
            pygame.image.load(_logo_path).convert_alpha()
            if os.path.exists(_logo_path)
            else None
        )

        _bg_path = os.path.join(_ROOT,
                                "assets",
                                "Utils",
                                "background_main.jpg")
        _bg_raw = (
            pygame.image.load(_bg_path).convert()
            if os.path.exists(_bg_path)
            else None
        )
        _item_gap = max(60, _h * 96 // 1080)
        items = [
            "Start Game", "View Highscores",
            "Instructions", "Exit",
        ]
        actions = ["play", "highscores", "instructions", "quit"]
        clock = pygame.time.Clock()
        nav = MenuNav(len(items))

        anim_x = -250

        while True:
            w, h = self.screen.get_size()

            # Pre-compute clickable rects for menu items (stable hitboxes).
            item_rects: list[pygame.Rect] = []
            for i, label in enumerate(items):
                lbl_surf = font_item.render(label, True, (200, 200, 200))
                y_i = h // 2 - 80 + i * _item_gap
                r = lbl_surf.get_rect(centerx=w // 2, y=y_i)
                item_rects.append(r.inflate(180, 24))

            cmd, idx = nav.handle(item_rects)
            if cmd == "quit":
                return "quit"
            if cmd == "escape":
                # ESC acts as the "Exit" entry: leave the arcade menu.
                get_sounds().play("button", volume=0.6)
                return "quit"
            if cmd == "confirm":
                get_sounds().play("button", volume=0.6)
                return actions[idx]

            if _bg_raw is not None:
                _bg = pygame.transform.smoothscale(_bg_raw, (w, h))
                self.screen.blit(_bg, (0, 0))
            else:
                self.screen.fill((0, 0, 0))

            # Animation at the bottom
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
                    self.screen.blit(pac_sprite, (anim_x, anim_y))

            for i, name in enumerate(["Blinky", "Pinky", "Inky", "Clyde"]):
                ghost_sprite_list = self.sprites.get(f"{name}_Right")
                if isinstance(ghost_sprite_list, list):
                    ghost_sprite = ghost_sprite_list[ghost_frame]
                    if ghost_sprite:
                        ghost_x = anim_x + 100 + 60 * i
                        self.screen.blit(ghost_sprite, (ghost_x, anim_y))

            if _logo_raw is not None:
                _lw = int(w * LOGO_WIDTH_RATIO)
                _lh = int(_logo_raw.get_height() * _lw / _logo_raw.get_width())
                _logo = pygame.transform.smoothscale(_logo_raw, (_lw, _lh))
                self.screen.blit(_logo, (_logo.get_rect(
                    centerx=int(w * LOGO_CENTER_X_RATIO),
                    centery=LOGO_CENTER_Y,
                )))

            for i, label in enumerate(items):
                chosen = i == nav.selected
                color = (255, 255, 0) if chosen else (200, 200, 200)
                prefix = "> " if chosen else "  "
                self._draw_centered(
                    f"{prefix}{label}", font_item, color,
                    h // 2 - 80 + i * _item_gap,
                )
            _helper = get_helper(self.screen)
            _helper.update()
            _helper.draw(self.screen)
            pygame.display.flip()
            clock.tick(30)

    def _run_highscores(self) -> None:
        """
        Show top-10 leaderboard. ENTER or ESC to go back.
        """
        _w, _h = self.screen.get_size()
        font_title = _safe_font(_TYPO_PATH, max(14, _h * 44 // 1080))
        font_row = _safe_font(_TYPO_PATH, max(10, _h * 26 // 1080))
        font_hint = _safe_font(_TYPO_PATH, max(10, _h * 22 // 1080))
        _title_y = max(10, _h * 30 // 1080)
        _row_start = max(50, _h * 100 // 1080)
        _row_gap = max(14, _h * 36 // 1080)
        clock = pygame.time.Clock()

        while True:
            w, h = self.screen.get_size()
            mouse = pygame.mouse.get_pos()
            back_y = h - _h * 50 // 1080
            back_surf = font_hint.render(
                "ENTER or ESC  -  back", True, (255, 255, 255)
            )
            back_rect = back_surf.get_rect(centerx=w // 2, y=back_y)
            back_rect = back_rect.inflate(180, 24)
            hovering_back = back_rect.collidepoint(mouse)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                        get_sounds().play("button", volume=0.6)
                        return
                if (event.type == pygame.MOUSEBUTTONDOWN
                        and event.button == 1
                        and back_rect.collidepoint(event.pos)):
                    get_sounds().play("button", volume=0.6)
                    return

            self.screen.fill((0, 0, 0))
            self._draw_centered(
                "HIGH SCORES", font_title, (255, 255, 0), _title_y)
            scores = self.score_manager.top_scores()
            if not scores:
                self._draw_centered(
                    "No scores yet!", font_row, (180, 180, 180), h // 2,
                )
            else:
                for i, (name, score) in enumerate(scores):
                    line = f"{i + 1:2}.  {name:<10}  {score:>8}"
                    self._draw_centered(
                        line, font_row, (255, 255, 255),
                        _row_start + i * _row_gap,
                    )
            back_color = (255, 255, 0) if hovering_back else (120, 120, 120)
            self._draw_centered(
                "ENTER or ESC  -  back",
                font_hint, back_color, back_y,
            )
            pygame.display.flip()
            clock.tick(30)

    def _run_instructions(self) -> None:
        """
        Show controls and rules. ENTER or ESC to go back.
        """
        _w, _h = self.screen.get_size()
        font_title = _safe_font(_TYPO_PATH, max(14, _h * 44 // 1080))
        font_body = _safe_font(_TYPO_PATH, max(10, _h * 24 // 1080))
        _title_y = max(10, _h * 30 // 1080)
        _lines_start = max(50, _h * 110 // 1080)
        _line_gap = max(16, _h * 38 // 1080)
        clock = pygame.time.Clock()
        # Each entry: (text, colour)
        lines: List[Tuple[str, Tuple[int, int, int]]] = [
            ("CONTROLS", (255, 255, 0)),
            ("Arrow keys / WASD  -  Move", (200, 200, 200)),
            ("ESC  -  Pause menu", (200, 200, 200)),
            ("", (0, 0, 0)),
            ("RULES", (255, 255, 0)),
            ("Eat all pac-gums to win.", (200, 200, 200)),
            ("Ghosts kill you on touch.", (200, 200, 200)),
            ("Super pac-gum makes ghosts edible.", (200, 200, 200)),
            ("3 lives total.", (200, 200, 200)),
            ("", (0, 0, 0)),
            ("ENTER or ESC  -  back", (120, 120, 120)),
        ]

        back_idx = len(lines) - 1

        while True:
            w, h = self.screen.get_size()
            mouse = pygame.mouse.get_pos()
            back_y = _lines_start + back_idx * _line_gap
            back_surf = font_body.render(lines[back_idx][0], True,
                                         (255, 255, 255))
            back_rect = back_surf.get_rect(centerx=w // 2, y=back_y)
            back_rect = back_rect.inflate(180, 24)
            hovering_back = back_rect.collidepoint(mouse)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                        get_sounds().play("button", volume=0.6)
                        return
                if (event.type == pygame.MOUSEBUTTONDOWN
                        and event.button == 1
                        and back_rect.collidepoint(event.pos)):
                    get_sounds().play("button", volume=0.6)
                    return

            self.screen.fill((0, 0, 0))
            self._draw_centered(
                "INSTRUCTIONS", font_title, (255, 255, 0), _title_y
            )
            for i, (text, color) in enumerate(lines):
                draw_color = color
                if i == back_idx and hovering_back:
                    draw_color = (255, 255, 0)
                self._draw_centered(
                    text, font_body, draw_color,
                    _lines_start + i * _line_gap)
            pygame.display.flip()
            clock.tick(30)
