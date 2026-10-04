import tempfile
import unittest
from pathlib import Path

import pygame

from game.app import GameApp
from game.dialogue.relationships import RelationshipStore
from game.minigames.key_retrieval_clicker import KeyRetrievalClicker
from game.screens.grove import GroveScreen
from game.screens.screen import ScreenId
from game.tasks.results import TaskOutcome


class KeyRetrievalClickerTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.game = KeyRetrievalClicker((800, 600))

    def tearDown(self) -> None:
        pygame.quit()

    def click_key(self) -> None:
        self.game.handle_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                button=pygame.BUTTON_LEFT,
                pos=self.game.key_rect.center,
            )
        )

    def test_key_requires_clicking_and_shows_plug_before_returning(self) -> None:
        outside = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            button=pygame.BUTTON_LEFT,
            pos=(0, 0),
        )
        self.game.handle_event(outside)
        self.assertEqual(self.game.hits, 0)

        for _ in range(self.game.REQUIRED_HITS):
            self.click_key()

        self.assertTrue(self.game.completed)
        self.assertIsNone(self.game.update(self.game.COMPLETION_SECONDS / 2))
        self.game.draw(pygame.Surface((800, 600)))
        self.assertIs(self.game.update(self.game.COMPLETION_SECONDS), ScreenId.GROVE)
        self.assertEqual(self.game.consume_completed_task_id(), "retrieve_key")

    def test_cancel_does_not_complete_task_and_reset_clears_progress(self) -> None:
        self.click_key()
        self.game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))

        self.assertIs(self.game.update(0), ScreenId.GROVE)
        self.assertIsNone(self.game.consume_completed_task_id())
        self.game.reset()
        self.assertEqual(self.game.hits, 0)
        self.assertFalse(self.game.completed)

    def test_completed_key_task_drains_pond_persistently(self) -> None:
        grove = GroveScreen((800, 600))
        grove.begin_day(3)
        grove.mark_character_talked("elf")
        grove.mark_character_talked("fae")
        grove.choose_task("retrieve_key")
        water_background = grove.background.copy()

        grove.complete_task("retrieve_key")
        drained_background = grove.background.copy()
        drained_pond_color = drained_background.get_at(grove.feature_rects["Pond"].center)
        grove.begin_day(4)

        self.assertTrue(grove.pond_drained)
        self.assertNotEqual(
            water_background.get_at(grove.feature_rects["Pond"].center),
            drained_pond_color,
        )
        self.assertEqual(
            grove.background.get_at(grove.feature_rects["Pond"].center),
            drained_pond_color,
        )

    def test_app_routes_key_retrieval_and_completes_the_fae_task(self) -> None:
        grove = GroveScreen((800, 600))
        grove.begin_day(3)
        grove.mark_character_talked("elf")
        grove.mark_character_talked("fae")
        app = GameApp.__new__(GameApp)
        app.day_number = 3
        app.current_screen_id = ScreenId.GROVE
        app._fade_phase = None
        app.grove_screen = grove
        app.key_retrieval_screen = self.game
        with tempfile.TemporaryDirectory() as directory:
            app.relationship_store = RelationshipStore(
                Path(directory) / "relationships.json"
            )
        app.screens = {
            ScreenId.GROVE: grove,
            ScreenId.PULL_KEY: self.game,
        }

        app._start_selected_task("retrieve_key")
        self.assertIs(app.current_screen_id, ScreenId.PULL_KEY)
        for _ in range(self.game.REQUIRED_HITS):
            self.click_key()

        app.update(self.game.COMPLETION_SECONDS)

        self.assertIs(app.current_screen_id, ScreenId.GROVE)
        self.assertIn("retrieve_key", grove.completed_tasks)
        self.assertTrue(grove.pond_drained)
        self.assertEqual(app.relationship_store.score("fae"), 8)

    def test_abandoning_a_chosen_character_task_reduces_their_relationship(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            app = GameApp.__new__(GameApp)
            app.relationship_store = RelationshipStore(
                Path(directory) / "relationships.json"
            )

            message = app._record_task_relationship(
                "retrieve_key",
                TaskOutcome.CANCELLED,
            )

            self.assertEqual(app.relationship_store.score("fae"), 2)
            self.assertIn("Fae relationship -3", message)


if __name__ == "__main__":
    unittest.main()
