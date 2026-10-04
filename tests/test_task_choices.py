import unittest
from concurrent.futures import Future

import pygame

from game.app import GameApp
from game.dialogue.gemini import GeminiReply
from game.screens.grove import GroveScreen
from game.screens.interaction import InteractionScreen
from game.screens.screen import ScreenId
from game.screens.task_choices import (
    JigsawScreen,
    TaskActivityScreen,
    TaskChoicesScreen,
)
from game.minigames.lock_break_clicker import LockBreakClicker
from game.tasks.daily import DailyTask


class TaskChoicesTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.screen = TaskChoicesScreen((800, 600))
        self.options = (
            DailyTask(
                "repair",
                2,
                "hammer",
                "elf",
                "Repair the roof",
                "Repair the roof",
                "Start the roof jigsaw.",
            ),
            DailyTask(
                "break",
                2,
                "hammer",
                "fae",
                "Break the gate lock",
                "Break the gate lock",
                "Use the hammer.",
            ),
        )

    def tearDown(self) -> None:
        pygame.quit()

    def test_choices_remain_locked_until_both_characters_are_talked_to(self) -> None:
        self.screen.start("Hammer tasks", self.options, unlocked=False)
        self.screen.handle_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                button=pygame.BUTTON_LEFT,
                pos=self.screen.option_rects[0].center,
            )
        )

        self.assertIsNone(self.screen.update(0))
        self.assertIsNone(self.screen.consume_selected_option())

    def test_unlocked_choice_routes_back_to_the_grove_with_selection(self) -> None:
        self.screen.start("Hammer tasks", self.options, unlocked=True)
        self.screen.handle_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                button=pygame.BUTTON_LEFT,
                pos=self.screen.option_rects[1].center,
            )
        )

        self.assertIs(self.screen.update(0), ScreenId.GROVE)
        self.assertEqual(self.screen.consume_selected_option(), "break")

    def test_app_routes_roof_repair_choice_to_jigsaw_and_completes_task(self) -> None:
        grove = GroveScreen((800, 600))
        grove.begin_day(2)
        grove.mark_character_talked("elf")
        choices = TaskChoicesScreen((800, 600))
        jigsaw = JigsawScreen((800, 600))
        activity = TaskActivityScreen((800, 600))
        lock_break = LockBreakClicker((800, 600))
        app = GameApp.__new__(GameApp)
        app.day_number = 2
        app.current_screen_id = ScreenId.GROVE
        app.screens = {
            ScreenId.GROVE: grove,
            ScreenId.TASK_CHOICES: choices,
            ScreenId.JIGSAW: jigsaw,
            ScreenId.TASK_ACTIVITY: activity,
            ScreenId.LOCK_BREAK: lock_break,
        }
        app.grove_screen = grove
        app.task_choices_screen = choices
        app.jigsaw_screen = jigsaw
        app.task_activity_screen = activity
        app.lock_break_screen = lock_break
        app._fade_phase = None

        app._start_task_choices("hammer")
        self.assertIs(app.current_screen_id, ScreenId.TASK_CHOICES)
        choices.handle_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                button=pygame.BUTTON_LEFT,
                pos=choices.option_rects[0].center,
            )
        )
        app.update(0)
        self.assertIs(app.current_screen_id, ScreenId.TASK_CHOICES)

        grove.mark_character_talked("fae")
        app._start_task_choices("hammer")
        choices.handle_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                button=pygame.BUTTON_LEFT,
                pos=choices.option_rects[0].center,
            )
        )
        app.update(0)

        self.assertIs(app.current_screen_id, ScreenId.JIGSAW)
        self.assertEqual(jigsaw.task_id, "repair_roof")
        jigsaw.draw(pygame.Surface((800, 600)))
        for target, piece in enumerate(range(len(jigsaw.board))):
            if jigsaw.board[target] == piece:
                continue
            if piece in jigsaw.tray:
                source_index = jigsaw.tray.index(piece)
                source_rect = jigsaw.tray_slot_rects[source_index]
            else:
                source_index = jigsaw.board.index(piece)
                source_rect = jigsaw.board_slot_rects[source_index]
            jigsaw.handle_event(
                pygame.event.Event(
                    pygame.MOUSEBUTTONDOWN,
                    button=pygame.BUTTON_LEFT,
                    pos=source_rect.center,
                )
            )
            jigsaw.handle_event(
                pygame.event.Event(
                    pygame.MOUSEBUTTONUP,
                    button=pygame.BUTTON_LEFT,
                    pos=jigsaw.board_slot_rects[target].center,
                )
            )
            if jigsaw.completed:
                break
        self.assertEqual(jigsaw.board, list(range(len(jigsaw.board))))
        app.update(0)
        self.assertIn("repair_roof", grove.completed_tasks)

        app._start_task_choices("hammer")
        choices.handle_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                button=pygame.BUTTON_LEFT,
                pos=choices.option_rects[1].center,
            )
        )
        app.update(0)
        self.assertIs(app.current_screen_id, ScreenId.TASK_CHOICES)
        self.assertNotIn("break_gate_lock", grove.completed_tasks)
        self.assertIn("break_gate_lock", grove.failed_tasks)
        self.assertTrue(grove.all_daily_tasks_complete)

    def test_jigsaw_can_be_cancelled_without_completing_task(self) -> None:
        jigsaw = JigsawScreen((800, 600))
        jigsaw.start("repair_roof", "Repair the roof", "Swap the tiles.")
        jigsaw.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))

        self.assertIs(jigsaw.update(0), ScreenId.GROVE)
        self.assertIsNone(jigsaw.consume_completed_task_id())

    def test_jigsaw_pieces_drag_from_tray_into_board_slots(self) -> None:
        jigsaw = JigsawScreen((800, 600))
        jigsaw.start("repair_roof", "Repair the roof", "Drag the tiles.")
        piece = jigsaw.tray[0]
        self.assertIsNotNone(piece)
        target = piece

        jigsaw.handle_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                button=pygame.BUTTON_LEFT,
                pos=jigsaw.tray_slot_rects[0].center,
            )
        )
        jigsaw.handle_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                pos=jigsaw.board_slot_rects[target].center,
                rel=(0, 0),
                buttons=(1, 0, 0),
            )
        )
        jigsaw.handle_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONUP,
                button=pygame.BUTTON_LEFT,
                pos=jigsaw.board_slot_rects[target].center,
            )
        )

        self.assertEqual(jigsaw.board[target], piece)
        self.assertIsNone(jigsaw.tray[0])
        self.assertEqual(jigsaw.placed_count, 1)

    def test_temporary_task_can_be_completed_or_cancelled(self) -> None:
        activity = TaskActivityScreen((800, 600))
        activity.start("clean_pond", "Clean the pond", "Use the net.")
        activity.draw(pygame.Surface((800, 600)))
        activity.handle_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                button=pygame.BUTTON_LEFT,
                pos=activity.complete_rect.center,
            )
        )

        self.assertIs(activity.update(0), ScreenId.GROVE)
        self.assertEqual(activity.consume_completed_task_id(), "clean_pond")

        activity.start("clean_pond", "Clean the pond", "Use the net.")
        activity.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        self.assertIs(activity.update(0), ScreenId.GROVE)
        self.assertIsNone(activity.consume_completed_task_id())

    def test_conversation_counts_as_talk_only_after_a_message_is_sent(self) -> None:
        screen = InteractionScreen((800, 600))
        future: Future[GeminiReply] = Future()
        submitted_turns: list[tuple[str, str, int, tuple[tuple[str, str], ...]]] = []

        def submit_turn(
            character: str,
            message: str,
            score: int,
            history: tuple[tuple[str, str], ...],
        ) -> Future[GeminiReply]:
            submitted_turns.append((character, message, score, history))
            return future

        def apply_delta(character: str, delta: int) -> int:
            return delta if character in ("elf", "fae") else -delta

        screen.start_conversation(
            "elf",
            -5,
            submit_turn,
            apply_delta,
            ScreenId.GROVE,
        )
        screen.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        self.assertIs(screen.update(0), ScreenId.GROVE)
        self.assertIsNone(screen.consume_completed_conversation_character())

        screen.start_conversation(
            "elf",
            -5,
            submit_turn,
            apply_delta,
            ScreenId.GROVE,
        )
        screen.handle_event(
            pygame.event.Event(pygame.TEXTINPUT, text="Can I help?")
        )
        screen.handle_event(
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0)
        )
        future.set_result(GeminiReply("Yes, please.", 0))
        screen.update(0)
        screen.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        self.assertIs(screen.update(0), ScreenId.GROVE)
        self.assertEqual(screen.consume_completed_conversation_character(), "elf")
        self.assertEqual(submitted_turns[0][0:3], ("elf", "Can I help?", -5))



if __name__ == "__main__":
    unittest.main()
