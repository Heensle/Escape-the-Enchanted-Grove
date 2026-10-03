import unittest
from types import SimpleNamespace

import pygame

from game.app import GameApp
from game.dialogue.service import DialogueEvent, DialogueLine, JsonDialogueService
from game.screens.interaction import InteractionScreen
from game.screens.screen import ScreenId


class _OneShotScreen:
    def __init__(self, destination: ScreenId | None = None) -> None:
        self.destination = destination

    def update(self, _delta_seconds: float) -> ScreenId | None:
        _ = _delta_seconds
        destination = self.destination
        self.destination = None
        return destination


class _GroveRequestScreen(_OneShotScreen):
    def __init__(self, trigger: str) -> None:
        super().__init__()
        self.trigger = trigger

    def consume_dialogue_trigger(self) -> str | None:
        trigger = self.trigger
        self.trigger = ""
        return trigger or None


class DayFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()

    def tearDown(self) -> None:
        pygame.quit()

    def test_dialogue_screen_advances_lines_then_returns_to_destination(self) -> None:
        event = DialogueEvent(
            id="day_01.scene.test",
            day=1,
            trigger="scene.test",
            lines=(
                DialogueLine("narrator", "First line."),
                DialogueLine("elf", "Second line."),
            ),
        )
        screen = InteractionScreen((800, 600))
        screen.start((event,), ScreenId.GROVE)
        surface = pygame.Surface((800, 600))
        screen.draw(surface)

        screen.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
        self.assertEqual(screen._line_index, 1)
        self.assertIsNone(screen.update(0))

        screen.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        self.assertIs(screen.update(0), ScreenId.GROVE)
        self.assertIsNone(screen.update(0))

    def test_day_change_fades_out_and_back_before_finishing(self) -> None:
        app = GameApp.__new__(GameApp)
        app.current_screen_id = ScreenId.INTERACTION
        app.day_number = 1
        app.grove_screen = SimpleNamespace(day_number=1)
        app._completed_event_ids = set()
        app._fade_destination = None
        app._fade_elapsed = 0.0
        app._fade_alpha = 0
        app._fade_phase = None

        app._start_day_fade(ScreenId.GROVE)
        app._update_day_fade(app.DAY_FADE_SECONDS)

        self.assertIs(app.current_screen_id, ScreenId.GROVE)
        self.assertEqual(app.day_number, 2)
        self.assertEqual(app.grove_screen.day_number, 2)
        self.assertEqual(app._fade_alpha, 255)
        self.assertEqual(app._fade_phase, "in")

        app._update_day_fade(app.DAY_FADE_SECONDS)

        self.assertEqual(app._fade_alpha, 0)
        self.assertIsNone(app._fade_phase)
        self.assertEqual(app._completed_event_ids, set())

    def test_day_one_events_are_connected_to_start_and_gate(self) -> None:
        title = _OneShotScreen(ScreenId.INTERACTION)
        grove = _GroveRequestScreen("scene.fall_asleep")
        dialogue = InteractionScreen((800, 600))
        app = GameApp.__new__(GameApp)
        app.screens = {
            ScreenId.TITLE: title,
            ScreenId.GROVE: grove,
            ScreenId.INTERACTION: dialogue,
        }
        app.title_screen = title
        app.grove_screen = grove
        app.interaction_screen = dialogue
        app.dialogue_service = JsonDialogueService()
        app.current_screen_id = ScreenId.TITLE
        app.day_number = 1
        app._completed_event_ids = set()
        app._fade_destination = None
        app._fade_elapsed = 0.0
        app._fade_alpha = 0
        app._fade_phase = None

        app.update(0)
        self.assertEqual(dialogue._events[0].id, "day_01.scene.intro")

        dialogue.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
        app.update(0)
        self.assertIs(app.current_screen_id, ScreenId.GROVE)
        self.assertEqual(app._completed_event_ids, {"day_01.scene.intro"})
        self.assertIsNone(app._fade_phase)

        app.update(0)
        self.assertEqual(dialogue._events[0].id, "day_01.scene.fall_asleep")

        dialogue.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
        app.update(0)
        self.assertEqual(app._fade_phase, "out")
        self.assertEqual(app._completed_event_ids, {
            "day_01.scene.intro",
            "day_01.scene.fall_asleep",
        })


if __name__ == "__main__":
    unittest.main()
