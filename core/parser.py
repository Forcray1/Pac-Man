import json
import os
import sys
from typing import Any


class ConfigParser:
    """
    Load and validate the game configuration file.
    """

    SCHEMA: dict[str, dict[str, Any]] = {
        "level":                   {"type": "int",  "min": 1, "max": 999,
                                    "default": 1},
        "width":                   {"type": "int",  "min": 3, "max": 50,
                                    "default": 15},
        "height":                  {"type": "int",  "min": 3, "max": 50,
                                    "default": 15},
        "difficulty":              {"type": "int",  "min": 1, "max": 5,
                                    "default": 1},
        "points_per_pacgum":       {"type": "int",  "min": 0, "max": 999,
                                    "default": 10},
        "points_per_super_pacgum": {"type": "int",  "min": 0, "max": 999,
                                    "default": 50},
        "points_per_ghost":        {"type": "int",  "min": 0, "max": 999,
                                    "default": 200},
        "seed":                    {"type": "int",  "min": 1,
                                    "default": 42},
        "level_max_time":          {"type": "int",  "min": 1, "max": 999,
                                    "default": 90},
        "cheat_mode":              {"type": "bool", "default": False},
        "super_time":              {"type": "int",  "min": 0, "max": 999,
                                    "default": 8},
        "practice":                {"type": "bool", "default": False},
    }

    # Derived from the schema so they can never drift out of sync.
    VALID_KEYS = set(SCHEMA)
    DEFAULTS: dict[str, Any] = {k: s["default"] for k, s in SCHEMA.items()}

    # Highscore file per difficulty level.
    SCORE_FILES = {d: f"scores/{d}/highscores.json" for d in range(1, 6)}

    def __init__(self, file: str) -> None:
        """
        Prepare to parse *file* (path to the JSON config).
        """
        self.file = file

    @staticmethod
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

    @staticmethod
    def _coerce_int(
        value: Any,
        key: str,
        default: int,
        lo: int | None = None,
        hi: int | None = None,
    ) -> int:
        """
        Coerce value to an int. When lo/hi are given, clamp into [lo, hi].
        On failure return default. A warning is printed when a value is
        replaced or clamped.
        """
        try:
            n = int(value)
        except (TypeError, ValueError):
            print(f"WARNING: '{key}' is not an integer ({value!r}),"
                  f" using default {default}\n", file=sys.stderr)
            return default
        if lo is not None and hi is not None and (n < lo or n > hi):
            clamped = max(lo, min(hi, n))
            print(f"WARNING: '{key}' must be between {lo} and {hi}"
                  f" ({n}), clamped to {clamped}\n", file=sys.stderr)
            return clamped
        return n

    @staticmethod
    def _coerce_bool(value: Any, key: str, default: bool) -> bool:
        """
        Coerce value to a bool, accepting actual booleans and the strings
        'true' / 'false'. Fallback to default otherwise.
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

    @classmethod
    def _validate(cls, key: str, value: Any) -> Any:
        """
        Validate a single raw value against its schema spec.
        """
        spec = cls.SCHEMA[key]
        if spec["type"] == "bool":
            return cls._coerce_bool(value, key, spec["default"])
        return cls._coerce_int(
            value, key, spec["default"], spec.get("min"), spec.get("max"))

    @classmethod
    def _ensure_scores_file(cls, difficulty: int) -> str | None:
        """
        Return the highscore file for difficulty, creating it (with an
        empty list) if missing. Returns None if the difficulty has no mapped
        file, or raises OSError if the file cannot be accessed.
        """
        filename = cls.SCORE_FILES.get(difficulty)
        if filename is None:
            return None
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        if not os.path.exists(filename):
            with open(filename, "w", encoding="utf-8") as f:
                json.dump([], f)
        else:
            with open(filename, "r+", encoding="utf-8"):
                pass
        return filename

    def parse(self) -> dict[str, Any]:
        """
        Load and validate the configuration file.

        Lines starting with '#' and trailing '//' comments are stripped
        before parsing. Missing or invalid values are clamped to safe
        defaults with a warning so the game can always start. Returns an
        empty dict on a fatal error (unreadable file, invalid JSON, etc.).
        """
        try:
            with open(self.file, "r", encoding="utf-8") as f:
                text = f.read()
        except FileNotFoundError:
            print(f"ERROR: Config file not found: {self.file}\n",
                  file=sys.stderr)
            return {}
        except OSError as e:
            print(f"ERROR: Cannot read config file '{self.file}': {e}\n",
                  file=sys.stderr)
            return {}

        try:
            config_raw = json.loads(self._strip_comments(text))
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON in '{self.file}': {e}\n",
                  file=sys.stderr)
            return {}

        if not isinstance(config_raw, dict):
            print("ERROR: Config root must be a JSON object in"
                  f" '{self.file}'\n", file=sys.stderr)
            return {}

        # Warn (and drop) unknown keys.
        for key in config_raw:
            if key not in self.VALID_KEYS:
                print(f"WARNING: Unknown key '{key}' ignored\n",
                      file=sys.stderr)

        # Warn for missing keys; the default will be used.
        for missing in self.VALID_KEYS - config_raw.keys():
            print(f"WARNING: Missing config key '{missing}',"
                  f" using default {self.DEFAULTS[missing]!r}\n",
                  file=sys.stderr)

        # Validate every known key
        config_final: dict[str, Any] = {
            key: self._validate(key, config_raw.get(key, self.DEFAULTS[key]))
            for key in self.SCHEMA
        }

        # Resolve and prepare the per-difficulty highscore file.
        try:
            config_final["highscore_filename"] = self._ensure_scores_file(
                config_final["difficulty"])
        except OSError as e:
            print(f"ERROR: Cannot access scores file: {e}\n", file=sys.stderr)
            return {}

        return config_final
