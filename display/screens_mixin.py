from __future__ import annotations

from typing import TYPE_CHECKING, Callable, List, Tuple

import pygame

if TYPE_CHECKING:
    from core.monitor import Monitor
    from core.scores import ScoreManager


class ScreensMixin:
    """Handles all full-screen UI loops: menu, highscores, instructions, end.
    """

    if TYPE_CHECKING:
        screen: pygame.Surface
        sprites: dict[str, pygame.Surface | list[pygame.Surface | None] | None]
        monitor: Monitor
        score_manager: ScoreManager
        _draw_centered: Callable[..., None]

    def _run_menu(self) -> str:
        """Main menu. Returns 'play', 'highscores', 'instructions', 'quit'."""
        _w, _h = self.screen.get_size()
        font_title = pygame.font.SysFont(
            "Arial", max(16, _h * 56 // 1080), bold=True)
        font_item = pygame.font.SysFont("Arial", max(12, _h * 34 // 1080))
        _item_gap = max(20, _h * 52 // 1080)
        items = [
            "Start Game", "View Highscores",
            "Instructions", "Exit",
        ]
        actions = ["play", "highscores", "instructions", "quit"]
        selected = 0
        clock = pygame.time.Clock()

        anim_x = -250

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        selected = (selected - 1) % len(items)
                    elif event.key == pygame.K_DOWN:
                        selected = (selected + 1) % len(items)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        return actions[selected]

            self.screen.fill((0, 0, 0))
            w, h = self.screen.get_size()

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

            self._draw_centered("PAC-MAN", font_title, (255, 255, 0), h // 5)
            for i, label in enumerate(items):
                color = (255, 255, 0) if i == selected else (200, 200, 200)
                prefix = "> " if i == selected else "  "
                self._draw_centered(
                    f"{prefix}{label}", font_item, color,
                    h // 2 + i * _item_gap,
                )
            pygame.display.flip()
            clock.tick(30)

    def _run_highscores(self) -> None:
        """Show top-10 leaderboard. ENTER or ESC to go back."""
        _w, _h = self.screen.get_size()
        font_title = pygame.font.SysFont(
            "Arial", max(14, _h * 44 // 1080), bold=True)
        font_row = pygame.font.SysFont("Courier New", max(10, _h * 26 // 1080))
        font_hint = pygame.font.SysFont("Arial", max(10, _h * 22 // 1080))
        _title_y = max(10, _h * 30 // 1080)
        _row_start = max(50, _h * 100 // 1080)
        _row_gap = max(14, _h * 36 // 1080)
        clock = pygame.time.Clock()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                        return

            self.screen.fill((0, 0, 0))
            _, h = self.screen.get_size()
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
            self._draw_centered(
                "ENTER or ESC  -  back",
                font_hint, (120, 120, 120), h - _h * 50 // 1080,
            )
            pygame.display.flip()
            clock.tick(30)

    def _run_instructions(self) -> None:
        """Show controls and rules. ENTER or ESC to go back."""
        _w, _h = self.screen.get_size()
        font_title = pygame.font.SysFont(
            "Arial", max(14, _h * 44 // 1080), bold=True)
        font_body = pygame.font.SysFont("Arial", max(10, _h * 24 // 1080))
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

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                        return

            self.screen.fill((0, 0, 0))
            self._draw_centered(
                "INSTRUCTIONS", font_title, (255, 255, 0), _title_y
            )
            for i, (text, color) in enumerate(lines):
                self._draw_centered(
                    text, font_body, color,
                    _lines_start + i * _line_gap)
            pygame.display.flip()
            clock.tick(30)

    def _run_end_screen(self, result: str, final_score: int) -> None:
        """Game-over or victory: show score, ask name, save it."""
        _w, _h = self.screen.get_size()
        font_title = pygame.font.SysFont(
            "Arial", max(16, _h * 52 // 1080), bold=True)
        font_score = pygame.font.SysFont("Arial", max(12, _h * 32 // 1080))
        font_label = pygame.font.SysFont("Arial", max(10, _h * 26 // 1080))
        font_input = pygame.font.SysFont(
            "Courier New", max(14, _h * 38 // 1080), bold=True)
        clock = pygame.time.Clock()

        title = "YOU WIN!" if result == "win" else "GAME OVER"
        t_color = (0, 255, 100) if result == "win" else (255, 50, 50)
        name = ""

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.score_manager.add(
                            name or "Anonymous", final_score
                        )
                        return
                    elif event.key == pygame.K_ESCAPE:
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

            self.screen.fill((0, 0, 0))
            _, h = self.screen.get_size()
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
            self._draw_centered(
                "ENTER to save  |  ESC to skip",
                font_label, (100, 100, 100), h - max(24, h * 60 // 1080),
            )
            pygame.display.flip()
            clock.tick(30)

    def _run_pause_menu(self) -> str:
        """Overlay pause menu. Returns 'resume' or 'quit'."""
        _w, _h = self.screen.get_size()
        font_title = pygame.font.SysFont(
            "Courier New", max(14, _h * 46 // 1080), bold=True)
        font_item = pygame.font.SysFont(
            "Courier New", max(10, _h * 28 // 1080), bold=True)
        font_hint = pygame.font.SysFont("Courier New", max(8, _h * 16 // 1080))
        _item_gap = max(20, _h * 44 // 1080)
        items = ["RESUME", "EXIT TO MAIN MENU"]
        actions = ["resume", "quit"]
        selected = 0
        clock = pygame.time.Clock()
        blink_timer = 0

        # Capture the current game frame to use as background
        background = self.screen.copy()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_p):
                        return "resume"
                    if event.key == pygame.K_UP:
                        selected = (selected - 1) % len(items)
                        blink_timer = 0
                    elif event.key == pygame.K_DOWN:
                        selected = (selected + 1) % len(items)
                        blink_timer = 0
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        return actions[selected]

            blink_timer += 1
            w, h = self.screen.get_size()
            cy = h // 2

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
        font_title = pygame.font.SysFont(
            "Courier New", max(14, _h * 46 // 1080), bold=True)
        font_item = pygame.font.SysFont(
            "Courier New", max(10, _h * 26 // 1080), bold=True)
        font_hint = pygame.font.SysFont("Courier New", max(8, _h * 16 // 1080))
        _item_gap = max(18, _h * 40 // 1080)
        selected = 0
        clock = pygame.time.Clock()
        blink_timer = 0

        background = self.screen.copy()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "resume"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "resume"
                    if event.key == pygame.K_UP:
                        selected = (selected - 1) % 4
                        blink_timer = 0
                    elif event.key == pygame.K_DOWN:
                        selected = (selected + 1) % 4
                        blink_timer = 0
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if selected == 0:
                            self.monitor.collision = (
                                not self.monitor.collision
                            )
                        elif selected == 1:
                            self.monitor.ghosts_frozen = (
                                not self.monitor.ghosts_frozen
                            )
                        elif selected == 2:
                            return "next_level"
                        elif selected == 3:
                            return "resume"

            blink_timer += 1
            collision_tag = "[OFF]" if self.monitor.collision else "[ON]"
            ghosts_tag = "[ON]" if self.monitor.ghosts_frozen else "[OFF]"
            display_items = [
                f"NO COLLISION  {collision_tag}",
                f"PAUSE GHOSTS  {ghosts_tag}",
                "NEXT LEVEL",
                "RESUME",
            ]

            w, h = self.screen.get_size()
            cy = h // 2

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
