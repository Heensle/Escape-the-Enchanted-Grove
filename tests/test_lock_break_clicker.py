import unittest

import pygame

from game.minigames.lock_break_clicker import LockBreakClicker
from game.screens.screen import ScreenId


class LockBreakClickerTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.game = LockBreakClicker((800, 600))

    def tearDown(self) -> None:
        pygame.quit()

    def click_lock(self) -> pygame.event.Event:
        return pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            button=pygame.BUTTON_LEFT,
            pos=self.game.lock_rect.center,
        )

    def test_clicks_on_lock_complete_game_at_required_hit_count(self) -> None:
        for _ in range(self.game.REQUIRED_HITS - 1):
            self.game.handle_event(self.click_lock())
            self.assertIsNone(self.game.update(0))
        self.game.handle_event(self.click_lock())
        self.assertTrue(self.game.completed)
        self.assertIs(self.game.update(0), ScreenId.GROVE)
        self.assertIsNone(self.game.update(0))

    def test_click_outside_lock_does_not_count(self) -> None:
        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            button=pygame.BUTTON_LEFT,
            pos=(0, 0),
        )

        self.game.handle_event(event)
        self.assertEqual(self.game.hits, 0)

    def test_non_left_click_does_not_count(self) -> None:
        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            button=pygame.BUTTON_RIGHT,
            pos=self.game.lock_rect.center,
        )

        self.game.handle_event(event)
        self.assertEqual(self.game.hits, 0)

    def test_completed_game_ignores_more_clicks(self) -> None:
        for _ in range(self.game.REQUIRED_HITS):
            self.game.handle_event(self.click_lock())

        self.game.handle_event(self.click_lock())
        self.assertEqual(self.game.hits, self.game.REQUIRED_HITS)

    def test_reset_allows_game_to_be_played_again(self) -> None:
        for _ in range(self.game.REQUIRED_HITS):
            self.game.handle_event(self.click_lock())

        self.game.reset()

        self.assertFalse(self.game.completed)
        self.assertEqual(self.game.hits, 0)
        self.game.handle_event(self.click_lock())
        self.assertIsNone(self.game.update(0))

    def test_draw_supports_surface_and_resize(self) -> None:
        self.game.resize((1024, 768))
        surface = pygame.Surface((1024, 768))

        self.game.draw(surface)

        self.assertEqual(self.game.lock_rect.center, (512, 465))

if __name__ == "__main__":
    unittest.main()
