from __future__ import annotations

import pygame


class MenuNav:
    """
    Reusable keyboard + mouse navigation for a vertical list menu.
    """

    def __init__(
        self,
        count: int,
        escape_keys: tuple[int, ...] = (pygame.K_ESCAPE,),
    ) -> None:
        self.count = count
        self.escape_keys = escape_keys
        self.selected = 0
        self.changed = False
        self._last_mouse = pygame.mouse.get_pos()

    def _select(self, idx: int) -> None:
        if idx != self.selected:
            self.selected = idx
            self.changed = True

    def handle(self, item_rects: list[pygame.Rect]) -> tuple[str, int]:
        """
        Process one frame of input given the current item hitboxes.
        """
        self.changed = False

        # Hover-select, but only when the mouse actually moved this frame.
        mouse = pygame.mouse.get_pos()
        if mouse != self._last_mouse:
            self._last_mouse = mouse
            for i, r in enumerate(item_rects):
                if r.collidepoint(mouse):
                    self._select(i)
                    break

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return ("quit", self.selected)
            if event.type == pygame.KEYDOWN:
                if event.key in self.escape_keys:
                    return ("escape", self.selected)
                if event.key == pygame.K_UP:
                    self._select((self.selected - 1) % self.count)
                elif event.key == pygame.K_DOWN:
                    self._select((self.selected + 1) % self.count)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return ("confirm", self.selected)
            if (event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1):
                for i, r in enumerate(item_rects):
                    if r.collidepoint(event.pos):
                        self._select(i)
                        return ("confirm", i)

        return ("none", self.selected)
