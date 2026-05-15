import json
import sys

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


def parser(file: str) -> dict:
    try:
        with open(file, "r") as f:
            config_raw = json.load(f)
    except FileNotFoundError:
        print("ERROR: File not found", file=sys.stderr)
        return {}
    except Exception as e:
        print(f"ERROR: Error while parsing the file {file}:\n{e}",
              file=sys.stderr)
        return {}
    missing_keys = VALID_KEYS - set(config_raw.keys())
    if missing_keys:
        print(f"Missing config key(s): {missing_keys}",
              file=sys.stderr)
        return {}
    config = {}
    for key, value in config_raw.items():
        if key in VALID_KEYS:
            config[key] = value
    # Check value of level
    levels = config["level"]
    try:
        n = int(levels)
        if n < 1:
            raise ValueError
    except Exception:
        print(f"ERROR: The level amount has to be a positive"
              f"integer ({levels})",
              file=sys.stderr)
        return {}
    # Check value of width
    try:
        width = int(config["width"])
        if width < 3:
            raise ValueError
    except Exception:
        print(f"ERROR: The width has to be a positive integer greater"
              f" than 3 ({config['width']})",
              file=sys.stderr)
        return {}
    # Check value of height
    try:
        height = int(config["height"])
        if height < 3:
            raise ValueError
    except Exception:
        print(f"ERROR: The height has to be a positive integer greater"
              f" than 3 ({config['height']})",
              file=sys.stderr)
        return {}
    # Check value of difficulty
    try:
        difficulty = int(config["difficulty"])
        if difficulty < 1 or difficulty > 5:
            raise ValueError
    except Exception:
        print(f"ERROR: The difficulty has to be a positive integer between"
              f" 1 (normal) and 5 (really hard) ({config['difficulty']})",
              file=sys.stderr)
        return {}
    # Check value of points_per_pacgum
    try:
        points_per_pacgums = int(config["points_per_pacgum"])
        if points_per_pacgums < 0:
            raise ValueError
    except Exception:
        print("ERROR: The points_per_pacgum has to be a positive integer"
              " or zero",
              file=sys.stderr)
        return {}
    # Check value of points_per_super_pacgum
    try:
        points_per_super_pacgum = int(config["points_per_super_pacgum"])
        if points_per_super_pacgum < 0:
            raise ValueError
    except Exception:
        print(f"ERROR: The points per super pacgum has to be a positive "
              f"integer or zero ({config['points_per_super_pacgum']})",
              file=sys.stderr)
        return {}
    # Check value of points_per_ghost
    try:
        points_per_ghost = int(config["points_per_ghost"])
        if points_per_ghost < 0:
            raise ValueError
    except Exception:
        print(f"ERROR: The points per ghost has to be a positive "
              f"integer or zero ({config['points_per_ghost']})",
              file=sys.stderr)
        return {}
    # Check value of seed
    try:
        seed = int(config["seed"])
    except Exception:
        print(f"ERROR: The seed isn't valid ({config['seed']})",
              file=sys.stderr)
        return {}
    # Check value of time
    try:
        time = int(config["level_max_time"])
    except Exception:
        print(f"ERROR: The time per level must be a positive integer "
              f"({config['time']})",
              file=sys.stderr)
        return {}
    # Check value of cheat mode
    cheat = config["cheat_mode"]
    if isinstance(cheat, str):
        if cheat.lower() == "true":
            cheat = True
        elif cheat.lower() == "false":
            cheat = False
        else:
            print(f"ERROR: The cheat mode have to be either "
                  f"'True' or 'False' ({cheat})",
                  file=sys.stderr)
            return {}
    elif not isinstance(cheat, bool):
        print(f"ERROR: The cheat mode have to be either "
              f"'True' or 'False' ({cheat})",
              file=sys.stderr)
        return {}
    # Check value of super time
    try:
        super_time = int(config["super_time"])
        if super_time < 0:
            raise ValueError
    except Exception:
        print(f"ERROR: The time for super mode has to be a positive integer or"
              f"zero ({config['super_time']})", file=sys.stderr)
        return {}

    # Check value of practice
    practice = config.get("practice", "False")
    files: dict = {
        1: "scores/1/highscores.json",
        2: "scores/2/highscores.json",
        3: "scores/3/highscores.json",
        4: "scores/4/highscores.json",
        5: "scores/5/highscores.json"
    }
    filename = files.get(difficulty)

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
