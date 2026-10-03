from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DailyTask:
    id: str
    day: int
    target: str
    giver: str | None
    label: str
    choice_title: str
    description: str


DAILY_TASKS = (
    DailyTask(
        id="repair_roof",
        day=2,
        target="hammer",
        giver="elf",
        label="Fix the roof with the hammer",
        choice_title="Help the Elf: repair the roof",
        description="Start the roof jigsaw task.",
    ),
    DailyTask(
        id="break_gate_lock",
        day=2,
        target="hammer",
        giver="fae",
        label="Break the gate lock with the hammer",
        choice_title="Help the Fae: break the gate lock",
        description="Use the hammer on the gate lock.",
    ),
    DailyTask(
        id="clean_pond",
        day=3,
        target="net",
        giver="elf",
        label="Clean the pond with the net",
        choice_title="Help the Elf: clean the pond",
        description="Clear the pond using the net.",
    ),
    DailyTask(
        id="retrieve_key",
        day=3,
        target="net",
        giver="fae",
        label="Retrieve the key with the net",
        choice_title="Help the Fae: retrieve the key",
        description="Pull the key from the pond.",
    ),
    DailyTask(
        id="garden_maze",
        day=4,
        target="garden",
        giver=None,
        label="Go through the garden maze",
        choice_title="Go through the garden maze",
        description="Find your way through the garden maze.",
    ),
)


def tasks_for_day(day: int) -> tuple[DailyTask, ...]:
    return tuple(task for task in DAILY_TASKS if task.day == day)


def tasks_for_target(day: int, target: str) -> tuple[DailyTask, ...]:
    return tuple(
        task for task in tasks_for_day(day) if task.target == target
    )


def get_task(task_id: str) -> DailyTask:
    for task in DAILY_TASKS:
        if task.id == task_id:
            return task
    raise KeyError(f"Unknown daily task: {task_id!r}")
