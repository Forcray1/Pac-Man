"""Temp launcher — skips the main menu and starts the game directly."""
import os
import sys

import pygame

# Make sure the project root is on the path
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

from core.parser import parser
from display.pygame_viewer import PygameViewer

CONFIG_PATH = os.path.join(_ROOT, "config", "config.json")

pygame.init()
config = parser(CONFIG_PATH)
if not config:
    print("ERROR: Failed to load config.json", file=sys.stderr)
    sys.exit(1)

viewer = PygameViewer(config)
viewer.display()
pygame.quit()
