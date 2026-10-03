from __future__ import annotations

import pygame

from game.dialogue.service import JsonDialogueService
from game.minigames.lock_break_clicker import LockBreakClicker
from game.screens.epilogue import EpilogueScreen
from game.screens.interaction import InteractionScreen
from game.screens.grove import GroveScreen
from game.screens.screen import ScreenId, ScreenView
from game.screens.title import TITLE, TitleScreen


class GameApp:
    DAY_FADE_SECONDS = 0.55

    def __init__(self) -> None:
        pygame.init()
        self.surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.dialogue_service = JsonDialogueService()
        self.day_number = 1
        self.screens: dict[ScreenId, ScreenView] = {}
        self._create_screens()
        self.current_screen_id = ScreenId.TITLE
        self.running = True
        self._completed_event_ids: set[str] = set()
        self._fade_phase: str | None = None
        self._fade_elapsed = 0.0
        self._fade_alpha = 0
        self._fade_destination: ScreenId | None = None

    def _create_screens(self) -> None:
        size = self.surface.get_size()
        self.title_screen = TitleScreen(size)
        self.lock_break_screen = LockBreakClicker(size)
        self.grove_screen = GroveScreen(size)
        self.interaction_screen = InteractionScreen(size)
        self.screens = {
            ScreenId.TITLE: self.title_screen,
            ScreenId.GROVE: self.grove_screen,
            ScreenId.INTERACTION: self.interaction_screen,
            ScreenId.LOCK_BREAK: self.lock_break_screen,
            ScreenId.EPILOGUE: EpilogueScreen(size),
        }

    @property
    def current_screen(self) -> ScreenView:
        return self.screens[self.current_screen_id]

    def _toggle_fullscreen(self) -> None:
        fullscreen = bool(self.surface.get_flags() & pygame.FULLSCREEN)
        flags = 0 if fullscreen else pygame.FULLSCREEN
        self.surface = pygame.display.set_mode((0, 0), flags)
        for screen in self.screens.values():
            screen.resize(self.surface.get_size())

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.running = False
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.running = False
            return
        if (
            event.type == pygame.KEYDOWN
            and event.key == pygame.K_F11
            and self.current_screen_id is ScreenId.TITLE
        ):
            self._toggle_fullscreen()
            return

        if self._fade_phase is not None:
            return
        self.current_screen.handle_event(event)

    def update(self, delta_seconds: float) -> None:
        if self._fade_phase is not None:
            self._update_day_fade(delta_seconds)
            return

        previous_screen_id = self.current_screen_id
        destination = self.current_screen.update(delta_seconds)

        if previous_screen_id is ScreenId.GROVE:
            trigger = self.grove_screen.consume_dialogue_trigger()
            if trigger is not None:
                events = tuple(
                    event
                    for event in self.dialogue_service.get_events_for(trigger)
                    if event.day == self.day_number
                    and event.id not in self._completed_event_ids
                )
                if not events:
                    return
                self.interaction_screen.start(events, ScreenId.GROVE)
                self.current_screen_id = ScreenId.INTERACTION
                return

        if destination is None:
            return

        if (
            previous_screen_id is ScreenId.TITLE
            and destination is ScreenId.INTERACTION
        ):
            self._start_dialogue("scene.intro", ScreenId.GROVE)
            return

        if (
            previous_screen_id is ScreenId.INTERACTION
            and destination is ScreenId.GROVE
        ):
            self._completed_event_ids.update(
                self.interaction_screen.consume_completed_event_ids()
            )
            day_events = self.dialogue_service.get_events_for_day(self.day_number)
            if day_events and all(
                event.id in self._completed_event_ids for event in day_events
            ):
                self._start_day_fade(destination)
                return
            self.current_screen_id = destination
            return

        if destination is ScreenId.TITLE:
            self.title_screen.reset()
        elif destination is ScreenId.LOCK_BREAK:
            self.lock_break_screen.reset()
        self.current_screen_id = destination

    def draw(self) -> None:
        self.current_screen.draw(self.surface)
        if self._fade_alpha:
            overlay = pygame.Surface(self.surface.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, self._fade_alpha))
            self.surface.blit(overlay, (0, 0))
        pygame.display.flip()

    def _start_dialogue(self, trigger: str, destination: ScreenId) -> None:
        events = tuple(
            event
            for event in self.dialogue_service.get_events_for(trigger)
            if event.day == self.day_number
        )
        if not events:
            raise ValueError(f"No dialogue is authored for trigger {trigger!r}.")
        self.interaction_screen.start(events, destination)
        self.current_screen_id = ScreenId.INTERACTION

    def _start_day_fade(self, destination: ScreenId) -> None:
        self._fade_destination = destination
        self._fade_elapsed = 0.0
        self._fade_alpha = 0
        self._fade_phase = "out"

    def _update_day_fade(self, delta_seconds: float) -> None:
        self._fade_elapsed = min(
            self._fade_elapsed + max(0.0, delta_seconds),
            self.DAY_FADE_SECONDS,
        )
        progress = self._fade_elapsed / self.DAY_FADE_SECONDS
        if self._fade_phase == "out":
            self._fade_alpha = round(255 * progress)
            if progress == 1:
                if self._fade_destination is None:
                    raise RuntimeError("Day fade has no destination screen.")
                self.current_screen_id = self._fade_destination
                self.day_number += 1
                self.grove_screen.day_number = self.day_number
                self._completed_event_ids.clear()
                self._fade_phase = "in"
                self._fade_elapsed = 0.0
            return

        self._fade_alpha = round(255 * (1 - progress))
        if progress == 1:
            self._fade_phase = None
            self._fade_alpha = 0
            self._fade_destination = None

    def run(self) -> None:
        try:
            while self.running:
                delta_seconds = self.clock.tick(60) / 1000
                for event in pygame.event.get():
                    self.handle_event(event)
                self.update(delta_seconds)
                self.draw()
        finally:
            pygame.quit()
