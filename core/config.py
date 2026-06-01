from typing import Any

import pygame

from core.sounds import get_sounds
from display.helper import get_helper


_BG = (0, 0, 0)          # pure black
_GREEN = (0, 255, 70)    # phosphor green
_DIM = (0, 130, 35)      # dim green (inactive / decorative)
_AMBER = (255, 176, 0)   # amber — selection highlight
_YELLOW = (255, 255, 0)  # Pac-Man yellow — title
_BORDER = (0, 210, 60)   # border lines


class edited_config:
    """
    Full-screen config editor
    """

    def __init__(self, screen: pygame.Surface) -> None:
        """
        Prepare fonts and the static scanline overlay used by the editor
        for the given screen.
        """
        self.screen = screen
        _h = screen.get_height()
        self._font_title = pygame.font.SysFont(
            "Courier New", max(14, _h * 42 // 1080), bold=True
        )
        self._font_label = pygame.font.SysFont(
            "Courier New", max(10, _h * 22 // 1080), bold=True
        )
        self._font_val = pygame.font.SysFont(
            "Courier New", max(10, _h * 22 // 1080))
        self._font_hint = pygame.font.SysFont(
            "Courier New", max(8, _h * 15 // 1080))

        # Pre-render a static scanline overlay used every frame
        w, h = screen.get_size()
        self._scanlines = pygame.Surface((w, h), pygame.SRCALPHA)
        for y in range(0, h, 2):
            pygame.draw.line(
                self._scanlines, (0, 0, 0, 55), (0, y), (w, y)
            )

    def draw_window(
        self, config: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Main config-editor loop.
        Plays the CRT power-on animation then lets the user navigate
        and edit every config key.
        Returns the (possibly modified) config.
        """
        self._crt_power_on()
        get_helper(self.screen).show("use arrow to select")

        keys = [k for k in config.keys() if k != "seed"]
        selected = 0
        blink = 0
        clock = pygame.time.Clock()
        select_channel: pygame.mixer.Channel | None = None

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key in (pygame.K_UP, pygame.K_DOWN):
                        if (select_channel is not None
                                and select_channel.get_busy()):
                            select_channel.stop()
                        select_channel = get_sounds().play(
                            "movement_select", volume=0.20,
                        )
                        step = -1 if event.key == pygame.K_UP else 1
                        selected = (selected + step) % len(keys)
                        blink = 0
                    elif event.key in (
                        pygame.K_RETURN, pygame.K_SPACE
                    ):
                        key = keys[selected]
                        new_val: int | str | None
                        if self._is_bool(config[key]):
                            new_val = self._run_bool_menu(
                                key, config[key]
                            )
                        elif self._is_int(config[key]):
                            new_val = self._run_int_menu(
                                key, config[key]
                            )
                        else:
                            new_val = self._run_edit_menu(
                                key, config[key]
                            )
                        if new_val is not None:
                            self.edit_config(
                                config, key, new_val
                            )

            if running:
                blink += 1
                self._render(config, keys, selected, blink)
                clock.tick(30)

        self._crt_power_off()
        return config

    def edit_config(
        self, config: dict[str, Any], key: str, value: Any
    ) -> None:
        """
        Write value back into config[key], preserving the original
        type.  Boolean strings stay as strings to match the JSON
        serialisation used elsewhere.
        """
        original = config.get(key)
        try:
            if (
                isinstance(original, str)
                and original.lower() in ("true", "false")
            ) or isinstance(original, bool):
                config[key] = str(value).strip().capitalize()
            elif isinstance(original, int):
                config[key] = int(value)
            elif isinstance(original, float):
                config[key] = float(value)
            else:
                config[key] = value
        except (ValueError, TypeError):
            pass  # Ignore malformed input — keep old value

    @staticmethod
    def _is_bool(value: Any) -> bool:
        """
        Return True if value represents a boolean field.
        """
        return isinstance(value, bool) or (
            isinstance(value, str)
            and value.lower() in ("true", "false")
        )

    @staticmethod
    def _is_int(value: Any) -> bool:
        """
        Return True if value is a plain integer (not a bool).
        """
        return isinstance(value, int) and not isinstance(
            value, bool
        )

    def _modal_dims(
        self, bw_ratio: int, min_bw: int, bh_ratio: int, min_bh: int
    ) -> tuple[int, int, int, int]:
        """
        Compute a centred modal-box rectangle (bx, by, bw, bh) sized
        proportionally to the current screen.
        """
        w, h = self.screen.get_size()
        bw = min(w - 160, max(min_bw, w * bw_ratio // 1920))
        bh = max(min_bh, h * bh_ratio // 1080)
        return (w - bw) // 2, (h - bh) // 2, bw, bh

    def _modal_fonts(
        self, lbl_px: int, big_px: int
    ) -> tuple[pygame.font.Font, pygame.font.Font, pygame.font.Font]:
        """
        Return (label, big, hint) fonts scaled to the screen height.
        """
        h = self.screen.get_height()
        return (
            pygame.font.SysFont(
                "Courier New", max(10, h * lbl_px // 1080), bold=True),
            pygame.font.SysFont(
                "Courier New", max(12, h * big_px // 1080), bold=True),
            pygame.font.SysFont(
                "Courier New", max(8, h * 14 // 1080)),
        )

    def _draw_modal_chrome(
        self,
        background: pygame.Surface,
        rect: tuple[int, int, int, int],
        key: str,
        hint: str,
        font_lbl: pygame.font.Font,
        font_hnt: pygame.font.Font,
        bh_ref: int = 190,
    ) -> None:
        """
        Render the shared modal frame: dimmed background, dark-green box,
        amber border, four corner markers, title (>> EDIT: KEY), a thin
        separator line below the title, and the bottom hint text.
        """
        bx, by, bw, bh = rect
        w, h = self.screen.get_size()

        self.screen.blit(background, (0, 0))
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 175))
        self.screen.blit(overlay, (0, 0))

        pygame.draw.rect(self.screen, (0, 18, 0), pygame.Rect(*rect))
        pygame.draw.rect(self.screen, _AMBER, pygame.Rect(*rect), 2)
        for cx, cy in (
            (bx, by), (bx + bw, by),
            (bx, by + bh), (bx + bw, by + bh),
        ):
            pygame.draw.rect(
                self.screen, _GREEN,
                pygame.Rect(cx - 3, cy - 3, 6, 6),
            )

        lbl = font_lbl.render(f">> EDIT: {key.upper()}", True, _AMBER)
        self.screen.blit(
            lbl, (bx + bw // 2 - lbl.get_width() // 2,
                  by + bh * 18 // bh_ref))

        sep_y = by + bh * 55 // bh_ref
        pygame.draw.line(
            self.screen, _DIM,
            (bx + 12, sep_y), (bx + bw - 12, sep_y), 1)

        hnt = font_hnt.render(hint, True, _DIM)
        self.screen.blit(
            hnt, (bx + bw // 2 - hnt.get_width() // 2,
                  by + bh - bh * 28 // bh_ref))

    def _run_bool_menu(
        self, key: str, current_value: Any
    ) -> str | None:
        """
        Overlay a True / False toggle.
        Left / Right arrows switch option, Enter confirm, ESC cancel.
        Returns "True" or "False" as a string, or None on ESC.
        """
        clock = pygame.time.Clock()
        font_lbl, font_opt, font_hnt = self._modal_fonts(24, 36)
        background = self.screen.copy()

        if isinstance(current_value, str):
            chosen = current_value.strip().lower() == "true"
        else:
            chosen = bool(current_value)

        rect = self._modal_dims(480, 360, 190, 140)
        bx, by, bw, bh = rect

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return None
                    if event.key == pygame.K_RETURN:
                        return "True" if chosen else "False"
                    if event.key in (
                        pygame.K_LEFT, pygame.K_RIGHT, pygame.K_SPACE,
                    ):
                        chosen = not chosen

            self._draw_modal_chrome(
                background, rect, key,
                "LEFT/RIGHT toggle      ENTER confirm      ESC cancel",
                font_lbl, font_hnt,
            )

            opt_y = by + bh * 80 // 190
            for i, label in enumerate(("True", "False")):
                is_active = (label == "True") == chosen
                fg = _YELLOW if is_active else _DIM
                wrapped = f"[ {label} ]" if is_active else f"  {label}  "
                surf = font_opt.render(wrapped, True, fg)
                slot_w = bw // 2
                ox = bx + slot_w * i + slot_w // 2 - surf.get_width() // 2
                self.screen.blit(surf, (ox, opt_y))

            pygame.display.flip()
            clock.tick(30)

    def _run_int_menu(
        self, key: str, current_value: Any
    ) -> int | None:
        """
        Overlay a CRT-style stepper for integer fields.
        UP / DOWN arrows (or hold) increment / decrement the value.
        Reaching INT_MIN and pressing DOWN wraps to INT_MAX, and
        vice versa. Returns the new int, or None on ESC.
        """
        import sys as _sys

        INT_MAX = {"difficulty": 5, "width": 50, "height": 50}.get(key, 999)
        INT_MIN = {
            "width": 3, "height": 3, "difficulty": 1,
            "level": 1, "level_max_time": 1,
        }.get(key, 0)

        clock = pygame.time.Clock()
        font_lbl, font_val, font_hnt = self._modal_fonts(24, 48)
        background = self.screen.copy()
        value = int(current_value)

        rect = self._modal_dims(480, 360, 220, 160)
        bx, by, bw, bh = rect

        held_key: int | None = None
        hold_timer = 0
        HOLD_DELAY = 20
        HOLD_REPEAT = 3

        def wrap(v: int) -> int:
            if v < INT_MIN:
                return INT_MAX
            if v > INT_MAX:
                return INT_MIN
            return v

        while True:
            delta = 0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return None
                    if event.key == pygame.K_RETURN:
                        return value
                    if event.key in (pygame.K_UP, pygame.K_DOWN):
                        delta = 1 if event.key == pygame.K_UP else -1
                        held_key = event.key
                        hold_timer = 0
                elif event.type == pygame.KEYUP and event.key == held_key:
                    held_key = None
                    hold_timer = 0

            if held_key is not None:
                hold_timer += 1
                remainder = hold_timer - HOLD_DELAY
                if remainder >= 0 and remainder % HOLD_REPEAT == 0:
                    step = 10 if remainder >= 60 else 1
                    delta = step if held_key == pygame.K_UP else -step

            if delta:
                value = wrap(value + delta)

            self._draw_modal_chrome(
                background, rect, key,
                "UP/DOWN change value      ENTER confirm      ESC cancel",
                font_lbl, font_hnt, bh_ref=220,
            )

            for txt, ratio, font, color in (
                ("   ^   ", 62, font_lbl, _DIM),
                (str(value), 90, font_val, _GREEN),
                ("   v   ", 148, font_lbl, _DIM),
            ):
                surf = font.render(txt, True, color)
                self.screen.blit(
                    surf,
                    (bx + bw // 2 - surf.get_width() // 2,
                     by + bh * ratio // 220))

            cap_txt = (
                f"max: {INT_MAX}" if INT_MAX < _sys.maxsize
                else f"min: {INT_MIN}"
            )
            cap_surf = font_hnt.render(cap_txt, True, _DIM)
            self.screen.blit(
                cap_surf,
                (bx + bw - cap_surf.get_width() - 12,
                 by + bh * 58 // 220))

            pygame.display.flip()
            clock.tick(30)

    def _run_edit_menu(
        self, key: str, current_value: Any
    ) -> Any | None:
        """
        Overlay a CRT-style input box.
        Returns the raw string entered, or None on ESC.
        """
        clock = pygame.time.Clock()
        font_lbl, font_inp, font_hnt = self._modal_fonts(24, 30)
        background = self.screen.copy()

        text = str(current_value)
        blink = 0

        rect = self._modal_dims(580, 400, 190, 140)
        bx, by, bw, bh = rect

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return None
                    if event.key == pygame.K_RETURN:
                        return text
                    if event.key == pygame.K_BACKSPACE:
                        text = text[:-1]
                    elif event.unicode and event.unicode.isprintable():
                        text += event.unicode

            blink += 1
            self._draw_modal_chrome(
                background, rect, key,
                "[ ENTER ] confirm      [ ESC ] cancel",
                font_lbl, font_hnt,
            )

            cursor = "_" if (blink // 14) % 2 == 0 else " "
            inp = font_inp.render(text + cursor, True, _GREEN)
            self.screen.blit(
                inp,
                (bx + bw // 2 - inp.get_width() // 2,
                 by + bh * 75 // 190))

            pygame.display.flip()
            clock.tick(30)

    def _render(
        self,
        config: dict[str, Any],
        keys: list[str],
        selected: int,
        blink: int,
    ) -> None:
        """
        Draw the full config-editor screen.
        """
        w, h = self.screen.get_size()
        self.screen.fill(_BG)

        margin = max(20, w * 44 // 1920)

        border_rect = pygame.Rect(
            margin, margin,
            w - 2 * margin, h - 2 * margin,
        )
        pygame.draw.rect(self.screen, _BORDER, border_rect, 1)

        for cx, cy in [
            (margin, margin),
            (w - margin, margin),
            (margin, h - margin),
            (w - margin, h - margin),
        ]:
            pygame.draw.rect(
                self.screen, _AMBER,
                pygame.Rect(cx - 4, cy - 4, 8, 8),
            )

        title_surf = self._font_title.render(
            "CONFIG EDITOR", True, _YELLOW
        )
        title_y = margin + 14
        title_x = w // 2 - title_surf.get_width() // 2
        self.screen.blit(title_surf, (title_x, title_y))

        sep_y = title_y + title_surf.get_height() + 6
        pygame.draw.line(
            self.screen, _BORDER,
            (margin + 18, sep_y),
            (w - margin - 18, sep_y),
            1,
        )

        col_key_x = margin + max(20, w * 50 // 1920)
        col_val_x = w // 2 + max(20, w * 50 // 1920)
        header_y = sep_y + max(6, h * 10 // 1080)

        hdr_k = self._font_hint.render(
            "PARAMETER", True, _DIM
        )
        hdr_v = self._font_hint.render("VALUE", True, _DIM)
        self.screen.blit(hdr_k, (col_key_x, header_y))
        self.screen.blit(hdr_v, (col_val_x, header_y))

        row_start = header_y + hdr_k.get_height() + 4
        _hint_h = self._font_hint.get_height() + 10
        _available = h - margin - _hint_h - row_start
        row_h = max(
            self._font_label.get_height() + 2,
            _available // max(1, len(keys)))

        for i, key in enumerate(keys):
            ry = row_start + i * row_h
            is_sel = i == selected
            fg = _AMBER if is_sel else _GREEN

            if is_sel:
                bar = pygame.Rect(
                    margin + 6, ry - 2,
                    w - 2 * margin - 12, row_h - 1,
                )
                pygame.draw.rect(
                    self.screen, (0, 38, 0), bar
                )
                if (blink // 10) % 2 == 0:
                    pygame.draw.rect(
                        self.screen, _AMBER, bar, 1
                    )
                arrow = self._font_label.render(
                    ">", True, _AMBER
                )
                self.screen.blit(arrow, (margin + 14, ry))

            k_surf = self._font_label.render(key, True, fg)
            v_surf = self._font_val.render(
                str(config[key]), True, fg
            )
            self.screen.blit(k_surf, (col_key_x, ry))
            self.screen.blit(v_surf, (col_val_x, ry))

        hints = (
            "UP/DOWN navigate"
            "   ENTER edit value"
            "   ESC back"
        )
        hnt_suf = self._font_hint.render(hints, True, _DIM)
        hint_x = w // 2 - hnt_suf.get_width() // 2
        hint_y = h - margin - hnt_suf.get_height() - 6
        self.screen.blit(hnt_suf, (hint_x, hint_y))

        self.screen.blit(self._scanlines, (0, 0))
        _helper = get_helper(self.screen)
        _helper.update()
        _helper.draw(self.screen)
        pygame.display.flip()

    def _crt_power_on(self) -> None:
        """
        Opening animation: a black rectangle grows from screen centre
        to full size on a white background, then config fades in.
        """
        w, h = self.screen.get_size()
        clock = pygame.time.Clock()
        get_sounds().play("computer_on", volume=0.8)

        steps = 28
        for i in range(1, steps + 1):
            t = i / steps
            ease = 1.0 - (1.0 - t) ** 2
            rw = max(2, int(w * ease))
            rh = max(2, int(h * ease))
            rx = (w - rw) // 2
            ry = (h - rh) // 2
            self.screen.fill((255, 255, 255))
            pygame.draw.rect(self.screen, _BG, pygame.Rect(rx, ry, rw, rh))
            self.screen.blit(self._scanlines, (0, 0))
            pygame.display.flip()
            clock.tick(60)

        fade = pygame.Surface((w, h))
        fade.fill(_BG)
        title_surf = self._font_title.render(
            "CONFIG EDITOR", True, _YELLOW
        )
        tx = w // 2 - title_surf.get_width() // 2
        ty = h // 2 - title_surf.get_height() // 2
        for alpha in range(255, -1, -12):
            self.screen.fill(_BG)
            self.screen.blit(title_surf, (tx, ty))
            fade.set_alpha(alpha)
            self.screen.blit(fade, (0, 0))
            self.screen.blit(self._scanlines, (0, 0))
            pygame.display.flip()
            clock.tick(60)

    def _crt_power_off(self) -> None:
        """
        Closing animation: config content shrinks into a rectangle
        contracting to screen centre, then white.
        """
        w, h = self.screen.get_size()
        clock = pygame.time.Clock()
        snapshot = self.screen.copy()
        get_sounds().play("computer_off", volume=0.8)

        steps = 28
        for i in range(steps, -1, -1):
            t = i / steps
            ease = 1.0 - (1.0 - t) ** 2
            rw = max(2, int(w * ease))
            rh = max(2, int(h * ease))
            rx = (w - rw) // 2
            ry = (h - rh) // 2
            self.screen.fill((255, 255, 255))
            if rw > 2 and rh > 2:
                self.screen.blit(
                    pygame.transform.scale(snapshot, (rw, rh)),
                    (rx, ry),
                )
            self.screen.blit(self._scanlines, (0, 0))
            pygame.display.flip()
            clock.tick(60)

        self.screen.fill((255, 255, 255))
        pygame.display.flip()
        clock.tick(7)
