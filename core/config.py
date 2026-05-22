from typing import Any

import pygame


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

        keys = [k for k in config.keys() if k != "seed"]
        selected = 0
        blink = 0
        clock = pygame.time.Clock()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return config
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return config
                    elif event.key == pygame.K_UP:
                        selected = (selected - 1) % len(keys)
                        blink = 0
                    elif event.key == pygame.K_DOWN:
                        selected = (selected + 1) % len(keys)
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

            blink += 1
            self._render(config, keys, selected, blink)
            clock.tick(30)

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

    def _run_bool_menu(
        self, key: str, current_value: Any
    ) -> str | None:
        """
        Overlay a True / False toggle.
        Left / Right arrows switch option, Enter confirm, ESC cancel.
        Returns "True" or "False" as a string, or None on ESC.
        """
        w, h = self.screen.get_size()
        clock = pygame.time.Clock()
        font_lbl = pygame.font.SysFont(
            "Courier New", max(10, h * 24 // 1080), bold=True
        )
        font_opt = pygame.font.SysFont(
            "Courier New", max(12, h * 36 // 1080), bold=True
        )
        font_hnt = pygame.font.SysFont("Courier New", max(8, h * 14 // 1080))

        background = self.screen.copy()
        # Normalise current value to a bool
        if isinstance(current_value, str):
            chosen = current_value.strip().lower() == "true"
        else:
            chosen = bool(current_value)

        bw = min(w - 160, max(360, w * 480 // 1920))
        bh = max(140, h * 190 // 1080)
        bx = w // 2 - bw // 2
        by = h // 2 - bh // 2

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return None
                    elif event.key == pygame.K_RETURN:
                        return "True" if chosen else "False"
                    elif event.key in (
                        pygame.K_LEFT,
                        pygame.K_RIGHT,
                        pygame.K_SPACE,
                    ):
                        chosen = not chosen

            self.screen.blit(background, (0, 0))
            overlay = pygame.Surface((w, h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 175))
            self.screen.blit(overlay, (0, 0))

            box_rect = pygame.Rect(bx, by, bw, bh)
            pygame.draw.rect(
                self.screen, (0, 18, 0), box_rect
            )
            pygame.draw.rect(
                self.screen, _AMBER, box_rect, 2
            )
            for cx, cy in [
                (bx, by), (bx + bw, by),
                (bx, by + bh), (bx + bw, by + bh),
            ]:
                pygame.draw.rect(
                    self.screen, _GREEN,
                    pygame.Rect(cx - 3, cy - 3, 6, 6),
                )

            # Label
            lbl = font_lbl.render(
                f">> EDIT: {key.upper()}", True, _AMBER
            )
            self.screen.blit(
                lbl,
                (bx + bw // 2 - lbl.get_width() // 2, by + bh * 18 // 190),
            )

            pygame.draw.line(
                self.screen, _DIM,
                (bx + 12, by + bh * 55 // 190),
                (bx + bw - 12, by + bh * 55 // 190), 1,
            )

            # True / False options
            opt_y = by + bh * 80 // 190
            for i, label in enumerate(("True", "False")):
                is_active = (label == "True") == chosen
                fg = _YELLOW if is_active else _DIM
                prefix = "[ " if is_active else "  "
                suffix = " ]" if is_active else "  "
                surf = font_opt.render(
                    prefix + label + suffix, True, fg
                )
                slot_w = bw // 2
                ox = bx + slot_w * i
                self.screen.blit(
                    surf,
                    (ox + slot_w // 2 - surf.get_width() // 2,
                     opt_y),
                )

            hnt = font_hnt.render(
                "LEFT/RIGHT toggle      ENTER confirm"
                "      ESC cancel",
                True, _DIM,
            )
            self.screen.blit(
                hnt,
                (
                    bx + bw // 2 - hnt.get_width() // 2,
                    by + bh - bh * 28 // 190,
                ),
            )

            pygame.display.flip()
            clock.tick(30)

    def _run_int_menu(
        self, key: str, current_value: Any
    ) -> int | None:
        """
        Overlay a CRT-style stepper for integer fields.
        UP / DOWN arrows (or hold) increment / decrement the value.
        Reaching 0 and pressing DOWN wraps to the maximum.
        'difficulty' is capped at 5; all other fields at sys.maxsize.
        Returns the new int, or None on ESC.
        """
        import sys as _sys

        # Per-key maximum / minimum
        _CAPS: dict[str, int] = {"difficulty": 5}
        _MINS: dict[str, int] = {"width": 3,
                                 "height": 3,
                                 "difficulty": 1,
                                 "level": 1}
        INT_MAX = _CAPS.get(key, _sys.maxsize)
        INT_MIN = _MINS.get(key, 0)

        w, h = self.screen.get_size()
        clock = pygame.time.Clock()
        font_lbl = pygame.font.SysFont(
            "Courier New", max(10, h * 24 // 1080), bold=True
        )
        font_val = pygame.font.SysFont(
            "Courier New", max(14, h * 48 // 1080), bold=True
        )
        font_hnt = pygame.font.SysFont("Courier New", max(8, h * 14 // 1080))

        background = self.screen.copy()
        value = int(current_value)

        bw = min(w - 160, max(360, w * 480 // 1920))
        bh = max(160, h * 220 // 1080)
        bx = w // 2 - bw // 2
        by = h // 2 - bh // 2

        # hold-to-repeat state
        held_key = None
        hold_timer = 0   # frames since key was first pressed
        HOLD_DELAY = 20  # frames before repeat kicks in
        HOLD_REPEAT = 3  # frames between repeats while held

        def apply_delta(v: int, delta: int) -> int:
            result = v + delta
            if result < INT_MIN:
                return INT_MAX   # wrap downward
            if result > INT_MAX:
                return INT_MIN   # wrap upward
            return result

        while True:
            delta = 0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return None
                    elif event.key == pygame.K_RETURN:
                        return value
                    elif event.key == pygame.K_UP:
                        delta = 1
                        held_key = pygame.K_UP
                        hold_timer = 0
                    elif event.key == pygame.K_DOWN:
                        delta = -1
                        held_key = pygame.K_DOWN
                        hold_timer = 0
                if event.type == pygame.KEYUP:
                    if event.key == held_key:
                        held_key = None
                        hold_timer = 0

            # Hold-to-repeat logic
            if held_key is not None:
                hold_timer += 1
                if hold_timer >= HOLD_DELAY:
                    remainder = hold_timer - HOLD_DELAY
                    if remainder % HOLD_REPEAT == 0:
                        step = 10 if remainder >= 60 else 1
                        delta = (
                            step if held_key == pygame.K_UP
                            else -step
                        )

            if delta:
                value = apply_delta(value, delta)

            self.screen.blit(background, (0, 0))
            overlay = pygame.Surface((w, h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 175))
            self.screen.blit(overlay, (0, 0))

            box_rect = pygame.Rect(bx, by, bw, bh)
            pygame.draw.rect(
                self.screen, (0, 18, 0), box_rect
            )
            pygame.draw.rect(
                self.screen, _AMBER, box_rect, 2
            )
            for cx, cy in [
                (bx, by), (bx + bw, by),
                (bx, by + bh), (bx + bw, by + bh),
            ]:
                pygame.draw.rect(
                    self.screen, _GREEN,
                    pygame.Rect(cx - 3, cy - 3, 6, 6),
                )

            lbl = font_lbl.render(
                f">> EDIT: {key.upper()}", True, _AMBER
            )
            self.screen.blit(
                lbl,
                (bx + bw // 2 - lbl.get_width() // 2,
                 by + bh * 18 // 220),
            )

            pygame.draw.line(
                self.screen, _DIM,
                (bx + 12, by + bh * 55 // 220),
                (bx + bw - 12, by + bh * 55 // 220), 1,
            )

            # Up arrow indicator
            up = font_lbl.render("   ^   ", True, _DIM)
            self.screen.blit(
                up,
                (bx + bw // 2 - up.get_width() // 2,
                 by + bh * 62 // 220),
            )

            # Current value
            val_surf = font_val.render(
                str(value), True, _GREEN
            )
            self.screen.blit(
                val_surf,
                (bx + bw // 2 - val_surf.get_width() // 2,
                 by + bh * 90 // 220),
            )

            # Down arrow indicator
            dn = font_lbl.render("   v   ", True, _DIM)
            self.screen.blit(
                dn,
                (bx + bw // 2 - dn.get_width() // 2,
                 by + bh * 148 // 220),
            )

            # Cap label
            cap_txt = (
                f"max: {INT_MAX}"
                if INT_MAX < _sys.maxsize
                else f"min: {INT_MIN}"
            )
            cap_surf = font_hnt.render(
                cap_txt, True, _DIM
            )
            self.screen.blit(
                cap_surf,
                (bx + bw - cap_surf.get_width() - 12,
                 by + bh * 58 // 220),
            )

            hnt = font_hnt.render(
                "UP/DOWN change value      ENTER confirm"
                "      ESC cancel",
                True, _DIM,
            )
            self.screen.blit(
                hnt,
                (
                    bx + bw // 2 - hnt.get_width() // 2,
                    by + bh - bh * 28 // 220,
                ),
            )

            pygame.display.flip()
            clock.tick(30)

    def _run_edit_menu(
        self, key: str, current_value: Any
    ) -> Any | None:
        """
        Overlay a CRT-style input box.
        Returns the raw string entered, or None on ESC.
        """
        w, h = self.screen.get_size()
        clock = pygame.time.Clock()
        font_lbl = pygame.font.SysFont(
            "Courier New", max(10, h * 24 // 1080), bold=True
        )
        font_inp = pygame.font.SysFont(
            "Courier New", max(12, h * 30 // 1080), bold=True
        )
        font_hnt = pygame.font.SysFont("Courier New", max(8, h * 14 // 1080))

        background = self.screen.copy()
        text = str(current_value)
        blink = 0

        bw = min(w - 160, max(400, w * 580 // 1920))
        bh = max(140, h * 190 // 1080)
        bx = w // 2 - bw // 2
        by = h // 2 - bh // 2

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return None
                    elif event.key == pygame.K_RETURN:
                        return text
                    elif event.key == pygame.K_BACKSPACE:
                        text = text[:-1]
                    else:
                        ch = event.unicode
                        if ch and ch.isprintable():
                            text += ch

            blink += 1

            self.screen.blit(background, (0, 0))
            overlay = pygame.Surface((w, h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 175))
            self.screen.blit(overlay, (0, 0))

            box_rect = pygame.Rect(bx, by, bw, bh)
            pygame.draw.rect(self.screen, (0, 18, 0), box_rect)
            pygame.draw.rect(
                self.screen, _AMBER, box_rect, 2
            )

            for cx, cy in [
                (bx, by),
                (bx + bw, by),
                (bx, by + bh),
                (bx + bw, by + bh),
            ]:
                pygame.draw.rect(
                    self.screen, _GREEN,
                    pygame.Rect(cx - 3, cy - 3, 6, 6),
                )

            lbl = font_lbl.render(
                f">> EDIT: {key.upper()}", True, _AMBER
            )
            lbl_x = bx + bw // 2 - lbl.get_width() // 2
            self.screen.blit(lbl, (lbl_x, by + bh * 18 // 190))

            pygame.draw.line(
                self.screen, _DIM,
                (bx + 12, by + bh * 55 // 190),
                (bx + bw - 12, by + bh * 55 // 190),
                1,
            )

            cursor = "_" if (blink // 14) % 2 == 0 else " "
            inp = font_inp.render(
                text + cursor, True, _GREEN
            )
            inp_x = bx + bw // 2 - inp.get_width() // 2
            self.screen.blit(inp, (inp_x, by + bh * 75 // 190))

            hnt = font_hnt.render(
                "[ ENTER ] confirm      [ ESC ] cancel",
                True,
                _DIM,
            )
            hnt_x = bx + bw // 2 - hnt.get_width() // 2
            self.screen.blit(hnt, (hnt_x, by + bh - bh * 28 // 190))

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
        pygame.display.flip()

    def _crt_power_on(self) -> None:
        """
        CRT start-up animation:
        1. A bright stripe expands from the screen centre (phosphor
           warm-up).
        2. The content fades in from black.
        """
        w, h = self.screen.get_size()
        clock = pygame.time.Clock()
        cy = h // 2

        step = max(1, cy // 28)
        for half in range(0, cy + 1, step):
            self.screen.fill(_BG)
            stripe = pygame.Rect(
                0, cy - half, w, half * 2 or 2
            )
            pygame.draw.rect(self.screen, _DIM, stripe)
            pygame.draw.line(
                self.screen, _GREEN, (0, cy), (w, cy), 1
            )
            self.screen.blit(self._scanlines, (0, 0))
            pygame.display.flip()
            clock.tick(60)

        fade = pygame.Surface((w, h))
        fade.fill(_BG)
        t = self._font_title.render(
            "CONFIG EDITOR", True, _YELLOW
        )
        tx = w // 2 - t.get_width() // 2
        ty = h // 2 - t.get_height() // 2
        for alpha in range(255, -1, -12):
            self.screen.fill(_BG)
            self.screen.blit(t, (tx, ty))
            fade.set_alpha(alpha)
            self.screen.blit(fade, (0, 0))
            self.screen.blit(self._scanlines, (0, 0))
            pygame.display.flip()
            clock.tick(60)
