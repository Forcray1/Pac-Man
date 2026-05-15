import os
import sys

from core.parser import parser
from display.pygame_viewer import PygameViewer


def main() -> None:
    if len(sys.argv) != 2:
        return
    else:
        config_file = f"config/{sys.argv[1]}"
        config_path = os.path.join(os.path.dirname(__file__), config_file)
        config = parser(config_path)
        if not config:
            print("ERROR: Failed to load config. Check config.json.",
                  file=sys.stderr)
            sys.exit(1)

        viewer: PygameViewer
        viewer = PygameViewer(config)
        viewer.display()


if __name__ == "__main__":
    main()
