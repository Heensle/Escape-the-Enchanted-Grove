import unittest

import pygame

from game.screens.grove import GroveScreen
from game.screens.screen import ScreenId


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

    def test_hammer_interaction_opens_lock_break_screen(self) -> None:
        self.grove.player_position.update(self.grove.tool_positions["Hammer"])
        self.grove._pressed_keys.add(pygame.K_w)
        self.grove.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))

        self.assertIs(self.grove.update(0), ScreenId.LOCK_BREAK)
        self.assertIsNone(self.grove.update(0))
        self.assertEqual(self.grove._pressed_keys, set())

    def test_other_interactions_display_a_message_without_leaving_room(self) -> None:
        self.grove.player_position.update(self.grove.character_positions["Elf"])
        self.grove.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))

        self.assertIsNone(self.grove.update(0))
        self.assertIn("Elf", self.grove._message)

    def test_locked_gate_blocks_movement_and_triggers_sleep_event(self) -> None:
        gate = self.grove.feature_rects["Gate"]
        self.grove.player_position.update(
            gate.centerx,
            gate.bottom + self.grove.player_radius + 1,
        )
        start = self.grove.player_position.copy()
        self.grove._move(pygame.Vector2(0, -30))

        self.assertEqual(self.grove.player_position, start)
        self.assertFalse(self.grove._player_rect().colliderect(gate))

        self.grove.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
        self.assertIsNone(self.grove.update(0))
        self.assertEqual(
            self.grove.consume_dialogue_trigger(),
            "scene.fall_asleep",
        )

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
