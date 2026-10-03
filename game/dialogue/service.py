"""Runtime loader for writer-authored dialogue in data/dialogue/."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from game.state import MAX_DAYS


@dataclass(frozen=True)
class DialogueLine:
    speaker: str
    text: str


@dataclass(frozen=True)
class DialogueEvent:
    id: str
    day: int
    trigger: str
    lines: tuple[DialogueLine, ...]


class DialogueService(Protocol):
    def get_event(self, event_id: str) -> DialogueEvent: ...

    def get_events_for(self, trigger: str) -> tuple[DialogueEvent, ...]: ...


class JsonDialogueService:
    """Loads authored dialogue events from data/dialogue/day_*.json."""

    def __init__(self, dialogue_dir: Path | None = None) -> None:
        if dialogue_dir is None:
            dialogue_dir = Path(__file__).resolve().parents[2] / "data" / "dialogue"
        if not dialogue_dir.is_dir():
            raise FileNotFoundError(
                f"Dialogue data directory not found: {dialogue_dir}"
            )

        self._events: dict[str, DialogueEvent] = {}
        for path in sorted(dialogue_dir.glob("day_*.json")):
            self._load_file(path)

    def get_event(self, event_id: str) -> DialogueEvent:
        try:
            return self._events[event_id]
        except KeyError:
            raise KeyError(f"Dialogue event not found: {event_id}") from None

    def get_events_for(self, trigger: str) -> tuple[DialogueEvent, ...]:
        return tuple(
            event for event in self._events.values() if event.trigger == trigger
        )

    def get_events_for_day(self, day: int) -> tuple[DialogueEvent, ...]:
        return tuple(event for event in self._events.values() if event.day == day)

    def _load_file(self, path: Path) -> None:
        try:
            with path.open(encoding="utf-8") as file:
                data = json.load(file)
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid dialogue JSON in {path}: {error}") from error

        if not isinstance(data, dict):
            raise ValueError(f"Dialogue file must contain an object: {path}")
        day = data.get("day")
        raw_events = data.get("events")
        if not isinstance(day, int) or isinstance(day, bool) or day < 1:
            raise ValueError(f"Dialogue file needs a positive integer 'day': {path}")
        if day > MAX_DAYS:
            raise ValueError(
                f"Dialogue file day must be between 1 and {MAX_DAYS}: {path}"
            )
        if not isinstance(raw_events, list):
            raise ValueError(f"Dialogue file needs an 'events' list: {path}")

        for raw_event in raw_events:
            event = self._parse_event(raw_event, day, path)
            if event.id in self._events:
                raise ValueError(f"Duplicate dialogue event ID {event.id!r} in {path}")
            self._events[event.id] = event

    @staticmethod
    def _parse_event(raw_event: object, day: int, path: Path) -> DialogueEvent:
        if not isinstance(raw_event, dict):
            raise ValueError(f"Each dialogue event must be an object: {path}")
        event_id = raw_event.get("id")
        trigger = raw_event.get("trigger")
        raw_lines = raw_event.get("lines")
        if not isinstance(event_id, str) or not event_id.strip():
            raise ValueError(f"Dialogue event needs a non-empty 'id': {path}")
        if not isinstance(trigger, str) or not trigger.strip():
            raise ValueError(f"Dialogue event {event_id!r} needs a non-empty 'trigger'")
        if not isinstance(raw_lines, list) or not raw_lines:
            raise ValueError(f"Dialogue event {event_id!r} needs a non-empty 'lines' list")

        lines = []
        for raw_line in raw_lines:
            if not isinstance(raw_line, dict):
                raise ValueError(f"Lines in event {event_id!r} must be objects")
            speaker = raw_line.get("speaker")
            text = raw_line.get("text")
            if not isinstance(speaker, str) or not speaker.strip():
                raise ValueError(f"Lines in event {event_id!r} need a non-empty 'speaker'")
            if not isinstance(text, str) or not text.strip():
                raise ValueError(f"Lines in event {event_id!r} need non-empty 'text'")
            lines.append(DialogueLine(speaker=speaker, text=text))

        return DialogueEvent(
            id=event_id,
            day=day,
            trigger=trigger,
            lines=tuple(lines),
        )
