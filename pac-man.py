import os
import sys

import pygame

from core.parser import parser
from core.redirect import Redirect


def main() -> None:
    if len(sys.argv) != 2:
        print(
            "Usage: python pac-man.py <config_file>\n"
            "Example: python pac-man.py config.json",
            file=sys.stderr,
        )
        sys.exit(1)
    else:
        config_file = f"config/{sys.argv[1]}"
        config_path = os.path.join(os.path.dirname(__file__), config_file)
        config = parser(config_path)
        if not config:
            print("ERROR: Failed to load config. Check config.json.",
                  file=sys.stderr)
            sys.exit(1)

        redirect = Redirect(config, config_path)
        redirect.main_menu()
        pygame.quit()


if __name__ == "__main__":
    main()
