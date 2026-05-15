from __future__ import annotations

from typing import List, Tuple

import pygame


class ScreensMixin:
    """Handles all full-screen UI loops: menu, highscores, instructions, end.
    """

    def _run_menu(self) -> str:
        """Main menu. Returns 'play', 'highscores', 'instructions', 'quit'."""
        font_title = pygame.font.SysFont("Arial", 56, bold=True)
        font_item = pygame.font.SysFont("Arial", 34)
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
                    f"{prefix}{label}", font_item, color, h // 2 + i * 52,
                )
            pygame.display.flip()
            clock.tick(30)

    def _run_highscores(self) -> None:
        """Show top-10 leaderboard. ENTER or ESC to go back."""
        font_title = pygame.font.SysFont("Arial", 44, bold=True)
        font_row = pygame.font.SysFont("Courier New", 26)
        font_hint = pygame.font.SysFont("Arial", 22)
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
            self._draw_centered("HIGH SCORES", font_title, (255, 255, 0), 30)
            scores = self.score_manager.top_scores()
            if not scores:
                self._draw_centered(
                    "No scores yet!", font_row, (180, 180, 180), h // 2,
                )
            else:
                for i, (name, score) in enumerate(scores):
                    line = f"{i + 1:2}.  {name:<10}  {score:>8}"
                    self._draw_centered(
                        line, font_row, (255, 255, 255), 100 + i * 36,
                    )
            self._draw_centered(
                "ENTER or ESC  -  back", font_hint, (120, 120, 120), h - 50,
            )
            pygame.display.flip()
            clock.tick(30)

    def _run_instructions(self) -> None:
        """Show controls and rules. ENTER or ESC to go back."""
        font_title = pygame.font.SysFont("Arial", 44, bold=True)
        font_body = pygame.font.SysFont("Arial", 24)
        clock = pygame.time.Clock()
        # Each entry: (text, colour)
        lines: List[Tuple[str, Tuple[int, int, int]]] = [
            ("CONTROLS", (255, 255, 0)),
            ("Arrow keys / WASD  -  Move", (200, 200, 200)),
            ("ESC  -  Back to menu", (200, 200, 200)),
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
                "INSTRUCTIONS", font_title, (255, 255, 0), 30
            )
            for i, (text, color) in enumerate(lines):
                self._draw_centered(text, font_body, color, 110 + i * 38)
            pygame.display.flip()
            clock.tick(30)

    def _run_end_screen(self, result: str, final_score: int) -> None:
        """Game-over or victory: show score, ask name, save it."""
        font_title = pygame.font.SysFont("Arial", 52, bold=True)
        font_score = pygame.font.SysFont("Arial", 32)
        font_label = pygame.font.SysFont("Arial", 26)
        font_input = pygame.font.SysFont("Courier New", 38, bold=True)
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
                "Enter your name:", font_label, (180, 180, 180), h // 2 - 30,
            )
            self._draw_centered(
                name + "_", font_input, (255, 255, 0), h // 2 + 20,
            )
            self._draw_centered(
                "ENTER to save  |  ESC to skip",
                font_label, (100, 100, 100), h - 60,
            )
            pygame.display.flip()
            clock.tick(30)
