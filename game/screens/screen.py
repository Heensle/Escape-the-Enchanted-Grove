from enum import Enum, auto
from typing import Protocol

import pygame


class ScreenId(Enum):
    TITLE = auto()
    GROVE = auto()
    INTERACTION = auto()
    LOCK_BREAK = auto()
    EPILOGUE = auto()


class ScreenView(Protocol):
    def handle_event(self, event: pygame.event.Event) -> None: ...

    def update(self, delta_seconds: float) -> ScreenId | None: ...

    def draw(self, surface: pygame.Surface) -> None: ...

    def resize(self, size: tuple[int, int]) -> None: ...
