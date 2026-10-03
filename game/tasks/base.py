from dataclasses import dataclass

from game.state import Location


@dataclass(frozen=True)
class TaskDefinition:
    location: Location
    title: str
    elf_path: str
    fae_path: str
