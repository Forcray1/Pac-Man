import json
import os
import pygame
import sys
from typing import Any

from core.config import edited_config
from core.parser import parser
from display.pygame_viewer import PygameViewer


_anim_cache: dict[tuple[str, int, int], list[pygame.Surface]] = {}


class Redirect:
    def __init__(self, config: dict[str, Any], config_path: str) -> None:
        self.config = config
        self.config_path = config_path
        self._fan_state: str = "idle"   # idle | slowing | stopped | speeding
        self._fan_fps: float = 30.0

    def main_menu(self) -> None:
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
        def _in_poly(pt: tuple[int, int], poly: list[tuple[int, int]]) -> bool:
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
        def _s(x: int, y: int) -> tuple[int, int]:
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
        if not os.path.isdir(_anim_dir):
            print(
                f"ERROR: BaseAnimation directory not found: {_anim_dir}",
                file=sys.stderr,
            )
            anim_frames = []
        else:
            _anim_files = sorted(
                f for f in os.listdir(_anim_dir)
                if f.lower().endswith(".webp")
            )
            if not _anim_files:
                print(
                    f"ERROR: No .webp frames found in BaseAnimation directory:"
                    f" {_anim_dir}",
                    file=sys.stderr,
                )
            anim_frames = [
                pygame.transform.scale(
                    pygame.image.load(
                        os.path.join(_anim_dir, f)
                    ).convert(),
                    (sw, sh),
                )
                for f in _anim_files
            ]
        anim_frame_idx = 0
        anim_timer = 0         # ms accumulator

        # Pre-load transition animations into cache
        _to_game_dir = os.path.join(
            os.path.dirname(__file__), "..", "animation", "TransitionToArcade"
        )
        self._preload_animation(screen, _to_game_dir)
        _to_computer_dir = os.path.join(
            os.path.dirname(__file__), "..", "animation", "TransitionToDesktop"
        )
        self._preload_animation(screen, _to_computer_dir)

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
                            # Restore the main menu display after returning
                            screen = pygame.display.set_mode(
                                (sw, sh), pygame.FULLSCREEN
                            )
                            pygame.display.set_caption("Pac-Man")
                            pygame.event.clear()

            dt = clock.get_time()   # ms since last tick

            # Fan slow-down / restart effect
            if self._fan_state == "slowing":
                self._fan_fps *= 0.934
                if self._fan_fps < 0.5:
                    self._fan_fps = 0.0
                    self._fan_state = "stopped"
            elif self._fan_state == "speeding":
                self._fan_fps += (30.0 - self._fan_fps) * 0.066
                if self._fan_fps >= 29.5:
                    self._fan_fps = 30.0
                    self._fan_state = "idle"

            # Draw background
            if anim_frames:
                if self._fan_fps > 0:
                    anim_timer += dt
                    if anim_timer >= 1000 / self._fan_fps:
                        anim_timer = 0
                        anim_frame_idx = (
                            (anim_frame_idx + 1) % len(anim_frames)
                        )
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

    def _preload_animation(self, screen: pygame.Surface, path: str) -> None:
        """Load and cache frames for path without displaying them."""
        if not path or not os.path.isdir(path):
            return
        sw, sh = screen.get_size()
        key = (os.path.abspath(path), sw, sh)
        if key in _anim_cache:
            return
        files = sorted(
            f for f in os.listdir(path)
            if f.lower().endswith(".webp")
        )
        if not files:
            return
        _anim_cache[key] = [
            pygame.transform.scale(
                pygame.image.load(os.path.join(path, f)).convert(),
                (sw, sh),
            )
            for f in files
        ]

    def _play_animation(
        self,
        screen: pygame.Surface,
        clock: pygame.time.Clock,
        path: str,
        fps: int = 12,
        reverse: bool = False,
    ) -> None:
        """
        Play every frame in `path` once at `fps`, then return.
        Pass None to skip silently. Set reverse=True to play backward.
        """
        if not path:
            return
        if not os.path.isdir(path):
            print(
                f"ERROR: Animation directory not found: {path}",
                file=sys.stderr,
            )
            return
        sw, sh = screen.get_size()
        key = (os.path.abspath(path), sw, sh)
        if key not in _anim_cache:
            files = sorted(
                f for f in os.listdir(path)
                if f.lower().endswith(".webp")
            )
            if not files:
                print(
                    f"ERROR: No .webp frames found in animation directory:"
                    f" {path}",
                    file=sys.stderr,
                )
                return
            _anim_cache[key] = [
                pygame.transform.scale(
                    pygame.image.load(
                        os.path.join(path, f)
                    ).convert(),
                    (sw, sh),
                )
                for f in files
            ]
        frames = _anim_cache[key]
        if reverse:
            frames = frames[::-1]
        for frame in frames:
            screen.blit(frame, (0, 0))
            pygame.display.flip()
            pygame.event.pump()
            clock.tick(fps)

    def to_game(self) -> None:
        anim_path = os.path.join(
            os.path.dirname(__file__), "..", "animation", "TransitionToArcade"
        )
        self.launch_animation(anim_path, 30)
        viewer = PygameViewer(self.config)
        viewer.display()
        self.launch_animation(anim_path, 30, reverse=True)

    def to_computer(self) -> None:
        anim_path = os.path.join(
            os.path.dirname(__file__), "..", "animation", "TransitionToDesktop"
        )
        self.launch_animation(anim_path, 30)
        with open(self.config_path, encoding="utf-8") as f:
            config = json.load(f)

        screen = pygame.display.get_surface()
        if screen is None:
            return
        pygame.display.set_caption("Config Editor")

        editor = edited_config(screen)
        updated = editor.draw_window(config)

        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(updated, f, indent="\t")
        parsed = parser(self.config_path)
        if parsed:
            self.config = parsed
        self.launch_animation(anim_path, 30, reverse=True)

    def on_fan(self) -> None:
        if self._fan_state in ("idle", "speeding"):
            self._fan_state = "slowing"
        else:  # slowing or stopped
            self._fan_state = "speeding"

    def launch_animation(
        self, path: str | None, fps: int = 12, reverse: bool = False
    ) -> None:
        """
        Play every frame in `path` once at `fps` on the current display,
        then return.  Call after pygame.init() and display.set_mode().
        """
        if path is None:
            return
        screen = pygame.display.get_surface()
        if screen is None:
            return
        clock = pygame.time.Clock()
        self._play_animation(screen, clock, path, fps, reverse)
