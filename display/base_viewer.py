from abc import ABC, abstractmethod
from typing import Any

from controllers.maze_controller import MazeController
from utils.observer import MazeEvent


class BaseViewer(ABC):
    """Base class for views.

    Automatically subscribes to controller events via EventBus.
    """

    def __init__(self, controller: MazeController) -> None:
        self.controller = controller
        self._register_events()

    def _register_events(self) -> None:
        bus = self.controller.events
        bus.subscribe(MazeEvent.MAZE_GENERATED, self.on_maze_generated)
        bus.subscribe(MazeEvent.MAZE_STEP, self.on_maze_step)
        bus.subscribe(MazeEvent.SOLVE_COMPLETE, self.on_solve_complete)
        bus.subscribe(MazeEvent.SOLVE_STEP, self.on_solve_step)
        bus.subscribe(MazeEvent.TYPE_CHANGED, self.on_type_changed)
        bus.subscribe(MazeEvent.ERROR, self.on_error)

    def on_maze_generated(self, **kwargs: Any) -> None:
        pass

    def on_maze_step(self, **kwargs: Any) -> None:
        pass

    def on_solve_complete(self, **kwargs: Any) -> None:
        pass

    def on_solve_step(self, **kwargs: Any) -> None:
        pass

    def on_type_changed(self, **kwargs: Any) -> None:
        pass

    def on_error(self, **kwargs: Any) -> None:
        pass

    @abstractmethod
    def display(self) -> None:
        pass

    @abstractmethod
    def close(self) -> None:
        pass
