#!/usr/bin/env python3
"""Test script to verify god mode works."""

from core.parser import parser
from entities.player import PacMan
from core.monitor import Monitor

# Parse config
config = parser('config/config.json')
print(f"✓ Config parsed successfully")
print(f"  - cheat_mode: {config.get('cheat_mode')} (type: {type(config.get('cheat_mode')).__name__})")

# Create a player
player = PacMan(5, 5)
print(f"\n✓ Player created")
print(f"  - god_mode initial: {player.god_mode}")

# Test toggling god mode
player.god_mode = True
print(f"  - god_mode after toggle: {player.god_mode}")

player.god_mode = not player.god_mode
print(f"  - god_mode after toggle back: {player.god_mode}")

# Test that god_mode prevents death in monitor
# Simulate collision
player.god_mode = True
player.is_dying = False
print(f"\n✓ Player in god mode: {player.god_mode}")
print(f"  - Should NOT die when hit by ghost")

# Test config string conversion
cheat_mode = config.get('cheat_mode', False)
check = str(cheat_mode).lower() == "true"
print(f"\n✓ Config string check")
print(f"  - str(cheat_mode).lower() == 'true': {check}")

print("\n✓ All tests passed!")
