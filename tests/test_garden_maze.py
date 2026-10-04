from __future__ import annotations

from collections import deque
import unittest

import pygame

from game.minigames.garden_maze import GardenMaze
from game.screens.screen import ScreenId
from game.state import GardenEnding


class GardenMazeTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.maze = GardenMaze((800, 600))
        self.maze.start("garden_maze", "The Garden Maze", "Find the vegetables.")

    def tearDown(self) -> None:
        pygame.quit()

    def test_maze_is_rectangular_and_every_vegetable_and_exit_is_reachable(self) -> None:
        self.assertTrue(all(len(row) == len(self.maze.MAZE[0]) for row in self.maze.MAZE))
        for target in (*self.maze._vegetable_cells, self.maze._find_cell("E"), self.maze._find_cell("F")):
            self.assertIsNotNone(self._path_to(target, allow_exits=True))

    def test_exit_does_not_complete_before_all_vegetables_are_collected(self) -> None:
        exit_cell = self.maze._find_cell("E")
        self.maze.player_cell = (exit_cell[0] + 1, exit_cell[1])
        self._step_to(exit_cell)

        self.assertIsNone(self.maze.update(0))
        self.assertIsNone(self.maze.consume_completed_task_id())
        self.assertEqual(len(self.maze._collected), 0)
        self.assertIn("Gather every vegetable", self.maze._message)

    def test_all_vegetables_can_be_delivered_at_either_exit(self) -> None:
        for exit_marker, ending in (
            ("E", GardenEnding.ELF),
            ("F", GardenEnding.FAE),
        ):
            with self.subTest(exit=exit_marker):
                self.maze.start(
                    "garden_maze",
                    "The Garden Maze",
                    "Find the vegetables.",
                )
                exit_cell = self.maze._find_cell(exit_marker)
                for vegetable_cell in tuple(self.maze._vegetable_cells):
                    path = self._path_to(vegetable_cell, allow_exits=False)
                    self.assertIsNotNone(path)
                    for cell in path[1:]:
                        self._step_to(cell)

                self.assertEqual(len(self.maze._collected), 4)
                path = self._path_to(exit_cell, allow_exits=True)
                self.assertIsNotNone(path)
                for cell in path[1:]:
                    self._step_to(cell)

                self.assertIs(self.maze.update(0), ScreenId.GROVE)
                self.assertEqual(self.maze.consume_completed_task_id(), "garden_maze")
                self.assertIs(self.maze.consume_garden_ending(), ending)

    def test_maze_draws_and_escape_returns_without_completing(self) -> None:
        self.maze.draw(pygame.Surface((800, 600)))
        self.maze.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))

        self.assertIs(self.maze.update(0), ScreenId.GROVE)
        self.assertIsNone(self.maze.consume_completed_task_id())

    def _step_to(self, target: tuple[int, int]) -> None:
        current_column, current_row = self.maze.player_cell
        target_column, target_row = target
        key_by_delta = {
            (0, -1): pygame.K_UP,
            (0, 1): pygame.K_DOWN,
            (-1, 0): pygame.K_LEFT,
            (1, 0): pygame.K_RIGHT,
        }
        delta = (target_column - current_column, target_row - current_row)
        self.assertIn(delta, key_by_delta)
        self.maze.handle_event(
            pygame.event.Event(pygame.KEYDOWN, key=key_by_delta[delta])
        )
        self.assertEqual(self.maze.player_cell, target)

    def _path_to(
        self,
        target: tuple[int, int],
        *,
        allow_exits: bool,
    ) -> list[tuple[int, int]] | None:
        queue = deque([self.maze.player_cell])
        previous: dict[tuple[int, int], tuple[int, int] | None] = {
            self.maze.player_cell: None
        }
        while queue:
            column, row = queue.popleft()
            if (column, row) == target:
                path = []
                current: tuple[int, int] | None = target
                while current is not None:
                    path.append(current)
                    current = previous[current]
                return list(reversed(path))
            for neighbor in (
                (column, row - 1),
                (column, row + 1),
                (column - 1, row),
                (column + 1, row),
            ):
                next_column, next_row = neighbor
                if not (
                    0 <= next_row < len(self.maze.MAZE)
                    and 0 <= next_column < len(self.maze.MAZE[next_row])
                ):
                    continue
                cell = self.maze.MAZE[next_row][next_column]
                if cell == "#" or (not allow_exits and cell in ("E", "F")):
                    continue
                if neighbor not in previous:
                    previous[neighbor] = (column, row)
                    queue.append(neighbor)
        return None


if __name__ == "__main__":
    unittest.main()
