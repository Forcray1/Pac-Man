import curses
from typing import Any, Protocol
from controllers.maze_controller import MazeController
from core.maze import Maze, CellType


class _AsciiViewerProtocol(Protocol):
    stdscr: Any

    def _update_maze_lines(self) -> None: ...

    def _draw_maze(
        self, stdscr: Any, visible_lines: int, max_x: int
    ) -> None: ...
    def show_message(self, msg: str) -> None: ...


class AsciiInteractiveConfig:

    def __init__(
        self, viewer: "_AsciiViewerProtocol", controller: "MazeController"
    ) -> None:
        self.viewer = viewer
        self.controller = controller
        self.stdscr = viewer.stdscr

    def resize(self) -> None:
        curses.curs_set(0)
        curses.mousemask(0)  # Disable mouse to avoid flickering
        self.stdscr.clear()

        width = self.controller.config["WIDTH"]
        height = self.controller.config["HEIGHT"]

        while True:
            self.stdscr.erase()
            max_y, max_x = self.stdscr.getmaxyx()
            visible_maze_lines = max_y - 2

            entry = self.controller.config.get("ENTRY", (0, 0))
            exit_pt = self.controller.config.get(
                "EXIT", (width - 1, height - 1))
            t_entry = (min(entry[0], width - 1), min(entry[1], height - 1))
            t_exit = (min(exit_pt[0], width - 1), min(exit_pt[1], height - 1))

            temp_maze = Maze(width, height, t_entry, t_exit)
            self.controller.maze = temp_maze
            self.viewer._update_maze_lines()
            self.viewer._draw_maze(self.stdscr, visible_maze_lines, max_x)

            msg = (
                f" Size: {width}x{height} | Arrows: Resize | "
                f"ENTER: Confirm "
            )
            try:
                self.stdscr.addstr(
                    max_y - 1,
                    max(0, (max_x - len(msg)) // 2),
                    msg,
                    curses.color_pair(3) | curses.A_BOLD,
                )
            except curses.error:
                pass

            self.stdscr.refresh()

            key = self.stdscr.getch()
            if (
                key == curses.KEY_UP
                and height > 1
                and not (height == 2 and width == 1)
            ):
                height -= 1
            elif key == curses.KEY_DOWN and height < 200:
                height += 1
            elif (
                key == curses.KEY_LEFT
                and width > 1
                and not (width == 2 and height == 1)
            ):
                width -= 1
            elif key == curses.KEY_RIGHT and width < 200:
                width += 1
            elif key in [10, 13]:
                break

        self.controller.config["WIDTH"] = width
        self.controller.config["HEIGHT"] = height
        self.controller.config["ENTRY"] = t_entry
        self.controller.config["EXIT"] = t_exit

        valid_points = True
        if t_entry == t_exit:
            valid_points = False
        else:
            validator_maze = Maze(width, height, t_entry, t_exit)
            t_entry_cell = validator_maze.grid[t_entry[1]][t_entry[0]]
            t_exit_cell = validator_maze.grid[t_exit[1]][t_exit[0]]
            if (
                t_entry_cell.type == CellType.TEMPLATE
                or t_exit_cell.type == CellType.TEMPLATE
            ):
                valid_points = False

        if not valid_points:
            self.viewer.show_message(
                "Warning: Template overwrites entry/exit. Please reposition."
            )
            self.set_points()
        else:
            self.controller.generate_maze()

    def set_points(self) -> None:
        curses.curs_set(0)
        self.stdscr.clear()

        width = self.controller.config["WIDTH"]
        height = self.controller.config["HEIGHT"]

        ex, ey = self.controller.config.get("ENTRY", (0, 0))
        sx, sy = self.controller.config.get("EXIT", (width - 1, height - 1))

        ex, ey = min(ex, width - 1), min(ey, height - 1)
        sx, sy = min(sx, width - 1), min(sy, height - 1)

        state = "ENTRY"
        cursor_x = ex
        cursor_y = ey

        while True:
            self.stdscr.erase()
            max_y, max_x = self.stdscr.getmaxyx()
            visible_maze_lines = max_y - 2

            curr_e = (cursor_x, cursor_y) if state == "ENTRY" else (ex, ey)
            curr_s = (cursor_x, cursor_y) if state == "EXIT" else (sx, sy)

            temp_maze = Maze(width, height, curr_e, curr_s)
            self.controller.maze = temp_maze
            self.viewer._update_maze_lines()
            self.viewer._draw_maze(self.stdscr, visible_maze_lines, max_x)

            point_msg = "ENTRY" if state == "ENTRY" else "EXIT"
            msg = (
                f"  Place {point_msg} at [{cursor_x}, {cursor_y}]"
                f" | Arrows: Move | ENTER: Confirm   "
            )
            try:
                self.stdscr.addstr(
                    max_y - 1,
                    max(0, (max_x - len(msg)) // 2),
                    msg,
                    curses.color_pair(3) | curses.A_BOLD,
                )
            except curses.error:
                pass

            self.stdscr.refresh()

            key = self.stdscr.getch()
            if key == curses.KEY_UP and cursor_y > 0:
                cursor_y -= 1
            elif key == curses.KEY_DOWN and cursor_y < height - 1:
                cursor_y += 1
            elif key == curses.KEY_LEFT and cursor_x > 0:
                cursor_x -= 1
            elif key == curses.KEY_RIGHT and cursor_x < width - 1:
                cursor_x += 1
            elif key in [10, 13]:
                target_cell = temp_maze.grid[cursor_y][cursor_x]
                if target_cell.type == CellType.TEMPLATE:
                    self.viewer.show_message(
                        "Invalid: This point is on the logo.")
                    continue

                if state == "ENTRY":
                    ex, ey = cursor_x, cursor_y
                    state = "EXIT"
                    cursor_x = sx
                    cursor_y = sy
                else:
                    if cursor_x == ex and cursor_y == ey:
                        self.viewer.show_message(
                            "Invalid: Entry and exit cannot be at "
                            "the same position."
                        )
                        continue
                    sx, sy = cursor_x, cursor_y
                    break

        self.controller.config["ENTRY"] = (ex, ey)
        self.controller.config["EXIT"] = (sx, sy)
        self.controller.generate_maze()
