import curses
import os
import sys
from typing import Any, Optional

from core.monitor import Monitor, WALL
from entities.ghost_types import Blinky, Clyde, Inky, Pinky

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "mazegenerator-00001-py3-none-any"))

from mazegenerator.mazegenerator import (  # noqa: E402 # type: ignore
    MazeGenerator,
)


STYLES = {
    "epais": {
        "chars": [
            " ",
            "╹",
            "╺",
            "┗",
            "╻",
            "┃",
            "┏",
            "┣",
            "╸",
            "┛",
            "━",
            "┻",
            "┓",
            "┫",
            "┳",
            "╋",
        ]
    }
}


class AsciiViewer:
    """
    Curses renderer for Pac-Man.
    Owns only: maze rendering, pac-gum/player drawing, color setup,
    keyboard input.
    All game state and logic live in Monitor.
    """

    def __init__(self, config: Optional[dict] = None) -> None:
        self.stdscr: Optional[Any] = None

        if config:
            self.maze_width: int = int(config.get("width", 15))
            self.maze_height: int = int(config.get("height", 15))
            self._seed: int = int(config.get("seed", 0))
            # Map parser key names to internal monitor config keys
            self.config = {
                "super_pacgums": 4,
                "p_pacgums":     int(config.get("points_per_pacgum", 10)),
                "p_Spacgums": int(
                    config.get("points_per_super_pacgum", 50)),
                "super_time":    int(config.get("super_time", 30)),
                "cheat_mode": config.get("cheat_mode", False),
            }
        else:
            self.maze_width = 15
            self.maze_height = 15
            self._seed = 0
            self.config = {
                "super_pacgums": 4,
                "p_pacgums": 10,
                "p_Spacgums": 50,
                "super_time": 30,
                "cheat_mode": False,
            }

        self.maze_lines: list[str] = []

    def _build_monitor(self) -> Monitor:
        """Generate the maze and hand it to Monitor.from_maze()."""
        generator = MazeGenerator(size=(self.maze_width,
                                        self.maze_height),
                                  perfect=False,
                                  seed=self._seed)
        monitor = Monitor.from_maze(generator.maze,
                                    self.maze_width,
                                    self.maze_height,
                                    self.config)

        # Build the character lines for wall rendering (pure display concern)
        self._build_maze_lines(monitor.grid)

        return monitor

    def _build_maze_lines(self, grid: list[list[int]]) -> None:
        """Convert the int grid to the 'epais' box-drawing character lines."""
        chars = STYLES["epais"]["chars"]
        rows = len(grid)
        cols = len(grid[0]) if rows else 0

        self.maze_lines = []
        for y in range(rows):
            line_str = ""
            for x in range(cols):
                if grid[y][x] != WALL:
                    line_str += "  "
                else:
                    mask = 0
                    if y > 0 and grid[y - 1][x] == WALL:
                        mask += 1
                    if x < cols - 1 and grid[y][x + 1] == WALL:
                        mask += 2
                    if y < rows - 1 and grid[y + 1][x] == WALL:
                        mask += 4
                    if x > 0 and grid[y][x - 1] == WALL:
                        mask += 8
                    char = chars[mask]
                    right = "━" if mask & 2 else " "
                    line_str += char + right
            self.maze_lines.append(line_str)

    def init_colors(self) -> None:
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(4, curses.COLOR_BLUE, -1)   # Walls
        curses.init_pair(5, curses.COLOR_WHITE, -1)  # Pac-Gums
        curses.init_pair(7, curses.COLOR_YELLOW, -1)  # Pac-Man
        curses.init_pair(10, curses.COLOR_RED, -1)     # Blinky
        curses.init_pair(11, curses.COLOR_MAGENTA, -1)  # Pinky
        curses.init_pair(12, curses.COLOR_CYAN, -1)    # Inky
        curses.init_pair(13, curses.COLOR_GREEN, -1)   # Clyde
        curses.init_pair(14, curses.COLOR_BLUE, -1)    # Scared Ghost

    def _draw_maze(self) -> None:
        if not self.stdscr:
            return
        self.stdscr.erase()
        self.stdscr.addstr(0, 2, "=== PAC-MAN MAZE ===", curses.A_BOLD)
        for i, line in enumerate(self.maze_lines):
            try:
                self.stdscr.addstr(i + 2,
                                   2,
                                   line,
                                   curses.color_pair(4) | curses.A_BOLD)
            except curses.error:
                pass
        try:
            max_y, _ = self.stdscr.getmaxyx()
            self.stdscr.addstr(max_y - 2,
                               2,
                               "Press 'q' to quit.",
                               curses.A_DIM)
        except curses.error:
            pass
        self.stdscr.refresh()

    def _draw_entities(self, monitor: Monitor) -> None:
        """Draw pac-gums and PacMan on top of the maze."""
        if not self.stdscr:
            return
        # Pac-gums
        for gomme in monitor.pacgums + monitor.super_pacgums:
            if gomme.active:
                try:
                    self.stdscr.addstr(gomme.y + 2,
                                       gomme.x * 2 + 2,
                                       gomme.sprite,
                                       curses.color_pair(5))
                except curses.error:
                    pass

        # Ghosts
        for ghost in monitor.active_ghosts:
            if ghost.is_dead:
                color = curses.color_pair(15)
                # Maybe another pair, wait, dead ghost could just be
                # another color, let's say 8
            elif ghost.eatable:
                color = curses.color_pair(14)
            elif isinstance(ghost, Blinky):
                color = curses.color_pair(10)
            elif isinstance(ghost, Pinky):
                color = curses.color_pair(11)
            elif isinstance(ghost, Inky):
                color = curses.color_pair(12)
            elif isinstance(ghost, Clyde):
                color = curses.color_pair(13)
            else:
                color = curses.color_pair(5)
            try:
                if ghost.is_dead:
                    sprite = '"'
                else:
                    sprite = ghost.sprite if ghost.sprite else "M"
                self.stdscr.addstr(ghost.y + 2,
                                   ghost.x * 2 + 2,
                                   sprite, color | curses.A_BOLD)
            except curses.error:
                pass

        # PacMan
        pacman = monitor.player
        try:
            self.stdscr.addstr(pacman.y + 2,
                               pacman.x * 2 + 2,
                               pacman.sprite,
                               curses.color_pair(7) | curses.A_BOLD)
        except curses.error:
            pass

    def _draw_hud(self, monitor: Monitor) -> None:
        """Score and power-up indicator."""
        if not self.stdscr:
            return
        mode = " [SUPER]" if monitor.player.is_powered_up else ""
        # Display Game Over if dying
        if monitor.player.is_dying:
            mode += "  >>> GAME OVER <<<"
        try:
            self.stdscr.addstr(1,
                               2,
                               f"SCORE: {monitor.player.score}"
                               f"LIVES: {monitor.player.lives}{mode}",
                               curses.A_BOLD)

            cheat_enabled = self.config.get("cheat_mode", False)
            if cheat_enabled:
                god_status = "ON" if monitor.player.god_mode else "OFF"
                cheat_text = f"Cheats: [G] God Mode ({god_status})"
                cheat_row = len(self.maze_lines) + 2
                self.stdscr.addstr(cheat_row, 2, cheat_text,
                                   curses.color_pair(3))
        except curses.error:
            pass

    def _draw_debug(self, monitor: Monitor) -> None:
        """Display debug statistics and algorithm targets."""
        if not self.stdscr:
            return

        # Start debug 3 lines after the maze
        start_y = len(self.maze_lines) + 5

        # Table header
        header = f"{'ENTITY':<10} | {'MODE':<12} | " \
                 f"{'POS':<8} | {'TARGET':<8} | {'SPEED':<5}"
        try:
            self.stdscr.addstr(start_y, 2, "-" * len(header), curses.A_DIM)
            self.stdscr.addstr(start_y + 1,
                               2,
                               header,
                               curses.color_pair(12) | curses.A_BOLD)
            self.stdscr.addstr(start_y + 2,
                               2,
                               "-" * len(header),
                               curses.A_DIM)

            # Player data
            p = monitor.player
            p_mode = "POWERED" if p.is_powered_up else "NORMAL"
            p_info = f"{'PACMAN':<10} | {p_mode:<12} | ({p.x:02},{p.y:02})" \
                     f" | {'--':<8} | {p.speed_multiplier:<5.2f}"
            self.stdscr.addstr(start_y + 3, 2, p_info, curses.color_pair(7))

            # Ghost data
            for i, ghost in enumerate(monitor.ghosts):
                name = ghost.__class__.__name__

                # Current state
                if not ghost.active:
                    mode = "RESPAWN"
                elif ghost.eatable:
                    mode = "SCARED"
                else:
                    mode = "CHASE"

                # Computed target
                try:
                    target = ghost.choose_target(monitor)
                    target_str = f"({target[0]:02},{target[1]:02})"
                except Exception:
                    target_str = "ERR"

                ghost_info = f"{name:<10} | {mode:<12} | " \
                             f"({ghost.x:02},{ghost.y:02}) | " \
                             f"{target_str:<8} | " \
                             f"{ghost.speed_multiplier:<5.2f}"

                # Color for each ghost
                color_idx = 10 + i
                # Blinky=10, Pinky=11, etc. based on init_colors
                self.stdscr.addstr(start_y + 4 + i,
                                   2,
                                   ghost_info,
                                   curses.color_pair(color_idx))

            # Global info
            gums = len(monitor.all_items)
            sys_info = f"Items: {gums:03}/{monitor.start_pacgums} | "
            f"Maze: {monitor.cols}x{monitor.rows}"
            self.stdscr.addstr(start_y + 9, 2, sys_info, curses.A_DIM)

        except curses.error:
            pass

    def display(self) -> None:
        curses.wrapper(self.run_terminal_loop)

    def run_terminal_loop(self, stdscr: Any) -> None:
        self.stdscr = stdscr
        curses.curs_set(0)
        curses.mousemask(0)
        self.init_colors()
        stdscr.nodelay(True)
        stdscr.keypad(True)

        self._seed = int(self.config.get("seed", 0))
        monitor = self._build_monitor()

        while True:
            # Initial draw and pause
            self._draw_maze()
            self._draw_hud(monitor)
            self._draw_entities(monitor)
            stdscr.refresh()
            curses.napms(2000)  # Pause for 2 seconds to assimilate the map

            running = True
            tick_counter = 0

            while running:
                self._draw_maze()
                self._draw_hud(monitor)
                self._draw_entities(monitor)
                self._draw_debug(monitor)
                stdscr.refresh()

                # Keyboard input
                key = stdscr.getch()
                if key == ord('q'):
                    running = False
                    break
                cheat_enabled = self.config.get("cheat_mode", False)
                if cheat_enabled and key == ord('g'):
                    monitor.player.god_mode = not monitor.player.god_mode
                elif key == curses.KEY_UP:
                    monitor.player.set_direction(0, -1)
                elif key == curses.KEY_DOWN:
                    monitor.player.set_direction(0, 1)
                elif key == curses.KEY_LEFT:
                    monitor.player.set_direction(-1, 0)
                elif key == curses.KEY_RIGHT:
                    monitor.player.set_direction(1, 0)

                # Game tick (every 5 frames = ~150 ms)
                tick_counter += 1
                if tick_counter >= 5:
                    tick_counter = 0
                    if not monitor.player.is_dying:
                        try:
                            monitor.update()
                        except Exception:
                            print("ERROR: An unexpected error"
                                  "occurred while choosing target")
                            return

                if monitor.is_cleared():
                    break

                if monitor.player.lives <= 0:
                    running = False
                    break

                curses.napms(30)

            if not running:
                break

            score = monitor.player.score
            lives = monitor.player.lives
            self._seed = 0
            monitor = self._build_monitor()
            monitor.player.score = score
            monitor.player.lives = lives


if __name__ == "__main__":
    viewer = AsciiViewer()
    viewer.display()
