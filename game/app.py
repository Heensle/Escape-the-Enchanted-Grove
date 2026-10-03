from __future__ import annotations

import pygame

from game.screens.epilogue import EpilogueScreen
from game.screens.interaction import InteractionScreen
from game.screens.intro import IntroScreen
from game.screens.grove import GroveScreen
from game.screens.screen import ScreenId, ScreenView
from game.screens.title import TITLE, TitleScreen
from game.minigames.lock_break_clicker import LockBreakClicker


class GameApp:
    def __init__(self) -> None:
        pygame.init()
        self.surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.screens: dict[ScreenId, ScreenView] = {}
        self._create_screens()
        self.current_screen_id = ScreenId.TITLE
        self.running = True

    def _create_screens(self) -> None:
        size = self.surface.get_size()
        self.title_screen = TitleScreen(size)
        self.lock_break_screen = LockBreakClicker(size)
        self.screens = {
            ScreenId.TITLE: self.title_screen,
            ScreenId.INTRO: IntroScreen(size),
            ScreenId.GROVE: GroveScreen(size),
            ScreenId.INTERACTION: InteractionScreen(size),
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

        self.current_screen.handle_event(event)

    def update(self, delta_seconds: float) -> None:
        destination = self.current_screen.update(delta_seconds)
        if destination is not None:
            if destination is ScreenId.TITLE:
                self.title_screen.reset()
            elif destination is ScreenId.LOCK_BREAK:
                self.lock_break_screen.reset()
            self.current_screen_id = destination

    def draw(self) -> None:
        self.current_screen.draw(self.surface)
        pygame.display.flip()

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
