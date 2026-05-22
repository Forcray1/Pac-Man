import os
import pygame
import sys


class Redirect:
    def main_menu(self):
        pygame.init()

        # Display
        info = pygame.display.Info()
        sw: int = info.current_w
        sh: int = info.current_h
        screen = pygame.display.set_mode((sw, sh), pygame.FULLSCREEN)
        pygame.display.set_caption("Pac-Man")
        clock = pygame.time.Clock()
        FPS = 30

        # Fonts
        font_hint = pygame.font.SysFont(
            "Courier New", max(10, sh * 18 // 1080)
        )

        # Point-in-polygon hit test (ray casting)
        def _in_poly(pt, poly):
            x, y = pt
            inside = False
            j = len(poly) - 1
            for i, (xi, yi) in enumerate(poly):
                xj, yj = poly[j]
                if (yi > y) != (yj > y):
                    if x < (xj - xi) * (y - yi) / (yj - yi) + xi:
                        inside = not inside
                j = i
            return inside

        # Polygons were measured at 3840×2160.
        # _s scales any point to the actual screen resolution.
        def _s(x, y):
            return (x * sw // 3840, y * sh // 2160)

        # Arcade cabinet → Play
        poly_play = [
            _s(1817,  144),
            _s(2223,  144),
            _s(2223, 1210),
            _s(1817, 1210),
        ]
        # Retro computer → Settings
        poly_config = [
            _s(489, 1018),
            _s(1252,  912),
            _s(1290, 1379),
            _s(573, 1553),
        ]
        # Fan base → Fan
        poly_fan = [
            _s(3186, 1598),
            _s(3413, 1672),
            _s(3326, 1843),
            _s(3005, 1749),
        ]
        # Quit button — small round, top-left
        # edit quit_margin / quit_r to reposition
        quit_margin = 14   # distance from screen edges
        quit_r = 22        # radius in pixels
        btn_quit = pygame.Rect(
            quit_margin, quit_margin, quit_r * 2, quit_r * 2
        )

        # (polygon, label, callable, launch-animation path or None)
        buttons = [
            (poly_play,   "PLAY",     self.to_game,     None),
            (poly_config, "SETTINGS", self.to_computer, None),
            (poly_fan,    "FAN",      self.on_fan,       None),
        ]

        tick = 0  # frame counter — available for custom animations

        # Animation frames
        _anim_dir = os.path.join(
            os.path.dirname(__file__),
            "..", "animation", "BaseAnimation",
        )
        anim_frames = [
            pygame.transform.scale(
                pygame.image.load(
                    os.path.join(_anim_dir, f"{i:04d}.webp")
                ).convert(),
                (sw, sh),
            )
            for i in range(1, 6)
        ]
        ANIM_FPS = 30          # frames per second for the animation
        anim_frame_idx = 0
        anim_timer = 0         # ms accumulator

        # Main loop
        while True:
            mouse = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        return
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if btn_quit.collidepoint(mouse):
                        pygame.quit()
                        return
                    for poly, _label, action, launch_anim in buttons:
                        if _in_poly(mouse, poly):
                            self.launch_animation(launch_anim)
                            action()
                            return

            dt = clock.get_time()   # ms since last tick

            # Draw background
            anim_timer += dt
            if anim_timer >= 1000 // ANIM_FPS:
                anim_timer = 0
                anim_frame_idx = (anim_frame_idx + 1) % len(anim_frames)
            screen.blit(anim_frames[anim_frame_idx], (0, 0))

            # Mouse position debug (top-right)
            pos_surf = font_hint.render(
                f"{mouse[0]}, {mouse[1]}", True, (255, 255, 255)
            )
            screen.blit(pos_surf, (sw - pos_surf.get_width() - 8, 8))

            # Draw quit button (translucent grey circle, top-left)
            quit_surf = pygame.Surface(
                (quit_r * 2, quit_r * 2), pygame.SRCALPHA
            )
            quit_alpha = 210 if btn_quit.collidepoint(mouse) else 130
            pygame.draw.circle(
                quit_surf,
                (180, 180, 180, quit_alpha),
                (quit_r, quit_r),
                quit_r,
            )
            x_lbl = font_hint.render("X", True, (40, 40, 40))
            quit_surf.blit(
                x_lbl,
                (quit_r - x_lbl.get_width() // 2,
                 quit_r - x_lbl.get_height() // 2),
            )
            screen.blit(quit_surf, btn_quit.topleft)

            # Draw buttons
            for poly, label, _, __ in buttons:
                hovered = _in_poly(mouse, poly)
                pygame.draw.polygon(
                    screen,
                    (255, 255, 255) if hovered else (180, 180, 180),
                    poly,
                    2,
                )

            pygame.display.flip()
            tick += 1
            clock.tick(FPS)

    def _play_animation(self, screen, clock, path, fps=12):
        """
        Play every frame in `path` once at `fps`, then return.
        Pass None or a non-existent path to skip silently.
        """
        if not path or not os.path.isdir(path):
            return
        files = sorted(
            f for f in os.listdir(path)
            if f.lower().endswith((".webp"))
        )
        if not files:
            sys.stderr.write(f"Animation path not found ({path})")
            return
        sw, sh = screen.get_size()
        frames = [
            pygame.transform.scale(
                pygame.image.load(
                    os.path.join(path, f)
                ).convert(),
                (sw, sh),
            )
            for f in files
        ]
        for frame in frames:
            screen.blit(frame, (0, 0))
            pygame.display.flip()
            pygame.event.pump()
            clock.tick(fps)

    def to_game(self):
        pass

    def to_computer(self):
        pass

    def off_fan(self):
        pass

    def on_fan(self):
        pass

    def launch_animation(self, path, fps=12):
        """
        Play every frame in `path` once at `fps` on the current display,
        then return.  Call after pygame.init() and display.set_mode().
        """
        screen = pygame.display.get_surface()
        if screen is None:
            return
        clock = pygame.time.Clock()
        self._play_animation(screen, clock, path, fps)


if __name__ == "__main__":
    redirect = Redirect()
    redirect.main_menu()
