import os

import pygame

from display._maze_utils import _ROOT

_TYPO_PATH = os.path.join(_ROOT, "assets", "Typo", "ByteBounce.ttf")


class Helper:
    """
    Helper for gamestyle that slides in from the top-right
    corner. One instance per surface; replaying show() restarts it.
    """

    DURATION_IN = 350    # ms slide-in
    DURATION_HOLD = 2600 # ms hold
    DURATION_OUT = 450   # ms slide-out
    DEFAULT_DELAY = 1000 # ms before the helper starts sliding in

    def __init__(self, screen_w: int, screen_h: int) -> None:
        self.sw = screen_w
        self.sh = screen_h
        self.font = pygame.font.Font(
            _TYPO_PATH, max(14, screen_h * 26 // 1080)
        )
        self.text = ""
        self.elapsed = 0
        self.delay_remaining = 0
        self.active = False
        self._last_tick = 0

    def show(self, text: str, delay_ms: int | None = None) -> None:
        self.text = text
        self.elapsed = 0
        self.delay_remaining = (
            self.DEFAULT_DELAY if delay_ms is None else max(0, delay_ms)
        )
        self.active = True
        self._last_tick = pygame.time.get_ticks()

    def update(self) -> None:
        if not self.active:
            return
        now = pygame.time.get_ticks()
        dt = now - self._last_tick
        self._last_tick = now
        if self.delay_remaining > 0:
            self.delay_remaining -= dt
            return
        self.elapsed += dt
        total = self.DURATION_IN + self.DURATION_HOLD + self.DURATION_OUT
        if self.elapsed >= total:
            self.active = False

    def draw(self, screen: pygame.Surface) -> None:
        if not self.active or self.delay_remaining > 0:
            return
        text_surf = self.font.render(self.text, True, (245, 245, 245))
        pad_x = max(8, self.sh * 10 // 1080)
        pad_y = max(4, self.sh * 6 // 1080)
        helper_w = text_surf.get_width() + pad_x * 2
        helper_h = text_surf.get_height() + pad_y * 2

        if self.elapsed < self.DURATION_IN:
            t = self.elapsed / self.DURATION_IN
            t = 1 - (1 - t) ** 3   # ease-out cubic
            offset = int((1 - t) * (helper_w + 20))
        elif self.elapsed > self.DURATION_IN + self.DURATION_HOLD:
            t = (self.elapsed - self.DURATION_IN - self.DURATION_HOLD) \
                / self.DURATION_OUT
            t = t ** 3              # ease-in cubic
            offset = int(t * (helper_w + 20))
        else:
            offset = 0

        helper_surf = pygame.Surface((helper_w, helper_h), pygame.SRCALPHA)
        bg_rect = helper_surf.get_rect()
        pygame.draw.rect(
            helper_surf, (18, 18, 28, 230), bg_rect, border_radius=5,
        )
        pygame.draw.rect(
            helper_surf, (210, 170, 60), bg_rect, width=2, border_radius=5,
        )
        helper_surf.blit(text_surf, (pad_x, pad_y))

        margin = max(10, self.sh * 14 // 1080)
        screen.blit(
            helper_surf, (self.sw - helper_w - margin + offset, margin),
        )


_singleton: Helper | None = None


def get_helper(screen: pygame.Surface) -> Helper:
    """
    Return the process-wide Helper singleton, sized to `screen`. Recreated
    if the screen size has changed (between fullscreen sessions as exemple).
    """
    global _singleton
    sw, sh = screen.get_size()
    if _singleton is None or (_singleton.sw, _singleton.sh) != (sw, sh):
        _singleton = Helper(sw, sh)
    return _singleton
