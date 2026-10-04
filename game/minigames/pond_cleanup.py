from __future__ import annotations

import random
from dataclasses import dataclass

import pygame

from game.screens.screen import ScreenId


@dataclass(frozen=True)
class PondItem:
    name: str
    material: str
    destination: str


class PondCleanup:
    """Drag pond litter into the matching trash or recycling bin."""

    ITEMS = (
        PondItem("Bottle", "PLASTIC", "recycling"),
        PondItem("Drink can", "ALUMINUM", "recycling"),
        PondItem("Newspaper", "PAPER", "recycling"),
        PondItem("Glass jar", "GLASS", "recycling"),
        PondItem("Food wrapper", "MIXED", "trash"),
        PondItem("Plastic bag", "FILM PLASTIC", "trash"),
        PondItem("Old shoe", "FABRIC", "trash"),
        PondItem("Broken toy", "MIXED PLASTIC", "trash"),
    )
    ITEM_COUNT = 8

    def __init__(self, size: tuple[int, int]) -> None:
        pygame.font.init()
        self.size = size
        self.task_id = ""
        self.title = ""
        self.description = ""
        self.items: list[PondItem | None] = []
        self._item_fractions: list[tuple[float, float]] = []
        self._item_rects: list[pygame.Rect] = []
        self._drag_index: int | None = None
        self._drag_position: tuple[int, int] | None = None
        self._pending_screen: ScreenId | None = None
        self._completed_task_id: str | None = None
        self._feedback = ""
        self._feedback_seconds = 0.0
        self._update_layout()

    def start(self, task_id: str, title: str, description: str) -> None:
        if not task_id:
            raise ValueError("A pond-cleaning activity needs a task ID.")
        self.task_id = task_id
        self.title = title
        self.description = description
        self.items = list(self.ITEMS)
        random.shuffle(self.items)
        columns = 4
        self._item_fractions = [
            (
                (column + 0.5 + random.uniform(-0.12, 0.12)) / columns,
                row_y + random.uniform(-0.025, 0.025),
            )
            for row_y in (0.67, 0.84)
            for column in range(columns)
        ]
        random.shuffle(self._item_fractions)
        self._drag_index = None
        self._drag_position = None
        self._pending_screen = None
        self._completed_task_id = None
        self._feedback = ""
        self._feedback_seconds = 0.0
        self._update_layout()

    def _update_layout(self) -> None:
        width, height = self.size
        self.water_rect = pygame.Rect(
            max(16, round(width * 0.045)),
            max(98, round(height * 0.17)),
            width - 2 * max(16, round(width * 0.045)),
            max(100, round(height * 0.64)),
        )
        self.floor_y = self.water_rect.bottom - max(75, round(height * 0.13))
        self.trash_bin_rect = pygame.Rect(
            round(width * 0.19),
            round(height * 0.84),
            round(width * 0.25),
            max(58, round(height * 0.105)),
        )
        self.recycling_bin_rect = pygame.Rect(
            round(width * 0.56),
            round(height * 0.84),
            round(width * 0.25),
            max(58, round(height * 0.105)),
        )
        card_width = min(154, max(90, round(width * 0.15)))
        card_height = min(68, max(52, round(height * 0.105)))
        self._item_rects = []
        for fraction_x, fraction_y in self._item_fractions:
            center_x = self.water_rect.left + round(self.water_rect.width * fraction_x)
            center_y = self.water_rect.top + round(self.water_rect.height * fraction_y)
            self._item_rects.append(
                pygame.Rect(0, 0, card_width, card_height).move(
                    center_x - card_width // 2,
                    center_y - card_height // 2,
                )
            )

    def resize(self, size: tuple[int, int]) -> None:
        self.size = size
        self._update_layout()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._pending_screen = ScreenId.GROVE
            return
        if self._pending_screen is not None:
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_LEFT:
            for index in range(len(self.items) - 1, -1, -1):
                if (
                    self.items[index] is not None
                    and self._item_rects[index].collidepoint(event.pos)
                ):
                    self._drag_index = index
                    self._drag_position = event.pos
                    return
        elif event.type == pygame.MOUSEMOTION and self._drag_index is not None:
            self._drag_position = event.pos
        elif (
            event.type == pygame.MOUSEBUTTONUP
            and event.button == pygame.BUTTON_LEFT
            and self._drag_index is not None
        ):
            self._drop_item(event.pos)

    def _drop_item(self, position: tuple[int, int]) -> None:
        index = self._drag_index
        if index is None:
            return
        item = self.items[index]
        if item is None:
            self._drag_index = None
            self._drag_position = None
            return
        target = (
            "trash"
            if self.trash_bin_rect.collidepoint(position)
            else "recycling"
            if self.recycling_bin_rect.collidepoint(position)
            else None
        )
        self._drag_index = None
        self._drag_position = None
        if target is None:
            return
        if item.destination != target:
            self._feedback = "Not quite - check the material and try again."
            self._feedback_seconds = 2.0
            return

        self.items[index] = None
        self._feedback = f"{item.name} sorted!"
        self._feedback_seconds = 1.2
        if all(remaining is None for remaining in self.items):
            self._completed_task_id = self.task_id
            self._pending_screen = ScreenId.GROVE

    def update(self, delta_seconds: float) -> ScreenId | None:
        if self._feedback_seconds > 0:
            self._feedback_seconds = max(0.0, self._feedback_seconds - delta_seconds)
            if self._feedback_seconds == 0:
                self._feedback = ""
        destination = self._pending_screen
        self._pending_screen = None
        return destination

    def consume_completed_task_id(self) -> str | None:
        task_id = self._completed_task_id
        self._completed_task_id = None
        return task_id

    def draw(self, surface: pygame.Surface) -> None:
        width, height = surface.get_size()
        surface.fill((16, 34, 39))
        title_font = pygame.font.Font(None, max(30, int(min(width, height) * 0.064)))
        text_font = pygame.font.Font(None, max(17, int(min(width, height) * 0.032)))
        small_font = pygame.font.Font(None, max(14, int(min(width, height) * 0.024)))

        heading = title_font.render("Clean the lake", True, (236, 229, 197))
        surface.blit(heading, heading.get_rect(center=(width // 2, round(height * 0.065))))
        instruction = text_font.render(
            "Drag each item with your net into the matching bin.",
            True,
            (194, 216, 202),
        )
        surface.blit(instruction, instruction.get_rect(center=(width // 2, round(height * 0.125))))

        self._draw_lake(surface, small_font)
        remaining_count = sum(item is not None for item in self.items)
        counter = small_font.render(
            f"Items left: {remaining_count} / {self.ITEM_COUNT}",
            True,
            (223, 232, 205),
        )
        surface.blit(counter, counter.get_rect(midleft=(self.water_rect.left + 16, self.water_rect.top + 20)))
        self._draw_bin(surface, self.trash_bin_rect, "TRASH", (116, 82, 62), (211, 170, 129), small_font)
        self._draw_bin(
            surface,
            self.recycling_bin_rect,
            "RECYCLING",
            (55, 112, 81),
            (153, 208, 157),
            small_font,
        )

        for index, item in enumerate(self.items):
            if item is None or index == self._drag_index:
                continue
            self._draw_item(surface, self._item_rects[index], item, text_font, small_font)
        if self._drag_index is not None and self._drag_position is not None:
            item = self.items[self._drag_index]
            if item is not None:
                rect = self._item_rects[self._drag_index].copy()
                rect.center = self._drag_position
                self._draw_item(surface, rect, item, text_font, small_font, lifted=True)
                self._draw_net(surface, self._drag_position)

        if self._feedback:
            color = (255, 214, 151) if self._feedback.startswith("Not quite") else (171, 229, 174)
            feedback = text_font.render(self._feedback, True, color)
            surface.blit(feedback, feedback.get_rect(center=(width // 2, round(height * 0.965))))

    def _draw_lake(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        pygame.draw.rect(surface, (33, 107, 127), self.water_rect, border_radius=16)
        pygame.draw.rect(surface, (109, 183, 178), self.water_rect, 3, border_radius=16)
        waterline = self.water_rect.top + round(self.water_rect.height * 0.15)
        pygame.draw.rect(
            surface,
            (117, 202, 183),
            pygame.Rect(self.water_rect.left + 3, waterline, self.water_rect.width - 6, 5),
        )
        for index in range(5):
            x = self.water_rect.left + round((index + 0.5) * self.water_rect.width / 5)
            y = self.water_rect.top + round(self.water_rect.height * (0.27 + index % 2 * 0.055))
            pygame.draw.arc(surface, (66, 143, 157), pygame.Rect(x - 24, y, 48, 15), 0, 3.14, 2)

        pygame.draw.rect(
            surface,
            (102, 88, 62),
            pygame.Rect(self.water_rect.left, self.floor_y, self.water_rect.width, self.water_rect.bottom - self.floor_y),
            border_bottom_left_radius=14,
            border_bottom_right_radius=14,
        )
        pygame.draw.line(
            surface,
            (151, 130, 85),
            (self.water_rect.left, self.floor_y),
            (self.water_rect.right, self.floor_y),
            4,
        )
        for index in range(10):
            x = self.water_rect.left + 18 + index * max(1, (self.water_rect.width - 36) // 9)
            y = self.floor_y + 13 + (index * 17) % max(20, self.water_rect.bottom - self.floor_y - 18)
            pygame.draw.circle(surface, (125, 109, 74), (x, y), 3 + index % 3)
        label = font.render("LAKE BED", True, (229, 215, 171))
        surface.blit(label, (self.water_rect.left + 14, self.floor_y + 8))

    @staticmethod
    def _draw_bin(
        surface: pygame.Surface,
        rect: pygame.Rect,
        label: str,
        color: tuple[int, int, int],
        highlight: tuple[int, int, int],
        font: pygame.font.Font,
    ) -> None:
        pygame.draw.rect(surface, color, rect, border_radius=12)
        pygame.draw.rect(surface, highlight, rect, 3, border_radius=12)
        pygame.draw.rect(
            surface,
            highlight,
            pygame.Rect(rect.left + 8, rect.top + 7, rect.width - 16, 7),
            border_radius=4,
        )
        text = font.render(label, True, (248, 244, 218))
        surface.blit(text, text.get_rect(center=(rect.centerx, rect.centery + 5)))

    @staticmethod
    def _draw_item(
        surface: pygame.Surface,
        rect: pygame.Rect,
        item: PondItem,
        name_font: pygame.font.Font,
        material_font: pygame.font.Font,
        lifted: bool = False,
    ) -> None:
        fill = (239, 224, 180) if not lifted else (255, 244, 204)
        pygame.draw.rect(surface, (33, 57, 55), rect.move(3, 4), border_radius=9)
        pygame.draw.rect(surface, fill, rect, border_radius=9)
        pygame.draw.rect(surface, (102, 89, 62), rect, 2, border_radius=9)
        name = name_font.render(item.name, True, (48, 57, 47))
        material = material_font.render(item.material, True, (96, 100, 73))
        surface.blit(name, name.get_rect(center=(rect.centerx, rect.centery - 8)))
        surface.blit(material, material.get_rect(center=(rect.centerx, rect.centery + 13)))

    @staticmethod
    def _draw_net(surface: pygame.Surface, position: tuple[int, int]) -> None:
        x, y = position
        pygame.draw.circle(surface, (228, 236, 207), (x + 25, y - 17), 18, 3)
        pygame.draw.line(surface, (155, 116, 67), (x + 38, y - 5), (x + 56, y + 15), 5)
        pygame.draw.line(surface, (196, 172, 118), (x + 12, y - 27), (x + 38, y - 7), 1)
        pygame.draw.line(surface, (196, 172, 118), (x + 11, y - 6), (x + 37, y - 27), 1)
