from __future__ import annotations

import pygame

from game.screens.screen import ScreenId


class KeyRetrievalClicker:
    """Click the submerged key to pull it free and drain the pond plug."""

    REQUIRED_HITS = 12
    COMPLETION_SECONDS = 1.8

    def __init__(self, size: tuple[int, int]) -> None:
        pygame.font.init()
        self.size = size
        self.hits = 0
        self.completed = False
        self._completion_seconds = 0.0
        self._pending_screen: ScreenId | None = None
        self._update_layout()

    def _update_layout(self) -> None:
        width, height = self.size
        target_size = max(92, min(round(width * 0.16), round(height * 0.21)))
        self.key_rect = pygame.Rect(
            width // 2 - target_size // 2,
            round(height * 0.57) - target_size // 2,
            target_size,
            target_size,
        )
        self.plug_rect = pygame.Rect(
            width // 2 - target_size // 2,
            round(height * 0.71) - target_size // 2,
            target_size,
            target_size,
        )

    def resize(self, size: tuple[int, int]) -> None:
        self.size = size
        self._update_layout()

    def reset(self) -> None:
        self.hits = 0
        self.completed = False
        self._completion_seconds = 0.0
        self._pending_screen = None

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._pending_screen = ScreenId.GROVE
            return
        if (
            self.completed
            or event.type != pygame.MOUSEBUTTONDOWN
            or event.button != pygame.BUTTON_LEFT
            or not self.key_rect.collidepoint(event.pos)
        ):
            return

        self.hits += 1
        if self.hits >= self.REQUIRED_HITS:
            self.completed = True
            self._completion_seconds = self.COMPLETION_SECONDS

    def update(self, delta_seconds: float) -> ScreenId | None:
        if self.completed and self._pending_screen is None:
            self._completion_seconds = max(0.0, self._completion_seconds - delta_seconds)
            if self._completion_seconds == 0:
                self._pending_screen = ScreenId.GROVE
        destination = self._pending_screen
        self._pending_screen = None
        return destination

    def consume_completed_task_id(self) -> str | None:
        return "retrieve_key" if self.completed else None

    def draw(self, surface: pygame.Surface) -> None:
        width, height = surface.get_size()
        surface.fill((17, 39, 48))
        title_font = pygame.font.Font(None, max(32, int(min(width, height) * 0.075)))
        text_font = pygame.font.Font(None, max(19, int(min(width, height) * 0.034)))
        small_font = pygame.font.Font(None, max(16, int(min(width, height) * 0.027)))

        title = title_font.render("Retrieve the key", True, (238, 226, 190))
        surface.blit(title, title.get_rect(center=(width // 2, int(height * 0.13))))
        instruction_text = (
            "The key is free! The plug has been pulled and the lake is draining."
            if self.completed
            else "Click the key repeatedly to pull it free from the lake bed."
        )
        instruction = text_font.render(instruction_text, True, (186, 210, 197))
        surface.blit(instruction, instruction.get_rect(center=(width // 2, int(height * 0.23))))

        self._draw_cross_section(surface)
        if self.completed:
            self._draw_key(surface, self.key_rect, lifted=True)
            self._draw_plug(surface, self.plug_rect.center)
            drained = small_font.render("THE POND IS DRAINED", True, (247, 207, 130))
            surface.blit(drained, drained.get_rect(center=(width // 2, int(height * 0.83))))
        else:
            self._draw_key(surface, self.key_rect)
            progress = text_font.render(
                f"Pulls: {self.hits} / {self.REQUIRED_HITS}",
                True,
                (226, 228, 199),
            )
            surface.blit(progress, progress.get_rect(center=(width // 2, int(height * 0.82))))
            self._draw_progress(surface)
            self._draw_net(surface, pygame.mouse.get_pos())

    def _draw_cross_section(self, surface: pygame.Surface) -> None:
        width, height = surface.get_size()
        water = pygame.Rect(
            max(18, round(width * 0.1)),
            round(height * 0.32),
            width - 2 * max(18, round(width * 0.1)),
            round(height * 0.42),
        )
        pygame.draw.rect(surface, (35, 109, 127), water, border_radius=22)
        pygame.draw.rect(surface, (108, 182, 177), water, 3, border_radius=22)
        for index in range(6):
            y = water.top + 26 + index * max(1, water.height // 7)
            pygame.draw.arc(
                surface,
                (59, 139, 151),
                pygame.Rect(water.left + 22, y, water.width - 44, 18),
                0,
                3.14159,
                2,
            )
        bed = pygame.Rect(
            water.left,
            water.bottom - max(36, round(height * 0.075)),
            water.width,
            max(36, round(height * 0.075)),
        )
        pygame.draw.rect(surface, (111, 91, 60), bed, border_radius=10)
        pygame.draw.line(surface, (165, 139, 87), bed.topleft, bed.topright, 4)
        pygame.draw.ellipse(
            surface,
            (73, 69, 53),
            pygame.Rect(water.centerx - 46, bed.top - 12, 92, 25),
        )
        for x in range(bed.left + 24, bed.right - 8, 47):
            pygame.draw.circle(
                surface,
                (141, 117, 76),
                (x, bed.centery + (x % 11)),
                3 + x % 4,
            )

    @staticmethod
    def _draw_key(
        surface: pygame.Surface,
        rect: pygame.Rect,
        lifted: bool = False,
    ) -> None:
        color = (255, 221, 120) if lifted else (203, 169, 83)
        center = (rect.left + rect.width // 3, rect.centery)
        radius = max(15, rect.width // 6)
        stroke = max(6, rect.width // 18)
        pygame.draw.circle(surface, color, center, radius, stroke)
        pygame.draw.line(
            surface,
            color,
            (center[0] + radius - 2, center[1]),
            (rect.right - rect.width // 7, center[1]),
            stroke,
        )
        shaft_end = rect.right - rect.width // 7
        pygame.draw.line(
            surface,
            color,
            (shaft_end - rect.width // 5, center[1]),
            (shaft_end - rect.width // 5, center[1] + rect.height // 6),
            stroke,
        )
        pygame.draw.line(
            surface,
            color,
            (shaft_end - rect.width // 9, center[1]),
            (shaft_end - rect.width // 9, center[1] + rect.height // 9),
            stroke,
        )

    @staticmethod
    def _draw_plug(surface: pygame.Surface, center: tuple[int, int]) -> None:
        x, y = center
        pygame.draw.ellipse(surface, (66, 51, 41), pygame.Rect(x - 36, y - 12, 72, 24))
        pygame.draw.ellipse(surface, (144, 106, 66), pygame.Rect(x - 29, y - 9, 58, 17))
        pygame.draw.circle(surface, (75, 58, 43), (x, y), 6)
        pygame.draw.line(surface, (188, 151, 96), (x + 25, y - 8), (x + 42, y - 25), 5)

    def _draw_progress(self, surface: pygame.Surface) -> None:
        width, height = surface.get_size()
        bar_width = min(round(width * 0.42), 440)
        bar_height = max(10, round(height * 0.02))
        bar = pygame.Rect(width // 2 - bar_width // 2, round(height * 0.87), bar_width, bar_height)
        pygame.draw.rect(surface, (47, 71, 68), bar, border_radius=bar_height // 2)
        fill = bar.copy()
        fill.width = round(bar.width * self.hits / self.REQUIRED_HITS)
        if fill.width:
            pygame.draw.rect(
                surface,
                (215, 173, 82),
                fill,
                border_radius=bar_height // 2,
            )

    @staticmethod
    def _draw_net(surface: pygame.Surface, position: tuple[int, int]) -> None:
        x, y = position
        pygame.draw.circle(surface, (229, 234, 203), (x + 21, y - 15), 15, 3)
        pygame.draw.line(surface, (157, 117, 68), (x + 32, y - 5), (x + 49, y + 13), 5)
