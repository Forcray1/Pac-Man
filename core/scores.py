from __future__ import annotations

import json


class ScoreManager:
    """
    Manages the top-10 highscores stored in a dedicated local JSON file.
    """

    def __init__(self, filename: str) -> None:
        self.filename: str = filename
        self.scores: list[tuple[str, int]] = []
        self.load()

    def load(self) -> None:
        """
        Load scores from the JSON file. Silently resets to empty on error.
        """
        entries: list[tuple[str, int]] = []
        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                data = json.load(f)
            for entry in data:
                try:
                    name = str(entry["name"])
                    score = int(entry["score"])
                    if score >= 0:
                        entries.append((name, score))
                except (KeyError, ValueError, TypeError):
                    continue
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        self.scores = self._top(entries)

    def save(self) -> None:
        """
        Write the current top scores to the JSON file.
        """
        data = [{"name": n, "score": s} for n, s in self.scores]
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent="\t", ensure_ascii=False)

    def qualifies(self, score: int) -> bool:
        """
        Return True if *score* earns a place in the top 10.
        """
        if len(self.scores) < 10:
            return True
        return score >= self.scores[-1][1]

    def check_value(self, score: int) -> bool:
        if score is None:
            return False
        elif isinstance(score, bool):
            return False
        elif not isinstance(score, int):
            return False
        elif score < 0:
            return False
        else:
            return True

    def check_name(self, username: str) -> bool:
        if len(username) > 10:
            return False
        if not username.isalpha():
            return False
        return True

    def add(self, name: str, score: int) -> bool:
        """
        Insert (name, score) into the leaderboard if it qualifies, then save.
        The list is trimmed to the top 10 entries.
        """
        if not self.check_name(name):
            return False
        if not self.qualifies(score):
            return False
        self.scores.append((name, score))
        self.scores = self._top(self.scores)
        self.save()
        return True

    def top_scores(self) -> list[tuple[str, int]]:
        """
        Return a copy of the current top-10 list (descending).
        """
        return list(self.scores)

    @staticmethod
    def _top(entries: list[tuple[str, int]]) -> list[tuple[str, int]]:
        """
        Sort descending by score and keep at most 10 entries.
        """
        return sorted(entries, key=lambda e: e[1], reverse=True)[:10]
