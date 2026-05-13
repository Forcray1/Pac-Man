from entities.entity import Entity


class Pacgum(Entity):
    """
    Class representing a standard pac-gum.
    Awards points when eaten by Pac-Man.
    """
    def __init__(self, x: int, y: int) -> None:
        # Pass a tuple to match the Entity base class interface
        super().__init__((x, y))
        self.sprite = '.'
        self.points = 10

    def update(self) -> None:
        """
        A standard pac-gum is static, so its update method
        does nothing in particular.
        """
        pass


class SuperPacgum(Entity):
    """
    Class representing a super pac-gum.
    Awards more points and grants Pac-Man the ability to eat ghosts.
    """
    def __init__(self, x: int, y: int) -> None:
        super().__init__((x, y))
        self.sprite = 'O'
        self.points = 50
        self.timer = 0  # Used to manage blinking

    def update(self) -> None:
        """
        Handles the blinking of the super pac-gum at each tick
        for a classic arcade effect.
        """
        if not self.active:
            return

        self.timer += 1
        # Toggle display state every 3 frames
        # (roughly every half-second with the current tick rate)
        if self.timer % 3 == 0:
            self.sprite = 'O' if self.sprite == ' ' else ' '
