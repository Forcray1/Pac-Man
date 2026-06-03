from __future__ import annotations

import os
import random
from typing import TYPE_CHECKING, Callable

import pygame

from core.sounds import get_sounds
from display._maze_utils import _ROOT, _safe_font
from display.menu import MenuNav

_TYPO_PATH = os.path.join(_ROOT, "assets", "Typo", "ByteBounce.ttf")

if TYPE_CHECKING:
    from core.monitor import Monitor
    from core.scores import ScoreManager


class OverlayScreensMixin:
    """
    In-game overlays and cutscenes: the jump-scare, the end screen, and the
    pause and cheat menus.
    """

    if TYPE_CHECKING:
        screen: pygame.Surface
        monitor: Monitor
        score_manager: ScoreManager
        _draw_centered: Callable[..., None]

    def _run_screamer(self) -> None:
        """
        Jumpscare shown right before the GAME OVER screen.
        """
        screamer_path = os.path.join(
            _ROOT, "assets", "Utils", "screamer.jpg"
        )
        if not os.path.exists(screamer_path):
            return

        try:
            raw = pygame.image.load(screamer_path).convert()
        except pygame.error:
            return

        w, h = self.screen.get_size()
        clock = pygame.time.Clock()

        self.screen.fill((0, 0, 0))
        pygame.display.flip()
        pygame.event.pump()
        jumpscare_channel = get_sounds().play("jumpscare", volume=1.4)
        pygame.time.delay(120)

        duration_ms = 400
        start = pygame.time.get_ticks()

        while True:
            elapsed = pygame.time.get_ticks() - start
            if elapsed >= duration_ms:
                break

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return

            pulse = 0.5 + 0.5 * abs(((elapsed // 60) % 4) - 2) / 2
            zoom = 1.05 + 0.15 * pulse
            shake = max(4, 18 - int(elapsed / 120))
            sx = random.randint(-shake, shake)
            sy = random.randint(-shake, shake)

            sw = int(w * zoom)
            sh = int(h * zoom)
            img = pygame.transform.smoothscale(raw, (sw, sh))

            self.screen.fill((0, 0, 0))
            self.screen.blit(
                img, ((w - sw) // 2 + sx, (h - sh) // 2 + sy)
            )

            if (elapsed // 80) % 2 == 0:
                overlay = pygame.Surface((w, h), pygame.SRCALPHA)
                overlay.fill((180, 0, 0, 60))
                self.screen.blit(overlay, (0, 0))

            pygame.display.flip()
            clock.tick(60)

        fade = pygame.Surface((w, h))
        fade.fill((0, 0, 0))
        for alpha in range(0, 256, 32):
            fade.set_alpha(alpha)
            self.screen.blit(
                pygame.transform.smoothscale(raw, (w, h)), (0, 0)
            )
            self.screen.blit(fade, (0, 0))
            pygame.display.flip()
            pygame.event.pump()
            clock.tick(60)

        # Kill the sound so it doesn't bleed into game-over.
        if jumpscare_channel is not None:
            jumpscare_channel.stop()

    def _run_end_screen(self, result: str, final_score: int) -> None:
        """
        Game-over or victory: show score, ask name, save it.
        """
        _w, _h = self.screen.get_size()
        font_title = _safe_font(_TYPO_PATH, max(16, _h * 52 // 1080))
        font_score = _safe_font(_TYPO_PATH, max(12, _h * 32 // 1080))
        font_label = _safe_font(_TYPO_PATH, max(10, _h * 26 // 1080))
        font_input = _safe_font(_TYPO_PATH, max(14, _h * 38 // 1080))
        clock = pygame.time.Clock()

        title = "YOU WIN!" if result == "win" else "GAME OVER"
        t_color = (0, 255, 100) if result == "win" else (255, 50, 50)
        name = ""

        while True:
            w, h = self.screen.get_size()
            mouse = pygame.mouse.get_pos()

            # Compute clickable rects for SAVE / SKIP buttons.
            btn_y = h - max(24, h * 60 // 1080)
            save_surf = font_label.render("SAVE", True, (255, 255, 255))
            skip_surf = font_label.render("SKIP", True, (255, 255, 255))
            gap = max(60, w * 60 // 1920)
            total_w = save_surf.get_width() + skip_surf.get_width() + gap
            start_x = (w - total_w) // 2
            save_rect = save_surf.get_rect(
                topleft=(start_x, btn_y)
            ).inflate(60, 20)
            skip_rect = skip_surf.get_rect(
                topleft=(start_x + save_surf.get_width() + gap, btn_y)
            ).inflate(60, 20)
            hovering_save = save_rect.collidepoint(mouse)
            hovering_skip = skip_rect.collidepoint(mouse)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        get_sounds().play("button", volume=0.6)
                        self.score_manager.add(
                            name or "Anonymous", final_score
                        )
                        return
                    elif event.key == pygame.K_ESCAPE:
                        get_sounds().play("button", volume=0.6)
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
                if (event.type == pygame.MOUSEBUTTONDOWN
                        and event.button == 1):
                    if save_rect.collidepoint(event.pos):
                        get_sounds().play("button", volume=0.6)
                        self.score_manager.add(
                            name or "Anonymous", final_score
                        )
                        return
                    if skip_rect.collidepoint(event.pos):
                        get_sounds().play("button", volume=0.6)
                        return

            self.screen.fill((0, 0, 0))
            self._draw_centered(title, font_title, t_color, h // 5)
            self._draw_centered(
                f"Final Score: {final_score}",
                font_score, (255, 255, 255), h // 3,
            )
            self._draw_centered(
                "Enter your name:", font_label,
                (180, 180, 180), h // 2 - max(10, h * 30 // 1080),
            )
            self._draw_centered(
                name + "_", font_input,
                (255, 255, 0), h // 2 + max(8, h * 20 // 1080),
            )
            save_color = (255, 255, 0) if hovering_save else (180, 180, 180)
            skip_color = (255, 255, 0) if hovering_skip else (180, 180, 180)
            self.screen.blit(
                font_label.render("SAVE", True, save_color),
                (start_x, btn_y),
            )
            self.screen.blit(
                font_label.render("SKIP", True, skip_color),
                (start_x + save_surf.get_width() + gap, btn_y),
            )
            self._draw_centered(
                "ENTER / click SAVE  |  ESC / click SKIP",
                font_label, (100, 100, 100),
                btn_y - max(20, h * 36 // 1080),
            )
            pygame.display.flip()
            clock.tick(30)

    def _run_pause_menu(self) -> str:
        """
        Overlay pause menu. Returns 'resume' or 'quit'.
        """
        _w, _h = self.screen.get_size()
        font_title = _safe_font(_TYPO_PATH, max(14, _h * 46 // 1080))
        font_item = _safe_font(_TYPO_PATH, max(10, _h * 28 // 1080))
        font_hint = _safe_font(_TYPO_PATH, max(8, _h * 16 // 1080))
        _item_gap = max(20, _h * 44 // 1080)
        items = ["RESUME", "EXIT TO MAIN MENU"]
        actions = ["resume", "quit"]
        clock = pygame.time.Clock()
        blink_timer = 0
        nav = MenuNav(len(items), escape_keys=(pygame.K_ESCAPE, pygame.K_p))

        # Capture the current game frame to use as background
        background = self.screen.copy()

        while True:
            w, h = self.screen.get_size()
            cy = h // 2

            # Build clickable rects for each pause-menu item.
            item_rects: list[pygame.Rect] = []
            for i, label in enumerate(items):
                lbl_surf = font_item.render(label, True, (200, 200, 200))
                y_i = cy - max(8, _h * 16 // 1080) + i * _item_gap
                r = lbl_surf.get_rect(centerx=w // 2, y=y_i)
                item_rects.append(r.inflate(180, 24))

            cmd, idx = nav.handle(item_rects)
            if nav.changed:
                blink_timer = 0
            if cmd == "quit":
                return "quit"
            if cmd == "escape":
                get_sounds().play("button", volume=0.6)
                return "resume"
            if cmd == "confirm":
                get_sounds().play("button", volume=0.6)
                return actions[idx]

            blink_timer += 1

            # Frozen game frame + dark overlay
            self.screen.blit(background, (0, 0))
            overlay = pygame.Surface((w, h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 190))
            self.screen.blit(overlay, (0, 0))

            # Title
            self._draw_centered(
                "- PAUSED -", font_title,
                (255, 255, 0), cy - max(30, _h * 80 // 1080)
            )

            # Blue separator
            sep_x1, sep_x2 = w // 4, 3 * w // 4
            _sep_off = max(12, _h * 32 // 1080)
            pygame.draw.line(
                self.screen, (33, 33, 255),
                (sep_x1, cy - _sep_off), (sep_x2, cy - _sep_off), 2,
            )

            # Menu items
            for i, label in enumerate(items):
                if i == nav.selected:
                    show_arrow = (blink_timer // 15) % 2 == 0
                    prefix = "> " if show_arrow else "  "
                    color: tuple[int, int, int] = (255, 255, 0)
                else:
                    prefix = "  "
                    color = (200, 200, 200)
                self._draw_centered(
                    f"{prefix}{label}", font_item, color,
                    cy - max(8, _h * 16 // 1080) + i * _item_gap,
                )

            # Hint
            self._draw_centered(
                "ESC / P  -  RESUME",
                font_hint, (100, 100, 100), h - max(14, _h * 36 // 1080),
            )

            pygame.display.flip()
            clock.tick(30)

    def _run_cheat_menu(self) -> str:
        """
        In-game cheat overlay (opened with the cheat key). Lets the player
        toggle collision and ghost freezing, add a life, skip to the next
        level, or resume.
        """
        _w, _h = self.screen.get_size()
        font_title = _safe_font(_TYPO_PATH, max(14, _h * 46 // 1080))
        font_item = _safe_font(_TYPO_PATH, max(10, _h * 26 // 1080))
        font_hint = _safe_font(_TYPO_PATH, max(8, _h * 16 // 1080))
        _item_gap = max(18, _h * 40 // 1080)
        clock = pygame.time.Clock()
        blink_timer = 0
        nav = MenuNav(5)

        background = self.screen.copy()

        def _activate(idx: int) -> str | None:
            """
            Apply the selected cheat. Returns 'resume'/'next_level' if
            the menu should exit, else None.
            """
            if idx == 0:
                self.monitor.collision = not self.monitor.collision
            elif idx == 1:
                self.monitor.ghosts_frozen = (
                    not self.monitor.ghosts_frozen
                )
            elif idx == 2:
                self.monitor.player.lives += 1
            elif idx == 3:
                return "next_level"
            elif idx == 4:
                return "resume"
            return None

        while True:
            w, h = self.screen.get_size()
            cy = h // 2

            collision_tag = "[OFF]" if self.monitor.collision else "[ON]"
            ghosts_tag = "[ON]" if self.monitor.ghosts_frozen else "[OFF]"
            display_items = [
                f"NO COLLISION  {collision_tag}",
                f"PAUSE GHOSTS  {ghosts_tag}",
                f"ADD LIFE      ({self.monitor.player.lives})",
                "NEXT LEVEL",
                "RESUME",
            ]

            # Build clickable rects for each cheat item.
            item_rects: list[pygame.Rect] = []
            for i, label in enumerate(display_items):
                lbl_surf = font_item.render(label, True, (200, 200, 200))
                y_i = cy - max(14, _h * 36 // 1080) + i * _item_gap
                r = lbl_surf.get_rect(centerx=w // 2, y=y_i)
                item_rects.append(r.inflate(220, 24))

            cmd, idx = nav.handle(item_rects)
            if nav.changed:
                blink_timer = 0
            if cmd == "quit":
                return "resume"
            if cmd == "escape":
                get_sounds().play("button", volume=0.6)
                return "resume"
            if cmd == "confirm":
                get_sounds().play("button", volume=0.6)
                exit_with = _activate(idx)
                if exit_with is not None:
                    return exit_with

            blink_timer += 1

            # Frozen game frame + dark overlay
            self.screen.blit(background, (0, 0))
            overlay = pygame.Surface((w, h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 190))
            self.screen.blit(overlay, (0, 0))

            # Title
            self._draw_centered(
                "- CHEATS -", font_title,
                (255, 255, 0), cy - max(36, _h * 100 // 1080)
            )

            # Blue separator
            sep_x1, sep_x2 = w // 4, 3 * w // 4
            _sep_off2 = max(20, _h * 52 // 1080)
            pygame.draw.line(
                self.screen, (33, 33, 255),
                (sep_x1, cy - _sep_off2), (sep_x2, cy - _sep_off2), 2,
            )

            # Menu items
            for i, label in enumerate(display_items):
                if i == nav.selected:
                    show_arrow = (blink_timer // 15) % 2 == 0
                    prefix = "> " if show_arrow else "  "
                    item_color: tuple[int, int, int] = (255, 255, 0)
                else:
                    prefix = "  "
                    item_color = (200, 200, 200)
                self._draw_centered(
                    f"{prefix}{label}", font_item, item_color,
                    cy - max(14, _h * 36 // 1080) + i * _item_gap,
                )

            # Hint
            self._draw_centered(
                "ESC  -  BACK",
                font_hint, (100, 100, 100), h - max(14, _h * 36 // 1080),
            )

            pygame.display.flip()
            clock.tick(30)
