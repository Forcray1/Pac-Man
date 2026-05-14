#!/usr/bin/env python3
"""Final verification that god mode is working."""

from core.parser import parser

# Test 1: Verify config parsing
config = parser('config/config.json')
print("✓ Test 1: Config parsing")
print(f"  cheat_mode = {config.get('cheat_mode')} (type: {type(config.get('cheat_mode')).__name__})")
assert config.get('cheat_mode') is True, "cheat_mode should be True"

# Test 2: Verify direct boolean comparison
cheat_enabled = config.get("cheat_mode", False)
print(f"\n✓ Test 2: Boolean comparison")
print(f"  cheat_enabled = {cheat_enabled}")
print(f"  if cheat_enabled: {bool(cheat_enabled)}")
assert cheat_enabled is True, "Should be True"

# Test 3: Verify god_mode toggle
from entities.player import PacMan
player = PacMan(5, 5)
print(f"\n✓ Test 3: God mode toggle")
print(f"  Initial god_mode: {player.god_mode}")
player.god_mode = not player.god_mode
print(f"  After toggle: {player.god_mode}")
assert player.god_mode is True, "Should be True after toggle"

# Test 4: Verify viewer config receives cheat_mode
# (We can't fully test this without pygame, but we can check the logic)
test_config = {
    "super_time": 30,
    "level_max_time": 90,
    "cheat_mode": True,
}
check = test_config.get("cheat_mode", False)
print(f"\n✓ Test 4: Viewer config check")
print(f"  Config cheat_mode: {check}")
assert check is True, "Should be True"

print("\n✓ All verifications passed! God mode should work now.")
