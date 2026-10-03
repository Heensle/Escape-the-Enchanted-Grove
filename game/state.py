from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class Location(Enum):
    HOUSE = auto()
    POND = auto()
    GARDEN = auto()


class Choice(Enum):
    HELP_ELF = auto()
    HELP_FAE = auto()


class HouseAction(Enum):
    REPAIR_ROOF = auto()
    BREAK_LOCK = auto()


class PondAction(Enum):
    CLEAN_POND_AND_SORT_WASTE = auto()
    RETRIEVE_KEY = auto()


class GardenEnding(Enum):
    ELF = auto()
    FAE = auto()


@dataclass(frozen=True)
class GameState:
    choices: tuple[tuple[Location, Choice], ...] = ()
    house_action: HouseAction | None = None
    pond_action: PondAction | None = None
    garden_ending: GardenEnding | None = None

    @property
    def destructive_choice_count(self) -> int:
        return sum(choice is Choice.HELP_FAE for _, choice in self.choices)

    @property
    def broken_locks(self) -> frozenset[Location]:
        return frozenset(
            location
            for location, choice in self.choices
            if choice is Choice.HELP_FAE
        )

    @property
    def completed_locations(self) -> frozenset[Location]:
        return frozenset(location for location, _ in self.choices)
