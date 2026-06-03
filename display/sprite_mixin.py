from __future__ import annotations

import os
from typing import TYPE_CHECKING
import sys

import pygame

from display._maze_utils import _ROOT

# Layout of texts.png: a 128×224 sheet of 8×8 glyphs, 16 columns. Colour
# variants are stacked in blocks of rows; row 24 is the yellow block.
# _TEXT_CMAP maps a character to its (col, row) within one colour block.
_TEXT_TILE = 8
_TEXT_CMAP: dict[str, tuple[int, int]] = {
    'A': (0, 0), 'B': (1, 0), 'C': (2, 0), 'D': (3, 0),
    'E': (4, 0), 'F': (5, 0), 'G': (6, 0), 'H': (7, 0),
    'I': (8, 0), 'J': (9, 0), 'K': (10, 0), 'L': (11, 0),
    'M': (12, 0), 'N': (13, 0), 'O': (14, 0),
    'P': (0, 1), 'Q': (1, 1), 'R': (2, 1), 'S': (3, 1),
    'T': (4, 1), 'U': (5, 1), 'V': (6, 1), 'W': (7, 1),
    'X': (8, 1), 'Y': (9, 1), 'Z': (10, 1), '!': (11, 1),
    '0': (0, 2), '1': (1, 2), '2': (2, 2), '3': (3, 2),
    '4': (4, 2), '5': (5, 2), '6': (6, 2), '7': (7, 2),
    '8': (8, 2), '9': (9, 2),
}


