from __future__ import annotations

from pathlib import Path

import pygame

from game.screens.screen import ScreenId
from game.state import GardenEnding


class GardenMaze:
    """Guide a tiny player sprite through the garden and deliver its harvest."""

    MAZE = (
        "###############",
        "#S....#.....#F#",
        "#.##..#.#.##..#",
        "#....##...#...#",
        "###......##...#",
        "#v.#.##..#v...#",
        "#..#....##....#",
        "#.##..v...#..#.#",
        "#....#....#v...#",
        "#E...#.......#.#",
        "###############",
    )
    VEGETABLES = ("Carrot", "Tomato", "Cabbage", "Beet")
    DIRECTIONS = {
        pygame.K_UP: (0, -1),
        pygame.K_w: (0, -1),
        pygame.K_DOWN: (0, 1),
        pygame.K_s: (0, 1),
        pygame.K_LEFT: (-1, 0),
        pygame.K_a: (-1, 0),
        pygame.K_RIGHT: (1, 0),
        pygame.K_d: (1, 0),
    }

    def __init__(self, size: tuple[int, int]) -> None:
        pygame.font.init()
        self.size = size
        asset_path = (
            Path(__file__).resolve().parents[2]
            / "assets_images"
            / "TheMainCharacter.png"
        )
        image = pygame.image.load(str(asset_path))
        bounds = image.get_bounding_rect(min_alpha=8)
        if bounds.width == 0 or bounds.height == 0:
            raise ValueError("Image asset has no visible pixels: Main character.png")
        self._player_image = image.subsurface(bounds).copy()
        self.task_id = ""
        self.title = ""
        self.description = ""
        self.player_cell = (0, 0)
        self._vegetable_cells: dict[tuple[int, int], str] = {}
        self._collected: set[str] = set()
        self._pending_screen: ScreenId | None = None
        self._completed_task_id: str | None = None
        self._garden_ending: GardenEnding | None = None
        self._message = ""
        self._update_layout()

    def start(self, task_id: str, title: str, description: str) -> None:
        if not task_id:
            raise ValueError("A garden maze needs a task ID.")
        self.task_id = task_id
        self.title = title
        self.description = description
        self.player_cell = self._find_cell("S")
        vegetable_positions = [
            (column, row)
            for row, line in enumerate(self.MAZE)
            for column, cell in enumerate(line)
            if cell == "v"
        ]
        if len(vegetable_positions) != len(self.VEGETABLES):
            raise ValueError("The garden maze must place each vegetable once.")
        self._vegetable_cells = dict(zip(vegetable_positions, self.VEGETABLES))
        self._collected = set()
        self._pending_screen = None
        self._completed_task_id = None
        self._garden_ending = None
        self._message = "Find all four vegetables, then choose an exit."
        self._update_layout()

    def _update_layout(self) -> None:
        width, height = self.size
        self.columns = len(self.MAZE[0])
        self.rows = len(self.MAZE)
        header_height = max(90, round(height * 0.17))
        footer_height = max(60, round(height * 0.12))
        margin = max(20, round(width * 0.04))
        self.cell_size = max(
            1,
            min(
                (width - margin * 2) // self.columns,
                (height - header_height - footer_height) // self.rows,
            ),
        )
        board_width = self.columns * self.cell_size
        board_height = self.rows * self.cell_size
        self.board_rect = pygame.Rect(
            (width - board_width) // 2,
            header_height + max(
                0,
                (height - header_height - footer_height - board_height) // 2,
            ),
            board_width,
            board_height,
        )

    def resize(self, size: tuple[int, int]) -> None:
        self.size = size
        self._update_layout()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            self._pending_screen = ScreenId.GROVE
            return
        direction = self.DIRECTIONS.get(event.key)
        if direction is not None:
            self._move_player(direction)

    def _move_player(self, direction: tuple[int, int]) -> None:
        if self._pending_screen is not None:
            return
        column, row = self.player_cell
        next_cell = (column + direction[0], row + direction[1])
        next_row, next_column = next_cell[1], next_cell[0]
        if not (
            0 <= next_row < self.rows
            and 0 <= next_column < self.columns
            and self.MAZE[next_row][next_column] != "#"
        ):
            return

        self.player_cell = next_cell
        vegetable = self._vegetable_cells.pop(next_cell, None)
        if vegetable is not None:
            self._collected.add(vegetable)
            self._message = f"You picked a {vegetable.lower()}!"

        cell = self.MAZE[next_row][next_column]
        if cell in ("E", "F"):
            if len(self._collected) != len(self.VEGETABLES):
                self._message = (
                    "Gather every vegetable before delivering the harvest."
                )
                return
            self._garden_ending = (
                GardenEnding.ELF if cell == "E" else GardenEnding.FAE
            )
            self._completed_task_id = self.task_id
            self._message = f"You delivered the harvest to the {cell.title()}!"
            self._pending_screen = ScreenId.GROVE

    @staticmethod
    def _find_cell(marker: str) -> tuple[int, int]:
        for row, line in enumerate(GardenMaze.MAZE):
            column = line.find(marker)
            if column >= 0:
                return column, row
        raise ValueError(f"The garden maze is missing its {marker!r} tile.")

    def update(self, _delta_seconds: float) -> ScreenId | None:
        _ = _delta_seconds
        destination = self._pending_screen
        self._pending_screen = None
        return destination

    def consume_completed_task_id(self) -> str | None:
        task_id = self._completed_task_id
        self._completed_task_id = None
        return task_id

    def consume_garden_ending(self) -> GardenEnding | None:
        ending = self._garden_ending
        self._garden_ending = None
        return ending

    def draw(self, surface: pygame.Surface) -> None:
        width, height = surface.get_size()
        surface.fill((17, 34, 28))
        title_font = pygame.font.Font(None, max(30, int(min(width, height) * 0.058)))
        text_font = pygame.font.Font(None, max(18, int(min(width, height) * 0.032)))
        small_font = pygame.font.Font(None, max(15, int(min(width, height) * 0.026)))
        heading = title_font.render("The Garden Maze", True, (241, 229, 190))
        surface.blit(heading, heading.get_rect(center=(width // 2, round(height * 0.055))))
        instructions = text_font.render(
            "Move with WASD or the arrow keys. Gather every vegetable and deliver it at either exit.",
            True,
            (194, 215, 186),
        )
        surface.blit(
            instructions,
            instructions.get_rect(center=(width // 2, round(height * 0.12))),
        )

        self._draw_maze(surface)
        status = f"Harvest: {len(self._collected)} / {len(self.VEGETABLES)}"
        inventory = small_font.render(status, True, (238, 220, 158))
        surface.blit(
            inventory,
            inventory.get_rect(midleft=(self.board_rect.left, self.board_rect.bottom + 20)),
        )
        message = small_font.render(self._message, True, (205, 219, 190))
        surface.blit(
            message,
            message.get_rect(midright=(self.board_rect.right, self.board_rect.bottom + 20)),
        )

    def _draw_maze(self, surface: pygame.Surface) -> None:
        for row, line in enumerate(self.MAZE):
            for column, cell in enumerate(line):
                rect = pygame.Rect(
                    self.board_rect.left + column * self.cell_size,
                    self.board_rect.top + row * self.cell_size,
                    self.cell_size,
                    self.cell_size,
                )
                if cell == "#":
                    pygame.draw.rect(surface, (47, 72, 49), rect)
                    pygame.draw.rect(surface, (65, 92, 59), rect, max(1, self.cell_size // 14))
                    continue
                pygame.draw.rect(surface, (128, 146, 91), rect)
                pygame.draw.rect(surface, (111, 133, 83), rect, 1)
                if cell in ("E", "F"):
                    color = (84, 146, 93) if cell == "E" else (133, 104, 169)
                    pygame.draw.rect(
                        surface,
                        color,
                        rect.inflate(-max(2, self.cell_size // 5), -max(2, self.cell_size // 5)),
                        border_radius=max(2, self.cell_size // 6),
                    )
                    label = pygame.font.Font(None, max(15, self.cell_size // 2)).render(
                        cell,
                        True,
                        (248, 239, 206),
                    )
                    surface.blit(label, label.get_rect(center=rect.center))
                elif cell == "v" and (column, row) in self._vegetable_cells:
                    self._draw_vegetable(surface, rect, self._vegetable_cells[(column, row)])

        player_rect = pygame.Rect(0, 0, self.cell_size * 3 // 4, self.cell_size * 9 // 10)
        player_rect.center = (
            self.board_rect.left + self.player_cell[0] * self.cell_size + self.cell_size // 2,
            self.board_rect.top + self.player_cell[1] * self.cell_size + self.cell_size // 2,
        )
        player = pygame.transform.smoothscale(self._player_image, player_rect.size)
        surface.blit(player, player_rect)

    @staticmethod
    def _draw_vegetable(
        surface: pygame.Surface,
        rect: pygame.Rect,
        vegetable: str,
    ) -> None:
        center_x, center_y = rect.center
        radius = max(4, rect.width // 4)
        colors = {
            "Carrot": (232, 116, 43),
            "Tomato": (204, 66, 56),
            "Cabbage": (159, 190, 99),
            "Beet": (143, 68, 91),
        }
        color = colors[vegetable]
        pygame.draw.ellipse(
            surface,
            color,
            pygame.Rect(center_x - radius, center_y - radius, radius * 2, radius * 2),
        )
        pygame.draw.polygon(
            surface,
            (82, 142, 70),
            (
                (center_x, center_y - radius),
                (center_x - radius // 2, center_y - radius * 2),
                (center_x, center_y - radius * 3 // 2),
                (center_x + radius // 2, center_y - radius * 2),
            ),
        )
