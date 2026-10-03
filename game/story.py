from dataclasses import replace
from enum import Enum, auto

from game.tasks.results import TaskOutcome, TaskResult
from game.state import (
    Choice,
    GameState,
    GardenEnding,
    HouseAction,
    Location,
    PondAction,
)


class Ending(Enum):
    GOOD = auto()
    NEUTRAL = auto()
    BAD = auto()


def record_choice(
    state: GameState,
    location: Location,
    choice: Choice,
) -> GameState:
    if location in state.completed_locations:
        raise ValueError(f"A choice has already been recorded for {location.name}.")
    return replace(state, choices=(*state.choices, (location, choice)))


def determine_ending(state: GameState) -> Ending | None:
    if len(state.completed_locations) != len(Location):
        return None
    if state.destructive_choice_count == len(Location):
        return Ending.BAD
    if state.destructive_choice_count > 0:
        return Ending.NEUTRAL
    return Ending.GOOD


def apply_task_result(
    state: GameState,
    result: TaskResult,
) -> GameState:
    if result.outcome is TaskOutcome.CANCELLED:
        return state

    outcome_fields = {
        HouseAction: "house_action",
        PondAction: "pond_action",
        GardenEnding: "garden_ending",
    }
    outcome_locations = {
        HouseAction: Location.HOUSE,
        PondAction: Location.POND,
        GardenEnding: Location.GARDEN,
    }
    if result.action is None:
        raise ValueError("A completed task must report its selected action.")
    action_type = type(result.action)
    if action_type not in outcome_fields:
        raise ValueError(f"Unsupported task action: {result.action!r}.")
    if outcome_locations[action_type] is not result.location:
        raise ValueError(
            f"{result.location.name} task cannot report {result.action!r}."
        )
    return replace(state, **{outcome_fields[action_type]: result.action})
