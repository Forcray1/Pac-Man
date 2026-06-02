from entities.entity import Entity
from typing import Tuple


class PacMan(Entity):
    """
    Class representing the player (Pac-Man).
    Inherits from the Entity class.
    """
    def __init__(self,
                 x: int,
                 y: int,
                 lives: int = 3,
                 power_duration: int = 15000
                 ) -> None:
        """
        Initialize Pac-Man at *(x, y)* with the given number of *lives* and
        the super pac-gum effect *power_duration* in milliseconds.
        """
        super().__init__((x, y))
        self.sprite = 'C'  # Fallback ASCII representation

        self.score: int = 0
        self.lives: int = lives
        self.default_power_duration: int = power_duration

        # Direction vector (dx, dy) - stationary at start
        self.direction: Tuple[int, int] = (0, 0)
        # Buffer for "Cornering"
        self.next_direction: Tuple[int, int] = (0, 0)

        # Management of "Super" mode (when eating a super pac-gum)
        self.is_powered_up: bool = False
        self.power_timer: int = 0  # Remaining super time
        self.ghosts_eaten_in_combo: int = 0  # Points multiplier

        self.eating_timer: int = 0  # ms left of the slowdown while eating

        # --- Variables for the Graphical view (Pygame / Blender) ---
        self.px: float = float(x)  # Fine position (Lerp) for fake 3D
        self.py: float = float(y)
        self.angle: int = 0        # 0=Right, 90=Up, 180=Left, 270=Down
        self.is_dying: bool = False
        # self.speed_multiplier is inherited from Entity
        self.death_start_time: int = 0

    def set_direction(self, dx: int, dy: int) -> None:
        """
        Store the next direction requested by the player.
        dx, dy: -1, 0, or 1 (e.g. (1, 0) to move right).
        """
        self.next_direction = (dx, dy)

    def update(self, dt_ms: int = 0) -> None:
        """
        Update called at each game tick. *dt_ms* is the real time elapsed
        since the previous tick (milliseconds), so every timer counts down
        in wall-clock time rather than in frames.
        """
        if not self.active or self.is_dying:
            return

        # Update angle for Blender graphical rendering
        if self.direction == (1, 0):
            self.angle = 0
        elif self.direction == (0, -1):
            self.angle = 90
        elif self.direction == (-1, 0):
            self.angle = 180
        elif self.direction == (0, 1):
            self.angle = 270

        # Handle end of the "Super Pac-Man" effect
        if self.is_powered_up:
            self.power_timer -= dt_ms
            if self.power_timer <= 0:
                self.is_powered_up = False
                #  self.speed_multiplier = 1.0  # Back to normal speed
                self.ghosts_eaten_in_combo = 0
        else:
            # Handle slowdown while consuming pac-gums
            # (outside Super mode)
            if self.eating_timer > 0:
                self.eating_timer -= dt_ms
                # Slowdown removed as it causes stuttering/lag
                #  self.speed_multiplier = 1.0
            else:
                #  self.speed_multiplier = 1.0  # Normal speed
                pass

        # Actual movement (x += dx) is handled by the controller (Game)
        # because collisions with walls (Maze) must be checked first
        # before allowing the actual change to self.pos.

    def eat(self, points: int) -> None:
        """
        Add points to the score.
        """
        self.score += points
        self.eating_timer = 0  # Disabled to avoid lag

    def trigger_power_up(self, duration: int = 0) -> None:
        """
        Activate Super mode for *duration* milliseconds. If no positive
        duration is given, falls back to the default configured duration.
        """
        self.is_powered_up = True
        self.power_timer = (
            duration if duration else self.default_power_duration
        )
        self.ghosts_eaten_in_combo = 0  # Reset the combo

    def eat_ghost(self, base_points: int = 200) -> int:
        """
        Point logic when Pac-Man eats a frightened ghost.
        Returns the number of points earned for this ghost.
        """
        points: int = base_points * (2 ** self.ghosts_eaten_in_combo)
        self.score += points
        self.ghosts_eaten_in_combo += 1
        return points

    def die(self) -> None:
        """
        Trigger Pac-Man's death sequence.
        """
        self.is_dying = True
        self.lives -= 1
        self.direction = (0, 0)
        self.next_direction = (0, 0)
