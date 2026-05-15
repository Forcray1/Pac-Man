from __future__ import annotations

import pygame

from core.monitor import WALL
from entities.ghost_types import Blinky, Pinky, Inky, Clyde
from entities.items import SuperPacgum


class RendererMixin:
    """Handles all drawing and window-resize logic."""

    def get_wall_mask(self, grid: list[list[int]], x: int, y: int) -> int:
        mask = 0
        if y > 0 and grid[y - 1][x] == WALL:
            mask += 1  # Top = 1
        if x < self.cols - 1 and grid[y][x + 1] == WALL:
            mask += 2  # Right = 2
        if y < self.rows - 1 and grid[y + 1][x] == WALL:
            mask += 4  # Bottom = 4
        if x > 0 and grid[y][x - 1] == WALL:
            mask += 8  # Left = 8
        return mask

    def get_sprites_for_wall(
        self, mask: int, x: int, y: int
    ) -> list[pygame.Surface]:
        sprites_to_draw: list[pygame.Surface] = []
        is_border = False
        is_corner = False

        # --- 1. BORDER AND CORNER IDENTIFICATION ---
        border_sprite = None

        # Corner detection (no inside wall sprites here)
        if y == 0 and x == 0:
            border_sprite = self.sprites.get("Border_BottomToRight")
            is_corner = True
        elif y == 0 and x == self.cols - 1:
            border_sprite = self.sprites.get("Border_LeftToBottom")
            is_corner = True
        elif y == self.rows - 1 and x == 0:
            border_sprite = self.sprites.get("Border_TopToRight")
            is_corner = True
        elif y == self.rows - 1 and x == self.cols - 1:
            border_sprite = self.sprites.get("Border_LeftToTop")
            is_corner = True

        # Straight border detection (if not a corner)
        elif y == 0:
            border_sprite = self.sprites.get("Border_TopHorizontal")
        elif y == self.rows - 1:
            border_sprite = self.sprites.get("Border_BottomHorizontal")
        elif x == 0:
            border_sprite = self.sprites.get("Border_LeftVertical")
        elif x == self.cols - 1:
            border_sprite = self.sprites.get("Border_RightVertical")

        if border_sprite and isinstance(border_sprite, pygame.Surface):
            sprites_to_draw.append(border_sprite)
            is_border = True

        # If it's a corner, stop here: don't draw any blue lines
        if is_corner:
            return sprites_to_draw

        # --- 2. DRAWING JUNCTIONS WITH OFFSET ---
        temp_surface = pygame.Surface(
            (self.TILE_SIZE, self.TILE_SIZE), pygame.SRCALPHA
        )
        mid = self.TILE_SIZE // 2
        color = (33, 33, 255)  # Pac-Man blue

        # OFFSET: double border thickness.
        # Adjust this value (4, 5 or 6) so the line stops exactly on
        # the sprite edge.
        offset = 5

        if not is_border:
            # Normal cell inside the maze
            if mask == 0:
                # Isolated wall (surrounded by empty cells)
                pygame.draw.rect(
                    temp_surface, color, (mid - 2, mid - 2, 4, 4), 2
                )
            if mask & 1:
                pygame.draw.line(temp_surface, color, (mid, mid), (mid, 0), 2)
            if mask & 2:
                pygame.draw.line(
                    temp_surface, color, (mid, mid), (self.TILE_SIZE, mid), 2
                )
            if mask & 4:
                pygame.draw.line(
                    temp_surface, color, (mid, mid), (mid, self.TILE_SIZE), 2
                )
            if mask & 8:
                pygame.draw.line(temp_surface, color, (mid, mid), (0, mid), 2)
        else:
            # BORDER cell: connect the interior toward the inner edge
            # of the sprite

            # TOP border: draw a line coming from the bottom up to offset
            if y == 0 and (mask & 4):
                pygame.draw.line(
                    temp_surface,
                    color,
                    (mid, self.TILE_SIZE),
                    (mid, offset),
                    2,
                )

            # BOTTOM border: draw a line coming from the top down to
            # (size - offset)
            if y == self.rows - 1 and (mask & 1):
                pygame.draw.line(
                    temp_surface,
                    color,
                    (mid, 0),
                    (mid, self.TILE_SIZE - offset),
                    2,
                )

            # LEFT border: draw a line coming from the right up to offset
            if x == 0 and (mask & 2):
                pygame.draw.line(
                    temp_surface,
                    color,
                    (self.TILE_SIZE, mid),
                    (offset, mid),
                    2,
                )

            # RIGHT border: draw a line coming from the left up to
            # (size - offset)
            if x == self.cols - 1 and (mask & 8):
                pygame.draw.line(
                    temp_surface,
                    color,
                    (0, mid),
                    (self.TILE_SIZE - offset, mid),
                    2,
                )

        sprites_to_draw.append(temp_surface)
        return sprites_to_draw

    def draw_maze(self) -> None:
        actual_w, actual_h = self.screen.get_size()
        self.offset_x = (actual_w - (self.cols * self.TILE_SIZE)) // 2
        self.offset_y = (actual_h - (self.rows * self.TILE_SIZE)) // 2
        grid = self.monitor.grid
        for y in range(self.rows):
            for x in range(self.cols):
                rect = pygame.Rect(
                    self.offset_x + x * self.TILE_SIZE,
                    self.offset_y + y * self.TILE_SIZE,
                    self.TILE_SIZE,
                    self.TILE_SIZE,
                )

                if grid[y][x] == WALL:
                    mask = self.get_wall_mask(grid, x, y)
                    sprites = self.get_sprites_for_wall(mask, x, y)

                    # Always paint a pure black background under the wall
                    # before drawing its transparent lines
                    pygame.draw.rect(self.screen, (0, 0, 0), rect)

                    if sprites:
                        for sprite in sprites:
                            self.screen.blit(sprite, rect.topleft)
                    else:
                        pygame.draw.rect(self.screen, (0, 0, 200), rect)
                        # Fallback blue
                else:
                    floor = self.sprites.get("floor")
                    if floor and isinstance(floor, pygame.Surface):
                        self.screen.blit(floor, rect.topleft)
                    else:
                        pygame.draw.rect(self.screen, (0, 0, 0), rect)
                        # Fallback floor

    def _update_dimensions(self, new_tile_size: int) -> None:
        """Update the tile size and resize the window accordingly."""
        # Safety guard to avoid tiny tiles
        self.TILE_SIZE = max(4, new_tile_size)

        # Recompute screen size
        self.screen_width = (self.cols * self.TILE_SIZE) + (2 * self.margin)
        self.screen_height = (self.rows * self.TILE_SIZE) + (2 * self.margin)

        # Apply the new video mode
        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height), pygame.RESIZABLE
        )

        # Re-centre and rescale sprites
        self.offset_x = (self.screen_width - (self.cols * self.TILE_SIZE)) // 2
        self.offset_y = (
            self.screen_height - (self.rows * self.TILE_SIZE)
        ) // 2
        self.scale_sprites()

    def draw_items(self) -> None:
        """Draw the active pac-gums and super pac-gums."""
        all_gums = self.monitor.pacgums + self.monitor.super_pacgums

        for gum in all_gums:
            if gum.active:
                sprite_key = (
                    "Super_Pacgum"
                    if isinstance(gum, SuperPacgum)
                    else "Pacgum"
                )
                sprite = self.sprites.get(sprite_key)

                if sprite and isinstance(sprite, pygame.Surface):
                    # Compute position to centre the sprite in the cell
                    pos_x = (
                        self.offset_x
                        + (gum.x * self.TILE_SIZE)
                        + (self.TILE_SIZE - sprite.get_width()) // 2
                    )
                    pos_y = (
                        self.offset_y
                        + (gum.y * self.TILE_SIZE)
                        + (self.TILE_SIZE - sprite.get_height()) // 2
                    )
                    self.screen.blit(sprite, (pos_x, pos_y))

    def draw_player(self) -> None:
        """Draw Pac-Man with interpolation for smooth movement."""
        player = self.monitor.player
        if not player.active:
            return

        render_x, render_y = float(player.x), float(player.y)

        # Normal movement
        if not player.is_dying:
            dx, dy = player.direction
            grid = self.monitor.grid
            if (0 <= player.y + dy < self.rows and
                    0 <= player.x + dx < self.cols and
                    grid[player.y + dy][player.x + dx] != 1):
                render_x += dx * player.move_accumulator
                render_y += dy * player.move_accumulator

            # Animation selection
            dir_map = {0: "Right", 90: "Up", 180: "Left", 270: "Down"}
            anim_dir = dir_map.get(player.angle, "Right")

            frames = self.sprites.get(f"Pacman_{anim_dir}")
            if frames and isinstance(frames, list):
                # 4 frames per animation, ~100 ms per frame
                frame_index = (pygame.time.get_ticks() // 100) % 4
                base_sprite = frames[frame_index]
            else:
                base_sprite = None
        else:
            # Death sequence
            if player.death_start_time == 0:
                player.death_start_time = pygame.time.get_ticks()

            elapsed = pygame.time.get_ticks() - player.death_start_time
            frames = self.sprites.get("Pacman_Death")
            if frames and isinstance(frames, list):
                frame_index = elapsed // 100
                if frame_index >= len(frames):
                    # Hold on the last frame
                    frame_index = len(frames) - 1
                base_sprite = frames[frame_index]
            else:
                base_sprite = None

        if base_sprite:
            # Convert to pixel coordinates
            pos_x = self.offset_x + render_x * self.TILE_SIZE
            pos_y = self.offset_y + render_y * self.TILE_SIZE

            rect = base_sprite.get_rect(
                center=(
                    pos_x + self.TILE_SIZE // 2,
                    pos_y + self.TILE_SIZE // 2,
                )
            )
            self.screen.blit(base_sprite, rect.topleft)

    def draw_ghost_paths(self) -> None:
        """Draw each ghost's current path (practice mode only)."""
        if not self.practice:
            return

        color_map = {
            "Blinky": (255, 0, 0),
            "Pinky": (255, 184, 255),
            "Inky": (0, 255, 255),
            "Clyde": (255, 184, 82),
            "Eatable": (0, 0, 255),
        }
        ts = self.TILE_SIZE
        half = ts // 2

        for ghost in self.monitor.ghosts:
            if not ghost.active or not ghost.current_path:
                continue

            c_name = ghost.__class__.__name__
            key = "Eatable" if ghost.eatable else c_name
            color = color_map.get(key, (200, 200, 200))
            path = ghost.current_path

            dir_vec = {
                "N": (0, -1), "S": (0, 1),
                "E": (1, 0), "W": (-1, 0),
            }
            dx, dy = dir_vec.get(ghost.direction, (0, 0))
            rx = float(ghost.x)
            ry = float(ghost.y)
            grid = self.monitor.grid
            if (0 <= ghost.y + dy < self.rows and
                    0 <= ghost.x + dx < self.cols and
                    grid[ghost.y + dy][ghost.x + dx] != 1):
                rx += dx * ghost.move_accumulator
                ry += dy * ghost.move_accumulator

            points = [
                (
                    self.offset_x + rx * ts + half,
                    self.offset_y + ry * ts + half,
                )
            ]
            for px, py in path:
                points.append((
                    self.offset_x + px * ts + half,
                    self.offset_y + py * ts + half,
                ))

            if len(points) >= 2:
                pygame.draw.lines(self.screen, color, False, points, 3)
                last_px, last_py = path[-1]
                end_x = self.offset_x + last_px * ts + half
                end_y = self.offset_y + last_py * ts + half
                pygame.draw.circle(self.screen, color, (end_x, end_y), 6)

    def draw_ghosts(self) -> None:
        """Draw all ghosts with smooth interpolation and blink effect."""
        dir_map_vectors = {
            "N": (0, -1),
            "S": (0, 1),
            "E": (1, 0),
            "W": (-1, 0),
        }
        dir_map_str = {"N": "Up", "S": "Down", "E": "Right", "W": "Left"}
        player = self.monitor.player

        for ghost in self.monitor.ghosts:
            if not ghost.active:
                continue

            # --- POSITION COMPUTATION (Interpolation) ---
            dx, dy = dir_map_vectors.get(ghost.direction, (0, 0))
            render_x, render_y = float(ghost.x), float(ghost.y)
            render_x += dx * ghost.move_accumulator
            render_y += dy * ghost.move_accumulator

            # --- FRAME SELECTION ---
            ghost_dir = dir_map_str.get(ghost.direction, "Down")

            if ghost.is_dead:
                frames = self.sprites.get(f"Dead_{ghost_dir}")

            elif ghost.eatable:
                # Blink threshold: 3 seconds * 30 FPS = 90
                if player.power_timer < 90:
                    # Alternate between blue and white every 5 frames
                    if (player.power_timer // 5) % 2 == 0:
                        frames = self.sprites.get("Frighten_End")
                    else:
                        frames = self.sprites.get("Frighten")
                else:
                    frames = self.sprites.get("Frighten")

            elif isinstance(ghost, Blinky):
                frames = self.sprites.get(f"Blinky_{ghost_dir}")
            elif isinstance(ghost, Pinky):
                frames = self.sprites.get(f"Pinky_{ghost_dir}")
            elif isinstance(ghost, Inky):
                frames = self.sprites.get(f"Inky_{ghost_dir}")
            elif isinstance(ghost, Clyde):
                frames = self.sprites.get(f"Clyde_{ghost_dir}")
            else:
                frames = None

            # --- Drawing with double validation ---
            if frames and isinstance(frames, list):
                frame_index = (pygame.time.get_ticks() // 150) % len(frames)
                sprite = frames[frame_index]

                if sprite:  # CRITICAL: only blit if the sprite is valid
                    pos_x = self.offset_x + render_x * self.TILE_SIZE
                    pos_y = self.offset_y + render_y * self.TILE_SIZE
                    self.screen.blit(sprite, (pos_x, pos_y))
