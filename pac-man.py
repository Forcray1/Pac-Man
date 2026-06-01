import os
import sys

import pygame

from core.parser import parser
from core.redirect import Redirect
from mazegenerator.mazegenerator import MazeGenerator  # noqa: E402


def main() -> None:
    if len(sys.argv) != 2:
        print(
            "Usage: python pac-man.py <config_file>\n"
            "Example: python pac-man.py config.json",
            file=sys.stderr,
        )
        sys.exit(1)
    else:
        try:
            maze = MazeGenerator((20, 20))
            if not maze.maze:
                raise ValueError
        except ValueError:
            print("ERROR: maze generator not working", file=sys.stderr)
        except Exception:
            print("ERROR: maze generator not found", file=sys.stderr)
        if not sys.argv[1].endswith(".json"):
            print("ERROR: the configuration file must be a json",
                  file=sys.stderr)
            sys.exit(0)
        config_file = f"config/{sys.argv[1]}"
        config_path = os.path.join(os.path.dirname(__file__), config_file)
        config = parser(config_path)
        if not config:
            print("ERROR: Failed to load config. Check config.json.",
                  file=sys.stderr)
            sys.exit(0)

        redirect = Redirect(config, config_path)
        redirect.main_menu()
        pygame.quit()


if __name__ == "__main__":
    main()
