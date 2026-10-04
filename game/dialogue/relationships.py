from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from game.state import GardenEnding, HouseAction, Location, PondAction
from game.tasks.results import TaskOutcome, TaskResult

CHARACTERS = ("elf", "fae")
INITIAL_SCORES = {"elf": -5, "fae": 5}
TASK_SCORE_CHANGE = 3


class RelationshipStore:
    """Persists per-character relationship scores outside the game install."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or self._default_path()
        self._scores = dict(INITIAL_SCORES)
        if self.path.exists():
            self._load()

    @staticmethod
    def _default_path() -> Path:
        if os.name == "nt":
            base = Path(
                os.environ.get("LOCALAPPDATA")
                or Path.home() / "AppData" / "Local"
            )
        else:
            base = Path(
                os.environ.get("XDG_DATA_HOME")
                or Path.home() / ".local" / "share"
            )
        return base / "EscapeTheEnchantedGrove" / "relationships.json"

    def score(self, character: str) -> int:
        return self._scores[self._normalize_character(character)]

    def reset_to_initial_scores(self) -> None:
        scores = dict(INITIAL_SCORES)
        self._save(scores)
        self._scores = scores

    def apply_delta(self, character: str, delta: int) -> int:
        normalized = self._normalize_character(character)
        if (
            not isinstance(delta, int)
            or isinstance(delta, bool)
            or delta not in (-1, 1)
        ):
            raise ValueError("A conversation relationship change must be -1 or +1.")
        return self._change_score(normalized, delta)

    def record_task_result(self, result: TaskResult) -> int:
        character, location = self._character_and_location_for_action(result.action)
        if result.location is not location:
            raise ValueError(
                f"{result.location.name} task cannot update the "
                f"{character.title()}'s relationship using {result.action!r}."
            )
        if result.outcome is TaskOutcome.COMPLETED:
            delta = TASK_SCORE_CHANGE
        elif result.outcome is TaskOutcome.CANCELLED:
            delta = -TASK_SCORE_CHANGE
        else:
            raise ValueError(f"Unsupported task outcome: {result.outcome!r}.")
        return self._change_score(character, delta)

    def _change_score(self, character: str, delta: int) -> int:
        score = self._scores[character] + delta
        updated = dict(self._scores)
        updated[character] = score
        self._save(updated)
        self._scores = updated
        return score

    def _load(self) -> None:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(f"Could not read relationship save {self.path}: {error}") from error
        if not isinstance(data, dict) or not isinstance(data.get("relationships"), dict):
            raise ValueError(f"Invalid relationship save format: {self.path}")
        relationships = data["relationships"]
        scores = {}
        for character in CHARACTERS:
            score = relationships.get(character, INITIAL_SCORES[character])
            if not isinstance(score, int) or isinstance(score, bool):
                raise ValueError(
                    f"Invalid relationship score for {character!r} in {self.path}"
                )
            scores[character] = score
        self._scores = scores

    def _save(self, scores: dict[str, int]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                delete=False,
            ) as file:
                temporary_path = Path(file.name)
                json.dump({"relationships": scores}, file, indent=2)
                file.write("\n")
            os.replace(temporary_path, self.path)
        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()

    @staticmethod
    def _character_and_location_for_action(
        action: HouseAction | PondAction | GardenEnding | None,
    ) -> tuple[str, Location]:
        characters = {
            HouseAction.REPAIR_ROOF: ("elf", Location.HOUSE),
            HouseAction.BREAK_LOCK: ("fae", Location.HOUSE),
            PondAction.CLEAN_POND_AND_SORT_WASTE: ("elf", Location.POND),
            PondAction.RETRIEVE_KEY: ("fae", Location.POND),
            GardenEnding.ELF: ("elf", Location.GARDEN),
            GardenEnding.FAE: ("fae", Location.GARDEN),
        }
        try:
            return characters[action]
        except KeyError:
            raise ValueError(
                "A task result needs its selected character path to update "
                "relationship points."
            ) from None

    @staticmethod
    def _normalize_character(character: str) -> str:
        normalized = character.lower()
        if normalized not in CHARACTERS:
            raise ValueError(f"Unsupported relationship character: {character!r}")
        return normalized
