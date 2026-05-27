from __future__ import annotations

import os
import random
from typing import TYPE_CHECKING, Callable, List, Tuple

import pygame

from core.sounds import get_sounds
from display._maze_utils import _ROOT

_TYPO_PATH = os.path.join(_ROOT, "assets", "Typo", "ByteBounce.ttf")

if TYPE_CHECKING:
    from core.monitor import Monitor
    from core.scores import ScoreManager


class ScreensMixin:
    """
    Handles all full-screen UI loops: menu, highscores, instructions, end.
    """

    if TYPE_CHECKING:
        screen: pygame.Surface
        sprites: dict[str, pygame.Surface | list[pygame.Surface | None] | None]
        monitor: Monitor
        score_manager: ScoreManager
        _draw_centered: Callable[..., None]

    def _run_menu(self) -> str:
        """
        Main menu. Returns 'play', 'highscores', 'instructions', 'quit'.
        """
        _w, _h = self.screen.get_size()
        font_item = pygame.font.Font(_TYPO_PATH, max(40, _h * 72 // 1080))

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
        selected = 0
        clock = pygame.time.Clock()

        anim_x = -250

        while True:
            w, h = self.screen.get_size()
            mouse = pygame.mouse.get_pos()

            # Pre-compute clickable rects for menu items (stable hitboxes).
            item_rects: list[pygame.Rect] = []
            for i, label in enumerate(items):
                lbl_surf = font_item.render(label, True, (200, 200, 200))
                y_i = h // 2 - 80 + i * _item_gap
                r = lbl_surf.get_rect(centerx=w // 2, y=y_i)
                item_rects.append(r.inflate(180, 24))

            # Mouse-hover selects the item under the cursor.
            for i, r in enumerate(item_rects):
                if r.collidepoint(mouse):
                    selected = i
                    break

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        selected = (selected - 1) % len(items)
                    elif event.key == pygame.K_DOWN:
                        selected = (selected + 1) % len(items)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        get_sounds().play("button", volume=0.6)
                        return actions[selected]
                if (event.type == pygame.MOUSEBUTTONDOWN
                        and event.button == 1):
                    for i, r in enumerate(item_rects):
                        if r.collidepoint(event.pos):
                            get_sounds().play("button", volume=0.6)
                            return actions[i]

            if _bg_raw is not None:
                _bg = pygame.transform.smoothscale(_bg_raw, (w, h))
                self.screen.blit(_bg, (0, 0))
            else:
                self.screen.fill((0, 0, 0))

            # --- Animation at the bottom ---
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
            # -------------------------------

            # --- Logo ---
            if _logo_raw is not None:
                _lw = int(w * LOGO_WIDTH_RATIO)
                _lh = int(_logo_raw.get_height() * _lw / _logo_raw.get_width())
                _logo = pygame.transform.smoothscale(_logo_raw, (_lw, _lh))
                self.screen.blit(_logo, (_logo.get_rect(
                    centerx=int(w * LOGO_CENTER_X_RATIO),
                    centery=LOGO_CENTER_Y,
                )))
            # ---------------

            for i, label in enumerate(items):
                color = (255, 255, 0) if i == selected else (200, 200, 200)
                prefix = "> " if i == selected else "  "
                self._draw_centered(
                    f"{prefix}{label}", font_item, color,
                    h // 2 - 80 + i * _item_gap,
                )
            pygame.display.flip()
            clock.tick(30)

    def _run_highscores(self) -> None:
        """Show top-10 leaderboard. ENTER or ESC to go back."""
        _w, _h = self.screen.get_size()
        font_title = pygame.font.Font(_TYPO_PATH, max(14, _h * 44 // 1080))
        font_row = pygame.font.Font(_TYPO_PATH, max(10, _h * 26 // 1080))
        font_hint = pygame.font.Font(_TYPO_PATH, max(10, _h * 22 // 1080))
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
        """Show controls and rules. ENTER or ESC to go back."""
        _w, _h = self.screen.get_size()
        font_title = pygame.font.Font(_TYPO_PATH, max(14, _h * 44 // 1080))
        font_body = pygame.font.Font(_TYPO_PATH, max(10, _h * 24 // 1080))
        _title_y = max(10, _h * 30 // 1080)
        _lines_start = max(50, _h * 110 // 1080)
        _line_gap = max(16, _h * 38 // 1080)
        clock = pygame.time.Clock()
        # Each entry: (text, colour)
        lines: List[Tuple[str, Tuple[int, int, int]]] = [
            ("CONTROLS", (255, 255, 0)),
            ("Arrow keys / WASD  -  Move", (200, 200, 200)),
            ("ESC / P  -  Pause menu", (200, 200, 200)),
            ("", (0, 0, 0)),
            ("RULES", (255, 255, 0)),
            ("Eat all pac-gums to win.", (200, 200, 200)),
            ("Ghosts kill you on touch.", (200, 200, 200)),
            ("Super pac-gum makes ghosts edible.", (200, 200, 200)),
            ("3 lives total.", (200, 200, 200)),
            ("", (0, 0, 0)),
            ("ENTER or ESC  -  back", (120, 120, 120)),
        ]

        # Index of the "back" hint in *lines* (last entry) so we can build
        # a hit rect over it.
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

        # Brief black flash to make the jumpscare hit harder.
        self.screen.fill((0, 0, 0))
        pygame.display.flip()
        pygame.event.pump()
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

            # Pulsing zoom (1.05x .. 1.20x) and violent shake.
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

            # Red strobe overlay every other frame for the FNAF feel.
            if (elapsed // 80) % 2 == 0:
                overlay = pygame.Surface((w, h), pygame.SRCALPHA)
                overlay.fill((180, 0, 0, 60))
                self.screen.blit(overlay, (0, 0))

            pygame.display.flip()
            clock.tick(60)

        # Fade to black before handing control to the end screen.
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

    def _run_end_screen(self, result: str, final_score: int) -> None:
        """
		Game-over or victory: show score, ask name, save it.
		"""
        _w, _h = self.screen.get_size()
        font_title = pygame.font.Font(_TYPO_PATH, max(16, _h * 52 // 1080))
        font_score = pygame.font.Font(_TYPO_PATH, max(12, _h * 32 // 1080))
        font_label = pygame.font.Font(_TYPO_PATH, max(10, _h * 26 // 1080))
        font_input = pygame.font.Font(_TYPO_PATH, max(14, _h * 38 // 1080))
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
        """Overlay pause menu. Returns 'resume' or 'quit'."""
        _w, _h = self.screen.get_size()
        font_title = pygame.font.Font(_TYPO_PATH, max(14, _h * 46 // 1080))
        font_item = pygame.font.Font(_TYPO_PATH, max(10, _h * 28 // 1080))
        font_hint = pygame.font.Font(_TYPO_PATH, max(8, _h * 16 // 1080))
        _item_gap = max(20, _h * 44 // 1080)
        items = ["RESUME", "EXIT TO MAIN MENU"]
        actions = ["resume", "quit"]
        selected = 0
        clock = pygame.time.Clock()
        blink_timer = 0

        # Capture the current game frame to use as background
        background = self.screen.copy()

        while True:
            w, h = self.screen.get_size()
            cy = h // 2
            mouse = pygame.mouse.get_pos()

            # Build clickable rects for each pause-menu item.
            item_rects: list[pygame.Rect] = []
            for i, label in enumerate(items):
                lbl_surf = font_item.render(label, True, (200, 200, 200))
                y_i = cy - max(8, _h * 16 // 1080) + i * _item_gap
                r = lbl_surf.get_rect(centerx=w // 2, y=y_i)
                item_rects.append(r.inflate(180, 24))

            for i, r in enumerate(item_rects):
                if r.collidepoint(mouse):
                    if selected != i:
                        blink_timer = 0
                    selected = i
                    break

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_p):
                        get_sounds().play("button", volume=0.6)
                        return "resume"
                    if event.key == pygame.K_UP:
                        selected = (selected - 1) % len(items)
                        blink_timer = 0
                    elif event.key == pygame.K_DOWN:
                        selected = (selected + 1) % len(items)
                        blink_timer = 0
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        get_sounds().play("button", volume=0.6)
                        return actions[selected]
                if (event.type == pygame.MOUSEBUTTONDOWN
                        and event.button == 1):
                    for i, r in enumerate(item_rects):
                        if r.collidepoint(event.pos):
                            get_sounds().play("button", volume=0.6)
                            return actions[i]

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

            # Blue separator (matches maze wall colour)
            sep_x1, sep_x2 = w // 4, 3 * w // 4
            _sep_off = max(12, _h * 32 // 1080)
            pygame.draw.line(
                self.screen, (33, 33, 255),
                (sep_x1, cy - _sep_off), (sep_x2, cy - _sep_off), 2,
            )

            # Menu items
            for i, label in enumerate(items):
                if i == selected:
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
        _w, _h = self.screen.get_size()
        font_title = pygame.font.Font(_TYPO_PATH, max(14, _h * 46 // 1080))
        font_item = pygame.font.Font(_TYPO_PATH, max(10, _h * 26 // 1080))
        font_hint = pygame.font.Font(_TYPO_PATH, max(8, _h * 16 // 1080))
        _item_gap = max(18, _h * 40 // 1080)
        selected = 0
        clock = pygame.time.Clock()
        blink_timer = 0

        background = self.screen.copy()

        def _activate(idx: int) -> str | None:
            """Apply the selected cheat. Returns 'resume'/'next_level' if
            the menu should exit, else None."""
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
            mouse = pygame.mouse.get_pos()

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

            for i, r in enumerate(item_rects):
                if r.collidepoint(mouse):
                    if selected != i:
                        blink_timer = 0
                    selected = i
                    break

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "resume"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        get_sounds().play("button", volume=0.6)
                        return "resume"
                    if event.key == pygame.K_UP:
                        selected = (selected - 1) % 5
                        blink_timer = 0
                    elif event.key == pygame.K_DOWN:
                        selected = (selected + 1) % 5
                        blink_timer = 0
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        get_sounds().play("button", volume=0.6)
                        exit_with = _activate(selected)
                        if exit_with is not None:
                            return exit_with
                if (event.type == pygame.MOUSEBUTTONDOWN
                        and event.button == 1):
                    for i, r in enumerate(item_rects):
                        if r.collidepoint(event.pos):
                            selected = i
                            get_sounds().play("button", volume=0.6)
                            exit_with = _activate(i)
                            if exit_with is not None:
                                return exit_with
                            break

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
                if i == selected:
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
