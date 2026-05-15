from __future__ import annotations

import os

import pygame

from display._maze_utils import _ROOT


class SpritesMixin:
    """Handles image loading and sprite scaling."""

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

    def scale_sprites(self) -> None:
        self.sprites: dict[
            str, pygame.Surface | list[pygame.Surface | None] | None
        ] = {}
        for key, item in self.raw_images.items():
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
                        size = int(self.TILE_SIZE * 0.3)  # Small dot
                    elif key == "Super_Pacgum":
                        size = int(self.TILE_SIZE * 0.6)  # Large dot
                    else:
                        size = self.TILE_SIZE

                    scaled = pygame.transform.scale(img, (size, size))
                    if key.startswith("Inside_"):
                        scaled.set_colorkey((0, 0, 0))
                    self.sprites[key] = scaled
                else:
                    self.sprites[key] = None
