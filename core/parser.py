import json
import os
import sys
from typing import Any

VALID_KEYS = {
    "level",
    "width",
    "height",
    "difficulty",
    "points_per_pacgum",
    "points_per_super_pacgum",
    "points_per_ghost",
    "seed",
    "level_max_time",
    "cheat_mode",
    "super_time",
    "practice"
}

DEFAULTS: dict[str, Any] = {
    "level": 1,
    "width": 15,
    "height": 15,
    "difficulty": 1,
    "points_per_pacgum": 10,
    "points_per_super_pacgum": 50,
    "points_per_ghost": 200,
    "seed": 42,
    "level_max_time": 90,
    "cheat_mode": False,
    "super_time": 8,
    "practice": False,
}


def _strip_comments(text: str) -> str:
    """
    Remove comments from a JSON-like text.
    Lines beginning with '#' (after optional whitespace) are dropped.
    """
    cleaned: list[str] = []
    for raw in text.splitlines():
        if raw.lstrip().startswith("#"):
            continue
        idx = raw.find("//")
        if idx != -1:
            raw = raw[:idx]
        cleaned.append(raw)
    return "\n".join(cleaned)


def _is_int(
    value: Any,
    key: str,
    lo: int,
    hi: int,
    default: int,
) -> int:
    """
    Coerce value to an int in [lo, hi]; on failure return default.
    A warning is printed whenever the input is replaced or clamped.
    """
    try:
        n = int(value)
    except (TypeError, ValueError):
        print(f"WARNING: '{key}' is not an integer ({value!r}),"
              f" using default {default}\n", file=sys.stderr)
        return default
    if n < lo or n > hi:
        clamped = max(lo, min(hi, n))
        print(f"WARNING: '{key}' must be between {lo} and {hi}"
              f" ({n}), clamped to {clamped}\n", file=sys.stderr)
        return clamped
    return n


def _is_bool(value: Any, key: str, default: bool) -> bool:
    """
    Coerce value to a bool, accepting actual booleans and the strings
    'true' / 'false' (case-insensitive). Fallback to default otherwise.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        if value.lower() == "true":
            return True
        if value.lower() == "false":
            return False
    print(f"WARNING: '{key}' must be True or False ({value!r}),"
          f" using default {default}\n", file=sys.stderr)
    return default


def parser(file: str) -> dict[str, Any]:
    """
    Load and validate the configuration file.

    Lines starting with '#' and trailing '//' comments are stripped before
    parsing. Missing or invalid values are clamped to safe defaults with a
    warning so the game can always start.
    """
    try:
        with open(file, "r", encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        print(f"ERROR: Config file not found: {file}\n", file=sys.stderr)
        return {}
    except OSError as e:
        print(f"ERROR: Cannot read config file '{file}': {e}\n",
              file=sys.stderr)
        return {}

    try:
        config_raw = json.loads(_strip_comments(text))
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in '{file}': {e}\n", file=sys.stderr)
        return {}

    if not isinstance(config_raw, dict):
        print(f"ERROR: Config root must be a JSON object in '{file}'\n",
              file=sys.stderr)
        return {}

    # Keep only valid keys; warn on unknown ones, ignore them silently
    # against the spec wording.
    config: dict[str, Any] = {}
    for key, value in config_raw.items():
        if key in VALID_KEYS:
            config[key] = value
        else:
            print(f"WARNING: Unknown key '{key}' ignored\n", file=sys.stderr)

    # Warn for missing keys; the default will be used.
    for missing in VALID_KEYS - set(config.keys()):
        print(f"WARNING: Missing config key '{missing}',"
              f" using default {DEFAULTS[missing]!r}\n", file=sys.stderr)

    # Validated values
    levels = _is_int(config.get("level", DEFAULTS["level"]),
                     "level", 1, 999, DEFAULTS["level"])
    width = _is_int(config.get("width", DEFAULTS["width"]),
                    "width", 3, 50, DEFAULTS["width"])
    height = _is_int(config.get("height", DEFAULTS["height"]),
                     "height", 3, 50, DEFAULTS["height"])
    difficulty = _is_int(
        config.get("difficulty", DEFAULTS["difficulty"]),
        "difficulty", 1, 5, DEFAULTS["difficulty"])
    points_per_pacgums = _is_int(
        config.get("points_per_pacgum", DEFAULTS["points_per_pacgum"]),
        "points_per_pacgum", 0, 999, DEFAULTS["points_per_pacgum"])
    points_per_super_pacgum = _is_int(
        config.get("points_per_super_pacgum",
                   DEFAULTS["points_per_super_pacgum"]),
        "points_per_super_pacgum", 0, 999,
        DEFAULTS["points_per_super_pacgum"])
    points_per_ghost = _is_int(
        config.get("points_per_ghost", DEFAULTS["points_per_ghost"]),
        "points_per_ghost", 0, 999, DEFAULTS["points_per_ghost"])
    # Seed has no range constraint; just coerce to int.
    try:
        seed = int(config.get("seed", DEFAULTS["seed"]))
    except (TypeError, ValueError):
        print(f"WARNING: 'seed' is not an integer"
              f" ({config.get('seed')!r}), using default"
              f" {DEFAULTS['seed']}\n", file=sys.stderr)
        seed = DEFAULTS["seed"]
    time = _is_int(
        config.get("level_max_time", DEFAULTS["level_max_time"]),
        "level_max_time", 1, 999, DEFAULTS["level_max_time"])
    super_time = _is_int(
        config.get("super_time", DEFAULTS["super_time"]),
        "super_time", 0, 999, DEFAULTS["super_time"])
    cheat = _is_bool(
        config.get("cheat_mode", DEFAULTS["cheat_mode"]),
        "cheat_mode", DEFAULTS["cheat_mode"])
    practice = _is_bool(
        config.get("practice", DEFAULTS["practice"]),
        "practice", DEFAULTS["practice"])

    files: dict[int, str] = {
        1: "scores/1/highscores.json",
        2: "scores/2/highscores.json",
        3: "scores/3/highscores.json",
        4: "scores/4/highscores.json",
        5: "scores/5/highscores.json"
    }
    filename = files.get(difficulty)

    # Check scores file: create it (with empty list) if missing,
    # error if not accessible
    if filename is not None:
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            if not os.path.exists(filename):
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump([], f)
            else:
                with open(filename, "r+", encoding="utf-8") as f:
                    pass
        except OSError as e:
            print(f"ERROR: Cannot access scores file '{filename}': {e}\n",
                  file=sys.stderr)
            return {}

    config_final = {
        "highscore_filename": filename,
        "level": levels,
        "width": width,
        "height": height,
        "difficulty": difficulty,
        "points_per_pacgum": points_per_pacgums,
        "points_per_super_pacgum": points_per_super_pacgum,
        "points_per_ghost": points_per_ghost,
        "seed": seed,
        "level_max_time": time,
        "cheat_mode": cheat,
        "super_time": super_time,
        "practice": practice
    }
    return config_final
