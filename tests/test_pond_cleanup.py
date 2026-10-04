import tempfile
import unittest
from pathlib import Path

import pygame

from game.app import GameApp
from game.dialogue.relationships import RelationshipStore
from game.minigames.pond_cleanup import PondCleanup
from game.screens.grove import GroveScreen
from game.screens.screen import ScreenId


class PondCleanupTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.game = PondCleanup((800, 600))
        self.game.start("clean_pond", "Clean the pond", "Sort the litter.")

    def tearDown(self) -> None:
        pygame.quit()

    def drag_item(self, index: int, destination: pygame.Rect) -> None:
        self.game.handle_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                button=pygame.BUTTON_LEFT,
                pos=self.game._item_rects[index].center,
            )
        )
        self.game.handle_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                pos=destination.center,
                rel=(0, 0),
                buttons=(1, 0, 0),
            )
        )
        self.game.handle_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONUP,
                button=pygame.BUTTON_LEFT,
                pos=destination.center,
            )
        )

    def test_generated_litter_contains_items_for_both_bins(self) -> None:
        self.assertEqual(len(self.game.items), self.game.ITEM_COUNT)
        self.assertEqual(
            {item.destination for item in self.game.items if item is not None},
            {"trash", "recycling"},
        )

    def test_wrong_bin_keeps_item_in_the_lake(self) -> None:
        index = next(
            index
            for index, item in enumerate(self.game.items)
            if item is not None and item.destination == "trash"
        )
        self.drag_item(index, self.game.recycling_bin_rect)

        self.assertIsNotNone(self.game.items[index])
        self.assertIn("Not quite", self.game._feedback)
        self.assertIsNone(self.game.update(0))

    def test_sorting_all_litter_completes_the_task(self) -> None:
        self.game.draw(pygame.Surface((800, 600)))
        for index, item in enumerate(tuple(self.game.items)):
            if item is None:
                continue
            destination = (
                self.game.trash_bin_rect
                if item.destination == "trash"
                else self.game.recycling_bin_rect
            )
            self.drag_item(index, destination)

        self.assertIs(self.game.update(0), ScreenId.GROVE)
        self.assertEqual(self.game.consume_completed_task_id(), "clean_pond")
        self.assertIsNone(self.game.consume_completed_task_id())
        self.assertTrue(all(item is None for item in self.game.items))

    def test_activity_can_be_cancelled_and_redrawn_after_resize(self) -> None:
        self.game.resize((1024, 768))
        self.game.draw(pygame.Surface((1024, 768)))
        self.game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))

        self.assertIs(self.game.update(0), ScreenId.GROVE)
        self.assertIsNone(self.game.consume_completed_task_id())

    def test_app_routes_and_records_the_completed_pond_task(self) -> None:
        grove = GroveScreen((800, 600))
        grove.begin_day(3)
        grove.mark_character_talked("elf")
        grove.mark_character_talked("fae")
        app = GameApp.__new__(GameApp)
        app.day_number = 3
        app.current_screen_id = ScreenId.GROVE
        app.grove_screen = grove
        app.pond_cleanup_screen = self.game
        with tempfile.TemporaryDirectory() as directory:
            app.relationship_store = RelationshipStore(
                Path(directory) / "relationships.json"
            )
        app.screens = {
            ScreenId.GROVE: grove,
            ScreenId.CLEAN_POND: self.game,
        }
        app._fade_phase = None

        app._start_selected_task("clean_pond")
        self.assertIs(app.current_screen_id, ScreenId.CLEAN_POND)
        for index, item in enumerate(tuple(self.game.items)):
            if item is None:
                continue
            destination = (
                self.game.trash_bin_rect
                if item.destination == "trash"
                else self.game.recycling_bin_rect
            )
            self.drag_item(index, destination)

        app.update(0)

        self.assertIs(app.current_screen_id, ScreenId.GROVE)
        self.assertIn("clean_pond", grove.completed_tasks)
        self.assertIn("retrieve_key", grove.failed_tasks)
        self.assertEqual(app.relationship_store.score("elf"), -2)


if __name__ == "__main__":
    unittest.main()
