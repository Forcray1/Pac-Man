"""Temporary launcher — opens the config editor screen in isolation."""
import json
import sys

import pygame

sys.path.insert(0, ".")
from core.config import edited_config

CONFIG_PATH = "config/config.json"


def main() -> None:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        config = json.load(f)

    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("Config Editor")

    editor = edited_config(screen)
    updated = editor.draw_window(config)

    pygame.quit()

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(updated, f, indent="\t")
    print("Config saved.")


if __name__ == "__main__":
    main()
