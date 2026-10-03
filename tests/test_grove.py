import unittest

import pygame

from game.screens.grove import GroveScreen


class GroveScreenTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.grove = GroveScreen((800, 600))

    def tearDown(self) -> None:
        pygame.quit()

    def test_player_starts_in_middle_of_walkable_clearing(self) -> None:
        self.assertTrue(self.grove.forest_bounds.contains(self.grove._player_rect()))
        self.assertEqual(
            self.grove.player_position,
            pygame.Vector2(self.grove.world_size[0] / 2, self.grove.world_size[1] / 2),
        )

    def test_wasd_movement_updates_player_position(self) -> None:
        start = self.grove.player_position.copy()
        self.grove.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_d))
        self.grove.update(0.1)
        self.grove.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_d))

        self.assertGreater(self.grove.player_position.x, start.x)
        self.assertEqual(self.grove.player_position.y, start.y)

    def test_player_cannot_enter_forest_or_house(self) -> None:
        house = self.grove.feature_rects["House"]
        self.grove.player_position.update(house.left - self.grove.player_radius - 1, house.centery)
        self.grove._move(pygame.Vector2(self.grove.player_speed, 0))
        self.assertFalse(self.grove._player_rect().colliderect(house))

        self.grove.player_position.update(
            self.grove.forest_bounds.left + self.grove.player_radius + 1,
            self.grove.player_position.y,
        )
        self.grove._move(pygame.Vector2(-self.grove.player_speed, 0))
        self.assertTrue(self.grove.forest_bounds.contains(self.grove._player_rect()))

    def test_hammer_interaction_opens_day_two_task_choices(self) -> None:
        self.grove.player_position.update(self.grove.tool_positions["Hammer"])
        self.grove.begin_day(2)
        self.grove.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))

        self.assertIsNone(self.grove.update(0))
        self.assertEqual(self.grove.consume_task_target(), "hammer")

    def test_talking_to_both_characters_unlocks_tasks_and_resets_each_day(self) -> None:
        self.grove.begin_day(2)
        self.grove.mark_character_talked("Elf")
        self.assertFalse(self.grove.both_characters_talked)

        self.grove.mark_character_talked("Fae")
        self.assertTrue(self.grove.both_characters_talked)
        self.grove.begin_day(3)

        self.assertFalse(self.grove.both_characters_talked)

    def test_daily_task_list_reveals_assignments_after_each_conversation(self) -> None:
        self.grove.begin_day(2)
        self.assertEqual(len(self.grove._daily_task_rows()), 2)

        self.grove.mark_character_talked("elf")
        rows = self.grove._daily_task_rows()
        self.assertEqual(rows[-1], ("Fix the roof with the hammer", False, False))

        self.grove.mark_character_talked("fae")
        rows = self.grove._daily_task_rows()
        self.assertEqual(rows[-2:], (
            ("Fix the roof with the hammer", False, True),
            ("Break the gate lock with the hammer", False, True),
        ))
        self.grove.choose_task("repair_roof")
        rows = self.grove._daily_task_rows()
        self.assertEqual(
            rows[-2:],
            (
                ("Fix the roof with the hammer", False, True),
                ("Break the gate lock with the hammer — FAILED", False, False),
            ),
        )

        self.grove.begin_day(4)
        self.grove.mark_character_talked("elf")
        self.grove.mark_character_talked("fae")
        self.assertEqual(
            self.grove._daily_task_rows()[-1],
            ("Go through the garden maze", False, True),
        )

    def test_character_interaction_emits_conversation_trigger(self) -> None:
        self.grove.player_position.update(self.grove.character_positions["Elf"])
        self.grove.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))

        self.assertIsNone(self.grove.update(0))
        self.assertIn("Elf", self.grove._message)
        self.assertEqual(self.grove.consume_dialogue_trigger(), "interaction.elf")

    def test_gate_blocks_movement_but_interaction_does_nothing(self) -> None:
        gate = self.grove.feature_rects["Gate"]
        self.grove.player_position.update(
            gate.centerx,
            gate.bottom + self.grove.player_radius + 1,
        )
        start = self.grove.player_position.copy()
        self.grove._move(pygame.Vector2(0, -30))

        self.assertEqual(self.grove.player_position, start)
        self.assertFalse(self.grove._player_rect().colliderect(gate))

        old_message = self.grove._message
        self.grove.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
        self.assertIsNone(self.grove.update(0))
        self.assertIsNone(self.grove.consume_dialogue_trigger())
        self.assertEqual(self.grove._message, old_message)

    def test_sleep_box_requires_confirmation_before_sleeping(self) -> None:
        self.grove.mark_character_talked("elf")
        self.grove.mark_character_talked("fae")
        self.grove.player_position.update(self.grove.tool_positions["Sleep"])
        self.grove.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
        self.assertTrue(self.grove.sleep_confirmation_open)
        self.assertFalse(self.grove.consume_sleep_request())

        self.grove.draw(pygame.Surface(self.grove.size))
        self.grove.handle_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                button=pygame.BUTTON_LEFT,
                pos=self.grove._sleep_yes_rect.center,
            )
        )
        self.assertFalse(self.grove.sleep_confirmation_open)
        self.assertTrue(self.grove.consume_sleep_request())

    def test_sleep_is_locked_until_both_characters_have_been_talked_to(self) -> None:
        self.grove.player_position.update(self.grove.tool_positions["Sleep"])
        self.grove.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
        self.grove.draw(pygame.Surface(self.grove.size))
        self.grove.handle_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                button=pygame.BUTTON_LEFT,
                pos=self.grove._sleep_yes_rect.center,
            )
        )

        self.assertTrue(self.grove.sleep_confirmation_open)
        self.assertFalse(self.grove.consume_sleep_request())

    def test_sleep_is_locked_until_every_daily_task_is_complete(self) -> None:
        self.grove.begin_day(2)
        self.grove.mark_character_talked("elf")
        self.grove.mark_character_talked("fae")
        self.grove.player_position.update(self.grove.tool_positions["Sleep"])
        self.grove.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
        self.grove.draw(pygame.Surface(self.grove.size))
        self.grove.handle_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                button=pygame.BUTTON_LEFT,
                pos=self.grove._sleep_yes_rect.center,
            )
        )
        self.assertFalse(self.grove.consume_sleep_request())
        self.assertTrue(self.grove.sleep_confirmation_open)

        self.grove.handle_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                button=pygame.BUTTON_LEFT,
                pos=self.grove._sleep_no_rect.center,
            )
        )
        self.grove.choose_task("repair_roof")
        self.grove.complete_task("repair_roof")
        self.grove.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
        self.grove.draw(pygame.Surface(self.grove.size))
        self.grove.handle_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                button=pygame.BUTTON_LEFT,
                pos=self.grove._sleep_yes_rect.center,
            )
        )

        self.assertTrue(self.grove.all_daily_tasks_complete)
        self.assertTrue(self.grove.consume_sleep_request())

    def test_cannot_choose_both_paths_for_the_same_tool(self) -> None:
        self.grove.begin_day(3)
        self.grove.mark_character_talked("elf")
        self.grove.mark_character_talked("fae")
        self.grove.choose_task("clean_pond")

        with self.assertRaises(ValueError):
            self.grove.choose_task("retrieve_key")
        with self.assertRaises(ValueError):
            self.grove.complete_task("retrieve_key")

        self.assertIn("retrieve_key", self.grove.failed_tasks)
        self.assertNotIn("retrieve_key", self.grove.completed_tasks)

    def test_sleep_can_be_cancelled(self) -> None:
        self.grove.player_position.update(self.grove.tool_positions["Sleep"])
        self.grove.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
        self.grove.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_n))

        self.assertFalse(self.grove.sleep_confirmation_open)
        self.assertFalse(self.grove.consume_sleep_request())

    def test_gate_has_visible_black_white_and_red_locks_next_to_fae(self) -> None:
        center_x = self.grove.gate_sprite.get_width() // 2
        scale_y = self.grove.gate_sprite.get_height() / self.grove.GATE_SPRITE_SIZE[1]
        scale_x = self.grove.gate_sprite.get_width() / self.grove.GATE_SPRITE_SIZE[0]
        lock_colors = ((16, 17, 20), (244, 244, 235), (196, 35, 42))
        for index, color in enumerate(lock_colors):
            source_y = (67, 108, 149)[index] + 4
            point = (
                center_x - round(7 * scale_x),
                round(source_y * scale_y),
            )
            self.assertEqual(self.grove.gate_sprite.get_at(point)[:3], color)

        fae_x, fae_y = self.grove.character_positions["Fae"]
        gate = self.grove.feature_rects["Gate"]
        self.assertGreater(fae_x, gate.right)
        self.assertLessEqual(fae_x - gate.right, 80)
        self.assertLessEqual(abs(fae_y - gate.centery), 30)
        self.assertLess(
            gate.top,
            self.grove.world_size[1] // 2,
        )

    def test_camera_tracks_player_and_clamps_at_world_edges(self) -> None:
        self.grove.player_position.update(
            self.grove.forest_bounds.right - self.grove.player_radius,
            self.grove.forest_bounds.bottom - self.grove.player_radius,
        )
        self.grove._update_camera()

        self.assertEqual(
            self.grove.camera.x,
            max(0, self.grove.world_size[0] - self.grove.size[0]),
        )
        self.assertEqual(
            self.grove.camera.y,
            max(0, self.grove.world_size[1] - self.grove.size[1]),
        )

    def test_draw_and_resize(self) -> None:
        self.grove.resize((1024, 768))
        surface = pygame.Surface((1024, 768))
        self.grove.draw(surface)

        self.assertEqual(self.grove.size, (1024, 768))
        self.assertEqual(surface.get_size(), (1024, 768))

    def test_uploaded_art_is_loaded_and_scaled_for_grove(self) -> None:
        self.assertEqual(
            set(self.grove.sprites),
            {"player", "elf", "fae", "broken_house"},
        )
        self.assertEqual(self.grove.sprites["player"].get_size(), (92, 122))
        self.assertEqual(self.grove.sprites["broken_house"].get_size(), (150, 300))


if __name__ == "__main__":
    unittest.main()
