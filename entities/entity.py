from abc import ABC, abstractmethod
from typing import Any


class Entity(ABC):
    """
    Abstract base class representing any mobile or interactive
    entity in the game (Pac-Man, Ghosts).

    The chosen architecture separates the entity logic (its position,
    its state) from its display.
    This class provides a solid common foundation for:
    - Managing spatial position (on the grid).
    - Active/inactive state (e.g. alive or eaten).
    - A strict contract (`update`) to force subclasses
    to implement their game behaviour.
    """

    def __init__(self, pos: tuple[int, int]) -> None:
        """
        Initialise the entity with default coordinates.

        Args:
            pos (tuple): Tuple containing (x, y)
        """
        self.pos: tuple[int, int] = pos
        self.prev_pos: tuple[int,
                             int] = pos  # Track previous position to detect
        # if entities cross paths

        # Variables for modulating speed on the grid
        self.speed_multiplier: float = 0.15
        self.move_accumulator: float = 0.0

        # The sprite or ASCII character representing the entity.
        # Can be typed more strictly depending on the view used.
        self.sprite: Any = None

        # `active` tracks whether the entity should be updated/displayed.
        # Useful when a ghost is eaten or Pac-Man dies,
        # without deleting the object.
        self.active: bool = True

    @property
    def x(self) -> int:
        """
        Return the current X coordinate.
        """
        return self.pos[0]

    @property
    def y(self) -> int:
        """
        Return the current Y coordinate.
        """
        return self.pos[1]

    def set_position(self, x: int, y: int) -> None:
        """
        Update the entity's position.
        Using this method instead of modifying `self.pos` directly
        allows adding checks or movement events later.
        """
        self.pos = (x, y)

    @abstractmethod
    def update(self) -> None:
        """
        Abstract method defining the entity update logic
        (AI, movement).
        Each subclass (Ghost, Player) MUST override this method because
        their movement and behaviour rules differ greatly.
        """
        pass
