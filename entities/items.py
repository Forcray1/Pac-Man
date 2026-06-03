from entities.entity import Entity


class Pacgum(Entity):
    """
    Class representing a standard pac-gum.
    Awards points when eaten by Pac-Man.
    """
    def __init__(self, x: int, y: int) -> None:
        """
        Initialize a pac-gum at (x, y) with the default points value.
        """
        # Pass a tuple to match the Entity base class interface
        super().__init__((x, y))
        self.sprite = '.'
        self.points = 10

    def update(self, dt_ms: int = 0) -> None:
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
        """
        Initialize a super pac-gum at (x, y) with its blinking timer.
        """
        super().__init__((x, y))
        self.sprite = 'O'
        self.points = 50
        self.timer = 0  # ms accumulator used to manage blinking

    # Toggle the blink roughly every 100 ms
    BLINK_PERIOD_MS = 100

    def update(self, dt_ms: int = 0) -> None:
        """
        Handles the blinking of the super pac-gum for a classic arcade
        effect. dt_ms is the real time elapsed since the previous tick.
        """
        if not self.active:
            return

        self.timer += dt_ms
        if self.timer >= self.BLINK_PERIOD_MS:
            self.timer -= self.BLINK_PERIOD_MS
            self.sprite = 'O' if self.sprite == ' ' else ' '