class SpritesMixin:
    """
    Handles image loading and sprite scaling.
    """

    if TYPE_CHECKING:
        TILE_SIZE: int
        _ascii_cache: dict[tuple[str, int], pygame.Surface]
        _ascii_font_size: int | None

    # ASCII-fallback for missing assets.
    # letter + RGB + size-fraction (relative to TILE_SIZE).
    _ASCII_FALLBACK: dict[str, tuple[str, tuple[int, int, int], float]] = {
        "wall": ("#", (33, 33, 255), 1.0),
        "floor": (" ", (0, 0, 0), 1.0),
        "Pacgum": (".", (255, 255, 255), 0.6),
        "Super_Pacgum": ("O", (255, 255, 255), 0.9),
        "Pacman_Right": (">", (255, 255, 0), 1.0),
        "Pacman_Left": ("<", (255, 255, 0), 1.0),
        "Pacman_Up": ("^", (255, 255, 0), 1.0),
        "Pacman_Down": ("v", (255, 255, 0), 1.0),
        "Pacman_Death": ("X", (255, 255, 0), 1.0),
        "Blinky": ("B", (255, 0, 0), 1.0),
        "Pinky": ("P", (255, 184, 255), 1.0),
        "Inky": ("I", (0, 255, 255), 1.0),
        "Clyde": ("C", (255, 184, 82), 1.0),
        "Frighten": ("F", (0, 0, 255), 1.0),
        "Frighten_End": ("F", (255, 255, 255), 1.0),
        "Dead": ("x", (180, 180, 180), 1.0),
    }

    def _get_ascii_font(self) -> pygame.font.Font:
        """
        Return the font used for ASCII fallbacks.
        """
        if not pygame.font.get_init():
            pygame.font.init()
        cached_size = getattr(self, "_ascii_font_size", None)
        if cached_size != self.TILE_SIZE:
            size = max(8, int(self.TILE_SIZE * 0.9))
            typo = os.path.join(_ROOT, "assets", "Typo", "ByteBounce.ttf")
            try:
                if os.path.exists(typo):
                    self._ascii_font = pygame.font.Font(typo, size)
                else:
                    self._ascii_font = pygame.font.SysFont(
                        "Courier", size, bold=True
                    )
            except Exception:
                self._ascii_font = pygame.font.SysFont(
                    "Courier", size, bold=True
                )
            self._ascii_font_size = self.TILE_SIZE
            self._ascii_cache = {}
        return self._ascii_font

    def ascii_glyph(self, key: str) -> pygame.Surface:
        """
        Return a tile-sized surface drawing the ASCII fallback for key.
        Cached per (key, TILE_SIZE) so the surface is only built once.
        """
        if not hasattr(self, "_ascii_cache"):
            self._ascii_cache = {}
        cache_key = (key, self.TILE_SIZE)
        if cache_key in self._ascii_cache:
            return self._ascii_cache[cache_key]

        letter, color, frac = self._ASCII_FALLBACK.get(
            key, ("?", (255, 0, 255), 1.0)
        )
        font = self._get_ascii_font()
        box = max(1, int(self.TILE_SIZE * frac))
        surf: pygame.Surface = pygame.Surface(
            (self.TILE_SIZE, self.TILE_SIZE), pygame.SRCALPHA
        )
        if letter.strip():
            text = font.render(letter, True, color)
            # Scale text to fit the requested box while preserving aspect.
            tw, th = text.get_size()
            if tw and th:
                scale = min(box / tw, box / th)
                if scale != 1.0:
                    text = pygame.transform.smoothscale(
                        text,
                        (max(1, int(tw * scale)), max(1, int(th * scale))),
                    )
            rect = text.get_rect(
                center=(self.TILE_SIZE // 2, self.TILE_SIZE // 2)
            )
            surf.blit(text, rect)
        self._ascii_cache[cache_key] = surf
        return surf

    def render_text(
        self, label: str, color_row: int = 24
    ) -> pygame.Surface | None:
        """
        Render label from the texts.png sprite sheet, scaled to the tile
        size, using the colour block starting at color_row (24 = yellow).
        Falls back to the ByteBounce font when the sheet is unavailable, and
        returns None only if even the fallback cannot be built.
        """
        texts = self.sprites.get("texts")
        if isinstance(texts, pygame.Surface):
            scale = max(1, self.TILE_SIZE // _TEXT_TILE)
            dw, dh = _TEXT_TILE * scale, _TEXT_TILE * scale
            surf = pygame.Surface((len(label) * dw, dh), pygame.SRCALPHA)
            missing: list[str] = []
            for i, ch in enumerate(label):
                if ch not in _TEXT_CMAP:
                    missing.append(ch)
                    continue
                col, row = _TEXT_CMAP[ch]
                sx = col * _TEXT_TILE
                sy = (row + color_row) * _TEXT_TILE
                if (sx + _TEXT_TILE > texts.get_width()
                        or sy + _TEXT_TILE > texts.get_height()):
                    print(
                        f"[WARNING] Tile '{ch}' out of bound ({sx},{sy}) in"
                        f" texts.png {texts.get_size()} — caracter ignored.",
                        file=sys.stderr,
                    )
                    continue
                tile = texts.subsurface(
                    pygame.Rect(sx, sy, _TEXT_TILE, _TEXT_TILE))
                surf.blit(pygame.transform.scale(tile, (dw, dh)), (i * dw, 0))
            if missing:
                print(f"[WARNING] Missing caracters from CMAP : {missing}",
                      file=sys.stderr)
            return surf

        # Fallback: render with the ByteBounce font.
        fb_path = os.path.join(_ROOT, "assets", "Typo", "ByteBounce.ttf")
        fb_size = max(12, self.TILE_SIZE * 2)
        try:
            fb_font = pygame.font.Font(fb_path, fb_size)
        except Exception:
            fb_font = pygame.font.SysFont(None, fb_size)
        print("[text] ℹ texts.png not accessible — fallback to ByteBounce.")
        return fb_font.render(label, True, (255, 255, 0))

    def _load_raw(self, rel_path: str) -> pygame.Surface | None:
        path = os.path.join(_ROOT, "assets", rel_path)
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            return img
        return None

    def _preload_raw_images(self) -> None:
        self.raw_images: dict[
            str, pygame.Surface | list[pygame.Surface | None] | None
        ] = {
            "floor": self._load_raw("Maze/MazePart/Tile/BlackTile.png"),
            # Borders
            "Border_TopHorizontal": self._load_raw(
                "Maze/MazePart/Wall/Border/TopHorizontal.png"
            ),
            "Border_BottomHorizontal": self._load_raw(
                "Maze/MazePart/Wall/Border/BottomHorizontal.png"
            ),
            "Border_LeftVertical": self._load_raw(
                "Maze/MazePart/Wall/Border/LeftVertical.png"
            ),
            "Border_RightVertical": self._load_raw(
                "Maze/MazePart/Wall/Border/RightVertical.png"
            ),
            "Border_TopToRight": self._load_raw(
                "Maze/MazePart/Wall/Border/TopToRight.png"
            ),
            "Border_BottomToRight": self._load_raw(
                "Maze/MazePart/Wall/Border/BottomToRight.png"
            ),
            "Border_LeftToTop": self._load_raw(
                "Maze/MazePart/Wall/Border/LeftToTop.png"
            ),
            "Border_LeftToBottom": self._load_raw(
                "Maze/MazePart/Wall/Border/LeftToBottom.png"
            ),
            # Straight inner walls
            "Inside_HorizontalTop": self._load_raw(
                "Maze/MazePart/Wall/Inside/HorizontalTop.png"
            ),
            "Inside_VerticalLeft": self._load_raw(
                "Maze/MazePart/Wall/Inside/VerticalLeft.png"
            ),
            # Pac-gums
            "Pacgum": self._load_raw("Maze/Pacgum.png"),
            "Super_Pacgum": self._load_raw("Maze/Super-Pacgum_2.png"),
        }

        # Ghosts
        for entity in ["Blinky", "Pinky", "Inky", "Clyde"]:
            for d in ["Up", "Down", "Left", "Right"]:
                self.raw_images[f"{entity}_{d}"] = [
                    self._load_raw(
                        f"Sprites/sprites/ghosts/{entity}/{d}/{d}_0.png"
                    ),
                    self._load_raw(
                        f"Sprites/sprites/ghosts/{entity}/{d}/{d}_1.png"
                    ),
                ]

        # Frighten
        self.raw_images["Frighten"] = [
            self._load_raw("Sprites/sprites/ghosts/Frighten/Frighten_0.png"),
            self._load_raw("Sprites/sprites/ghosts/Frighten/Frighten_1.png"),
        ]

        self.raw_images["Dead_Down"] = [
            self._load_raw("Sprites/sprites/ghosts/Dead/DeadBottom.png")
        ]
        self.raw_images["Dead_Up"] = [
            self._load_raw("Sprites/sprites/ghosts/Dead/DeadTop.png")
        ]
        self.raw_images["Dead_Left"] = [
            self._load_raw("Sprites/sprites/ghosts/Dead/DeadLeft.png")
        ]
        self.raw_images["Dead_Right"] = [
            self._load_raw("Sprites/sprites/ghosts/Dead/DeadRight.png")
        ]

        self.raw_images["Frighten_End"] = [
            self._load_raw(
                "Sprites/sprites/ghosts/Frighten/EndFrighten_0.png"
            ),
            self._load_raw(
                "Sprites/sprites/ghosts/Frighten/EndFrighten_1.png"
            ),
            self._load_raw("Sprites/sprites/ghosts/Frighten/Frighten_0.png"),
            self._load_raw("Sprites/sprites/ghosts/Frighten/Frighten_1.png"),
        ]

        # Pacman
        for d in ["Up", "Down", "Left", "Right"]:
            self.raw_images[f"Pacman_{d}"] = [
                self._load_raw(
                    f"Sprites/sprites/Pacman/animations/{d}/{d}_{i}.png"
                )
                for i in range(4)
            ]

        self.raw_images["Pacman_Death"] = [
            self._load_raw(
                f"Sprites/sprites/Pacman/animations/Death/Death_{i}.png"
            )
            for i in range(13)
        ]

        # texts.png — not normalized to keep raw cords
        _texts_path = os.path.join(_ROOT, "assets", "Typo", "texts.png")
        if not os.path.exists(_texts_path):
            print(
                f"[WARNING] texts.png not found : {_texts_path}\n"
                "  -> fallback (ByteBounce) will be used for READY!",
                file=sys.stderr
            )
            self.raw_images["texts"] = None
        else:
            try:
                _surf = pygame.image.load(_texts_path).convert_alpha()
                _w, _h = _surf.get_size()
                _expected_w, _expected_h = 128, 224
                if _w != _expected_w or _h != _expected_h:
                    print(
                        f"[WARNING] texts.png loaded but unexpected "
                        f"dimensions : {_w}×{_h} "
                        f"(instead of {_expected_w}×{_expected_h})\n"
                        "  → Tile grid might be off.",
                        file=sys.stderr
                    )
                else:
                    pass
                self.raw_images["texts"] = _surf
            except Exception as exc:
                print(
                    f"[WARNING] Error while loading texts.png : "
                    f"{exc}\n"
                    " -> fallback (ByteBounce) will be used for READY!"
                )
                self.raw_images["texts"] = None

    def scale_sprites(self) -> None:
        """
        Rescale every raw sprite to the current tile size for rendering.
        """
        self._ascii_cache = {}
        self._ascii_font_size: int | None = None
        self.sprites: dict[
            str, pygame.Surface | list[pygame.Surface | None] | None
        ] = {}
        for key, item in self.raw_images.items():
            # texts.png must stay at its original resolution so subsurface
            # extraction uses the correct pixel coordinates.
            if key == "texts":
                self.sprites[key] = item
                continue
            if isinstance(item, list):
                scaled_list: list[pygame.Surface | None] = []
                for img in item:
                    if img:
                        scaled = pygame.transform.scale(
                            img, (self.TILE_SIZE, self.TILE_SIZE)
                        )
                        scaled_list.append(scaled)
                    else:
                        scaled_list.append(None)
                self.sprites[key] = scaled_list
            else:
                img = item
                if img:
                    # Set a specific size for items
                    if key == "Pacgum":
                        size = max(3, int(self.TILE_SIZE * 0.3))  # Small dot
                    elif key == "Super_Pacgum":
                        size = max(5, int(self.TILE_SIZE * 0.6))  # Large dot
                    else:
                        size = self.TILE_SIZE

                    scaled = pygame.transform.scale(img, (size, size))
                    if key.startswith("Inside_"):
                        scaled.set_colorkey((0, 0, 0))
                    self.sprites[key] = scaled
                else:
                    self.sprites[key] = None
