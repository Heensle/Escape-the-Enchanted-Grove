from __future__ import annotations

import logging
from concurrent.futures import Future
from dataclasses import dataclass
from typing import Callable

import pygame

from game.dialogue.gemini import GameContext, GeminiReply
from game.dialogue.service import DialogueEvent
from game.screens.screen import ScreenId


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class ConversationMessage:
    day: int
    speaker: str
    text: str


class InteractionScreen:
    MAX_INPUT_LENGTH = 1000

    def __init__(self, size: tuple[int, int]) -> None:
        self.size = size
        self._events: tuple[DialogueEvent, ...] = ()
        self._event_index = 0
        self._line_index = 0
        self._destination: ScreenId | None = None
        self._pending_screen: ScreenId | None = None
        self._completed_event_ids: tuple[str, ...] = ()
        self._completed_conversation_character: str | None = None
        self._conversation_character: str | None = None
        self._conversation_has_spoken = False
        self._relationship_score = 0
        self._submit_turn: (
            Callable[
                [
                    str,
                    str,
                    int,
                    tuple[tuple[str, str], ...],
                    GameContext | None,
                ],
                Future[GeminiReply],
            ]
            | None
        ) = None
        self._apply_relationship_delta: Callable[[str, int], int] | None = None
        self._future: Future[GeminiReply] | None = None
        self._close_requested = False
        self._input_text = ""
        self._history_by_character: dict[str, list[ConversationMessage]] = {}
        self._history: list[ConversationMessage] = []
        self._history_scroll = 0
        self._conversation_day = 1
        self._status = ""
        game_context = self._build_game_context(character)


    @property
    def is_conversation(self) -> bool:
        return self._conversation_character is not None

    def start(
        self,
        events: tuple[DialogueEvent, ...],
        destination: ScreenId,
    ) -> None:
        if not events:
            raise ValueError("A dialogue screen needs at least one event.")
        if self._conversation_character is not None:
            pygame.key.stop_text_input()
        self._events = events
        self._event_index = 0
        self._line_index = 0
        self._destination = destination
        self._pending_screen = None
        self._completed_event_ids = ()
        self._completed_conversation_character = None
        self._conversation_character = None
        self._conversation_has_spoken = False
        self._future = None
        self._close_requested = False
        self._input_text = ""
        self._history = []
        self._status = ""
        self._game_context = None

    def handle_event(self, event: pygame.event.Event) -> None:
        if self._conversation_character is not None:
            self._handle_conversation_event(event)
            return
        if (
            self._destination is not None
            and event.type == pygame.KEYDOWN
            and event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e)
        ):
            self._advance()

    def start_conversation(
        self,
        character: str,
        relationship_score: int,
        submit_turn: Callable[
            [str, str, int, tuple[tuple[str, str], ...]],
            Future[GeminiReply],
        ],
        apply_relationship_delta: Callable[[str, int], int],
        destination: ScreenId,
        day_number: int = 1,
        game_context: GameContext | None = None,
    ) -> None:
        if character.lower() not in ("elf", "fae"):
            raise ValueError(f"Unsupported conversation character: {character!r}")
        if self._conversation_character is not None:
            pygame.key.stop_text_input()
        self._events = ()
        self._event_index = 0
        self._line_index = 0
        self._destination = destination
        self._pending_screen = None
        self._completed_event_ids = ()
        self._completed_conversation_character = None
        self._conversation_character = character.title()
        self._conversation_has_spoken = False
        self._relationship_score = relationship_score
        self._submit_turn = submit_turn
        self._apply_relationship_delta = apply_relationship_delta
        self._future = None
        self._close_requested = False
        self._input_text = ""
        character_key = character.lower()
        self._history = self._history_by_character.setdefault(character_key, [])
        self._history_scroll = 0
        self._conversation_day = day_number
        self._game_context = game_context
        self._status = "Type a message and press Enter to talk."
        pygame.key.start_text_input()

    def _handle_conversation_event(self, event: pygame.event.Event) -> None:
        if self._future is not None:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._close_requested = True
                self._status = (
                    "Finishing this reply before returning to the grove..."
                )
            return
        if event.type == pygame.TEXTINPUT:
            self._input_text = (
                self._input_text + event.text
            )[: self.MAX_INPUT_LENGTH]
            return
        if event.type == pygame.MOUSEWHEEL:
            self._history_scroll = min(
                max(0, self._history_scroll + event.y),
                max(0, len(self._history) - 1),
            )
            return
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            self._close_conversation()
        elif event.key == pygame.K_BACKSPACE:
            self._input_text = self._input_text[:-1]
        elif event.key == pygame.K_RETURN:
            if event.mod & pygame.KMOD_SHIFT:
                self._input_text += "\n"
                self._input_text = self._input_text[: self.MAX_INPUT_LENGTH]
            else:
                self._send_message()

    def _send_message(self) -> None:
        message = self._input_text.strip()
        if not message:
            self._status = "Type a message before sending."
            return
        character = self._conversation_character
        if character is None or self._submit_turn is None:
            raise RuntimeError("Conversation is not configured.")
        previous_messages = tuple(
            (entry.speaker, entry.text) for entry in self._history[-12:]
        )
        self._history.append(
            ConversationMessage(self._conversation_day, "You", message)
        )
        self._history_scroll = 0
        self._conversation_has_spoken = True
        self._input_text = ""
        if self._relationship_score <= -6:
            self._status = (
                f"The {character} grimaces while thinking..."
            )
        else:
            self._status = f"The {character} is thinking..."
        try:
            self._future = self._submit_turn(
                character.lower(),
                message,
                self._relationship_score,
                previous_messages,
                self._game_context,
            )
        except Exception as error:
            self._show_gemini_fallback(error)

    def _show_gemini_fallback(self, error: Exception) -> None:
        character = self._conversation_character
        if character is None:
            raise RuntimeError("Cannot show a fallback outside a conversation.")
        LOGGER.error(
            "Gemini dialogue failed for %s: %s",
            character,
            error,
            exc_info=(type(error), error, error.__traceback__),
        )
        self._history.append(
            ConversationMessage(
                self._conversation_day,
                character,
                f"The {character.lower()} has nothing to say to that.",
            )
        )
        self._history_scroll = 0
        self._status = "The conversation can continue."
        self._close_requested = False

    def _close_conversation(self) -> None:
        if self._conversation_character is None or self._future is not None:
            return
        if self._conversation_has_spoken:
            self._completed_conversation_character = (
                self._conversation_character.lower()
            )
        pygame.key.stop_text_input()
        self._pending_screen = self._destination
        self._destination = None
        self._conversation_character = None
        self._close_requested = False

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

    def consume_completed_conversation_character(self) -> str | None:
        character = self._completed_conversation_character
        self._completed_conversation_character = None
        return character

    def update(self, _delta_seconds: float) -> ScreenId | None:
        _ = _delta_seconds
        if self._future is not None and self._future.done():
            future = self._future
            self._future = None
            try:
                reply = future.result()
            except Exception as error:
                self._show_gemini_fallback(error)
            else:
                character = self._conversation_character
                if character is None or self._apply_relationship_delta is None:
                    raise RuntimeError("Conversation lost its relationship handler.")
                self._history.append(
                    ConversationMessage(self._conversation_day, character, reply.text)
                )
                self._history_scroll = 0
                try:
                    self._relationship_score = self._apply_relationship_delta(
                        character.lower(),
                        reply.relationship_delta,
                    )
                except Exception as error:
                    LOGGER.exception(
                        "Could not save %s relationship score.",
                        character,
                        exc_info=(type(error), error, error.__traceback__),
                    )
                    self._status = (
                        "The reply was received, but its relationship change "
                        "could not be saved."
                    )
                    self._close_requested = False
                else:
                    self._status = (
                        f"Relationship {reply.relationship_delta:+d} "
                        f"(now {self._relationship_score})."
                    )
                    if self._close_requested:
                        self._close_conversation()
        destination = self._pending_screen
        self._pending_screen = None
        return destination

    def draw(self, surface: pygame.Surface) -> None:
        if self._conversation_character is not None:
            self._draw_conversation(surface)
            return
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

    def _draw_conversation(self, surface: pygame.Surface) -> None:
        surface.fill((19, 34, 28))
        width, height = surface.get_size()
        padding = max(20, round(min(width, height) * 0.045))
        scale = max(0.7, min(1.4, min(width / 1280, height / 720)))
        title_font = pygame.font.Font(None, max(28, round(40 * scale)))
        text_font = pygame.font.Font(None, max(21, round(29 * scale)))
        hint_font = pygame.font.Font(None, max(18, round(22 * scale)))
        title = title_font.render(
            f"Talking with the {self._conversation_character}",
            True,
            (237, 212, 146),
        )
        surface.blit(title, (padding, padding))
        score = hint_font.render(
            f"Relationship: {self._relationship_score}",
            True,
            (183, 198, 166),
        )
        surface.blit(
            score,
            score.get_rect(topright=(width - padding, padding + title.get_height() // 2)),
        )

        input_height = max(150, round(height * 0.24))
        input_rect = pygame.Rect(
            padding,
            height - input_height - padding,
            width - 2 * padding,
            input_height,
        )
        transcript_rect = pygame.Rect(
            padding,
            padding + title.get_height() + 18,
            width - 2 * padding,
            input_rect.top - padding - (padding + title.get_height() + 18),
        )
        pygame.draw.rect(surface, (24, 39, 31), transcript_rect, border_radius=12)
        pygame.draw.rect(surface, (111, 133, 105), transcript_rect, width=1, border_radius=12)
        surface.set_clip(transcript_rect.inflate(-padding // 2, -padding // 2))
        history_end = len(self._history) - self._history_scroll
        visible_history = self._history[:history_end]
        y = transcript_rect.bottom - padding // 2
        for index in range(len(visible_history) - 1, -1, -1):
            entry = visible_history[index]
            wrapped = self._wrap_text(
                entry.text,
                text_font,
                transcript_rect.width - 2 * padding,
            )
            line_height = text_font.get_linesize()
            block_height = hint_font.get_linesize() + len(wrapped) * line_height + 12
            y -= block_height
            if y + block_height < transcript_rect.top:
                break
            color = (237, 212, 146) if entry.speaker == "You" else (182, 213, 179)
            label = hint_font.render(entry.speaker, True, color)
            surface.blit(label, (transcript_rect.left + padding, y))
            text_y = y + hint_font.get_linesize()
            for line in wrapped:
                rendered = text_font.render(line, True, (242, 237, 219))
                surface.blit(rendered, (transcript_rect.left + padding, text_y))
                text_y += line_height
            y -= 10
            if index > 0 and visible_history[index - 1].day != entry.day:
                divider_height = hint_font.get_linesize() + 12
                y -= divider_height
                if y + divider_height < transcript_rect.top:
                    break
                day_label = hint_font.render(
                    f"Day {entry.day}",
                    True,
                    (183, 198, 166),
                )
                label_rect = day_label.get_rect(
                    center=(
                        transcript_rect.centerx,
                        y + day_label.get_height() // 2,
                    )
                )
                pygame.draw.line(
                    surface,
                    (111, 133, 105),
                    (transcript_rect.left + padding, label_rect.centery),
                    (label_rect.left - 8, label_rect.centery),
                    1,
                )
                pygame.draw.line(
                    surface,
                    (111, 133, 105),
                    (label_rect.right + 8, label_rect.centery),
                    (transcript_rect.right - padding, label_rect.centery),
                    1,
                )
                surface.blit(day_label, label_rect)
        surface.set_clip(None)

        pygame.draw.rect(surface, (24, 39, 31), input_rect, border_radius=12)
        pygame.draw.rect(surface, (177, 163, 115), input_rect, width=2, border_radius=12)
        status = self._status
        status_font_color = (238, 174, 134) if "failed" in status.lower() or "could not" in status.lower() else (183, 198, 166)
        status_label = hint_font.render(status, True, status_font_color)
        status_x = input_rect.left + padding
        status_y = input_rect.top + padding // 2
        if self._future is not None:
            face_radius = max(10, round(14 * scale))
            face_center = (
                status_x + face_radius,
                status_y + status_label.get_height() // 2,
            )
            status_x += face_radius * 2 + 10
        surface.blit(status_label, (status_x, status_y))
        input_lines = self._wrap_text(
            self._input_text or "Type your message here...",
            text_font,
            input_rect.width - 2 * padding,
        )
        input_y = input_rect.top + padding // 2 + status_label.get_height() + 8
        for line in input_lines[-2:]:
            color = (242, 237, 219) if self._input_text else (151, 163, 145)
            rendered = text_font.render(line, True, color)
            surface.blit(rendered, (input_rect.left + padding, input_y))
            input_y += rendered.get_height()
        hint = hint_font.render(
            "Enter: send   Shift+Enter: new line   Esc: return   Scroll: history",
            True,
            (175, 190, 165),
        )
        surface.blit(
            hint,
            hint.get_rect(bottomright=(input_rect.right - padding // 2, input_rect.bottom - padding // 3)),
        )

    def resize(self, size: tuple[int, int]) -> None:
        self.size = size
