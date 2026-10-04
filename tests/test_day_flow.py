import unittest
from types import SimpleNamespace

import pygame

from game.app import GameApp
from game.dialogue.service import DialogueEvent, DialogueLine, JsonDialogueService
from game.screens.interaction import InteractionScreen
from game.screens.screen import ScreenId
from game.state import MAX_DAYS


class _OneShotScreen:
    def __init__(self, destination: ScreenId | None = None) -> None:
        self.destination = destination

    def update(self, _delta_seconds: float) -> ScreenId | None:
        _ = _delta_seconds
        destination = self.destination
        self.destination = None
        return destination


class _GroveRequestScreen(_OneShotScreen):
    def __init__(self) -> None:
        super().__init__()
        self.day_number = 1
        self.sleep_requested = False

    def consume_dialogue_trigger(self) -> str | None:
        return None

    def consume_sleep_request(self) -> bool:
        requested = self.sleep_requested
        self.sleep_requested = False
        return requested

    def consume_task_target(self) -> str | None:
        return None

    def begin_day(self, day_number: int) -> None:
        self.day_number = day_number


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
        app.grove_screen = SimpleNamespace(
            day_number=1,
            begin_day=lambda day_number: setattr(
                app.grove_screen, "day_number", day_number
            ),
        )
        app._completed_event_ids = set()
        app._fade_destination = None
        app._fade_elapsed = 0.0
        app._fade_alpha = 0
        app._fade_phase = None
        app._interaction_character = None

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

    def test_finishing_day_four_ends_the_story_without_starting_day_five(self) -> None:
        app = GameApp.__new__(GameApp)
        app.current_screen_id = ScreenId.INTERACTION
        app.day_number = MAX_DAYS
        app.grove_screen = SimpleNamespace(
            begin_day=lambda day_number: self.fail(
                f"Should not begin day {day_number} after the finale"
            )
        )
        app._completed_event_ids = {"day_04.scene.fall_asleep"}
        app._fade_destination = None
        app._fade_elapsed = 0.0
        app._fade_alpha = 0
        app._fade_phase = None

        app._start_day_fade(ScreenId.GROVE)
        app._update_day_fade(app.DAY_FADE_SECONDS)

        self.assertIs(app.current_screen_id, ScreenId.EPILOGUE)
        self.assertEqual(app.day_number, MAX_DAYS)
        self.assertEqual(app._completed_event_ids, set())

    def test_escape_opens_quit_confirmation_without_closing_game(self) -> None:
        forwarded_events = []
        app = GameApp.__new__(GameApp)
        app.current_screen_id = ScreenId.TITLE
        app.screens = {
            ScreenId.TITLE: SimpleNamespace(
                handle_event=forwarded_events.append,
            )
        }
        app.running = True
        app.surface = pygame.Surface((800, 600))
        app._quit_confirmation_open = False

        app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))

        self.assertTrue(app.running)
        self.assertTrue(app._quit_confirmation_open)
        self.assertEqual(forwarded_events, [])

    def test_quit_confirmation_can_be_cancelled_or_confirmed_by_keyboard(self) -> None:
        app = GameApp.__new__(GameApp)
        app.current_screen_id = ScreenId.TITLE
        app.screens = {
            ScreenId.TITLE: SimpleNamespace(
                handle_event=lambda _event: self.fail(
                    "Confirmation input should not reach the underlying screen"
                ),
            )
        }
        app.running = True
        app.surface = pygame.Surface((800, 600))
        app._quit_confirmation_open = True

        app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_n))
        self.assertTrue(app.running)
        self.assertFalse(app._quit_confirmation_open)

        app._quit_confirmation_open = True
        app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_y))
        self.assertFalse(app.running)
        self.assertTrue(app._quit_confirmation_open)

    def test_quit_confirmation_buttons_cancel_or_quit(self) -> None:
        app = GameApp.__new__(GameApp)
        app.current_screen_id = ScreenId.TITLE
        app.screens = {
            ScreenId.TITLE: SimpleNamespace(
                handle_event=lambda _event: self.fail(
                    "Confirmation input should not reach the underlying screen"
                ),
            )
        }
        app.running = True
        app.surface = pygame.Surface((800, 600))
        app._quit_confirmation_open = True
        _, yes_button, no_button = app._quit_confirmation_rects()

        app.handle_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                button=1,
                pos=no_button.center,
            )
        )
        self.assertTrue(app.running)
        self.assertFalse(app._quit_confirmation_open)

        app._quit_confirmation_open = True
        app.handle_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                button=1,
                pos=yes_button.center,
            )
        )
        self.assertFalse(app.running)

    def test_day_one_sleep_dialogue_requires_bedroll_confirmation(self) -> None:
        title = _OneShotScreen(ScreenId.INTERACTION)
        grove = _GroveRequestScreen()
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
        app._sleep_after_dialogue = False
        app._interaction_character = None
        app._fade_destination = None
        app._fade_elapsed = 0.0
        app._fade_alpha = 0
        app._fade_phase = None

        app.update(0)
        self.assertEqual(dialogue._events[0].id, "day_01.scene.intro")

        opening_event_ids = (
            "day_01.scene.elf_dialogue_1",
            "day_01.scene.elf_dialogue_2",
            "day_01.scene.elf_dialogue_3",
            "day_01.scene.elf_dialogue_4",
            "day_01.scene.fae_dialogue_1",
            "day_01.scene.fae_dialogue_2",
            "day_01.scene.fae_dialogue_3",
            "day_01.scene.fae_dialogue_4",
            "day_01.scene.fae_dialogue_5",
            "day_01.scene.fae_dialogue_6",
            "day_01.scene.fae_dialogue_7",
            "day_01.scene.fae_dialogue_8",
            "day_01.scene.fae_dialogue_9",
        )
        for event_id in opening_event_ids:
            dialogue.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
            app.update(0)
            self.assertIs(app.current_screen_id, ScreenId.INTERACTION)
            self.assertEqual(
                dialogue._events[dialogue._event_index].id,
                event_id,
            )

        dialogue.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
        app.update(0)
        self.assertIs(app.current_screen_id, ScreenId.GROVE)
        self.assertEqual(
            app._completed_event_ids,
            {"day_01.scene.intro", *opening_event_ids},
        )
        self.assertIsNone(app._fade_phase)

        grove.sleep_requested = True
        app.update(0)
        self.assertEqual(dialogue._events[0].id, "day_01.scene.fall_asleep")

        dialogue.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
        app.update(0)
        self.assertEqual(app._fade_phase, "out")
        self.assertEqual(app._completed_event_ids, {
            "day_01.scene.intro",
            *opening_event_ids,
            "day_01.scene.fall_asleep",
        })


if __name__ == "__main__":
    unittest.main()
