from __future__ import annotations

import pygame

from game.dialogue.service import DialogueEvent
from game.screens.screen import ScreenId


class InteractionScreen:
    def __init__(self, size: tuple[int, int]) -> None:
        self.size = size
        self._events: tuple[DialogueEvent, ...] = ()
        self._event_index = 0
        self._line_index = 0
        self._destination: ScreenId | None = None
        self._pending_screen: ScreenId | None = None
        self._completed_event_ids: tuple[str, ...] = ()

    def start(
        self,
        events: tuple[DialogueEvent, ...],
        destination: ScreenId,
    ) -> None:
        if not events:
            raise ValueError("A dialogue screen needs at least one event.")
        self._events = events
        self._event_index = 0
        self._line_index = 0
        self._destination = destination
        self._pending_screen = None
        self._completed_event_ids = ()

    def handle_event(self, event: pygame.event.Event) -> None:
        if (
            self._destination is not None
            and event.type == pygame.KEYDOWN
            and event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e)
        ):
            self._advance()

    def _advance(self) -> None:
        line_count = len(self._events[self._event_index].lines)
        self._line_index += 1
        if self._line_index < line_count:
            return
        self._event_index += 1
        self._line_index = 0
        if self._event_index == len(self._events):
            self._completed_event_ids = tuple(event.id for event in self._events)
            self._pending_screen = self._destination
            self._destination = None

    def consume_completed_event_ids(self) -> tuple[str, ...]:
        completed_event_ids = self._completed_event_ids
        self._completed_event_ids = ()
        return completed_event_ids

    def update(self, _delta_seconds: float) -> ScreenId | None:
        _ = _delta_seconds
        destination = self._pending_screen
        self._pending_screen = None
        return destination

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((19, 34, 28))
        if self._destination is None:
            return

        event = self._events[self._event_index]
        line = event.lines[self._line_index]
        width, height = surface.get_size()
        padding = max(20, round(min(width, height) * 0.045))
        panel_height = max(150, round(height * 0.42))
        panel = pygame.Rect(
            padding,
            height - panel_height - padding,
            width - 2 * padding,
            panel_height,
        )
        pygame.draw.rect(surface, (24, 39, 31), panel, border_radius=12)
        pygame.draw.rect(
            surface,
            (177, 163, 115),
            panel,
            width=max(1, round(min(width, height) * 0.003)),
            border_radius=12,
        )

        scale = max(0.7, min(1.4, min(width / 1280, height / 720)))
        speaker_font = pygame.font.Font(None, max(24, round(34 * scale)))
        text_font = pygame.font.Font(None, max(22, round(30 * scale)))
        hint_font = pygame.font.Font(None, max(18, round(23 * scale)))
        speaker = speaker_font.render(line.speaker.title(), True, (237, 212, 146))
        surface.blit(speaker, (panel.left + padding, panel.top + padding // 2))

        text_x = panel.left + padding
        text_y = panel.top + padding // 2 + speaker.get_height() + 8
        max_text_width = panel.width - 2 * padding
        for wrapped in self._wrap_text(line.text, text_font, max_text_width):
            rendered = text_font.render(wrapped, True, (242, 237, 219))
            surface.blit(rendered, (text_x, text_y))
            text_y += rendered.get_height() + 3

        hint = hint_font.render(
            "Press E, Enter, or Space to continue",
            True,
            (175, 190, 165),
        )
        surface.blit(
            hint,
            hint.get_rect(
                bottomright=(panel.right - padding // 2, panel.bottom - padding // 3)
            ),
        )

    @staticmethod
    def _wrap_text(text: str, font: pygame.font.Font, width: int) -> tuple[str, ...]:
        words = text.split()
        lines: list[str] = []
        current_line = ""
        for word in words:
            candidate = f"{current_line} {word}".strip()
            if current_line and font.size(candidate)[0] > width:
                lines.append(current_line)
                current_line = word
            else:
                current_line = candidate
        if current_line:
            lines.append(current_line)
        return tuple(lines)

    def resize(self, size: tuple[int, int]) -> None:
        self.size = size
