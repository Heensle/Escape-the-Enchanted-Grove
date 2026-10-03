from dataclasses import dataclass
from typing import Protocol

from game.state import Choice


@dataclass(frozen=True)
class DialogueContext:
    character: str
    situation: str
    choice: Choice | None = None


class DialogueService(Protocol):
    def get_line(self, context: DialogueContext) -> str: ...


class AuthoredDialogueService:
    def get_line(self, context: DialogueContext) -> str:
        if context.character.casefold() == "elf":
            return "The Elf watches you carefully, waiting to see what you will do."
        if context.character.casefold() == "fae":
            return "The Fae looks toward the grove's locked gates."
        return "The grove falls quiet."
