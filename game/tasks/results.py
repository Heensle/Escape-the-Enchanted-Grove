from dataclasses import dataclass
from enum import Enum, auto

from game.state import GardenEnding, HouseAction, Location, PondAction


class TaskOutcome(Enum):
    COMPLETED = auto()
    CANCELLED = auto()


@dataclass(frozen=True)
class TaskResult:
    location: Location
    outcome: TaskOutcome
    action: HouseAction | PondAction | GardenEnding | None = None
