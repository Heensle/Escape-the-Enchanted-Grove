from __future__ import annotations

import pygame

from game.screens.screen import ScreenId


class LockBreakClicker:
    """Click the lock with the hammer until it breaks."""

    REQUIRED_HITS = 10

    def __init__(self, size: tuple[int, int]) -> None:
        pygame.font.init()
        self.size = size
        self.hits = 0
        self.completed = False
        self._pending_screen: ScreenId | None = None
        self._update_layout()

    def _update_layout(self) -> None:
        width, height = self.size
        self.lock_rect = pygame.Rect(
            width // 2 - int(width * 0.09),
            height // 2 - int(height * 0.015),
            int(width * 0.18),
            int(height * 0.24),
        )

    def resize(self, size: tuple[int, int]) -> None:
        self.size = size
        self._update_layout()

    def reset(self) -> None:
        self.hits = 0
        self.completed = False
        self._pending_screen = None

    def handle_event(self, event: pygame.event.Event) -> None:
        if (
            self.completed
            or event.type != pygame.MOUSEBUTTONDOWN
            or event.button != pygame.BUTTON_LEFT
            or not self.lock_rect.collidepoint(event.pos)
        ):
            return

        self.hits += 1
        self.completed = self.hits >= self.REQUIRED_HITS
        if self.completed:
            self._pending_screen = ScreenId.GROVE

    def update(self, _delta_seconds: float) -> ScreenId | None:
        _ = _delta_seconds
        destination = self._pending_screen
        self._pending_screen = None
        return destination

    def draw(self, surface: pygame.Surface) -> None:
        width, height = surface.get_size()
        surface.fill((18, 34, 31))

        title_font = pygame.font.Font(None, max(32, int(min(width, height) * 0.075)))
        text_font = pygame.font.Font(None, max(20, int(min(width, height) * 0.035)))
        title = title_font.render("Break the lock", True, (238, 226, 190))
        surface.blit(title, title.get_rect(center=(width // 2, int(height * 0.16))))

        instruction_text = (
            "The lock is broken!"
            if self.completed
            else "Click the lock with your hammer"
        )
        instruction = text_font.render(instruction_text, True, (182, 199, 171))
        surface.blit(
            instruction,
            instruction.get_rect(center=(width // 2, int(height * 0.27))),
        )

        self._draw_lock(surface)
        self._draw_progress(surface, text_font)
        self._draw_hammer_cursor(surface, pygame.mouse.get_pos())

    def _draw_lock(self, surface: pygame.Surface) -> None:
        lock = self.lock_rect
        shackle_width = max(5, int(lock.width * 0.16))
        shackle = pygame.Rect(
            lock.centerx - lock.width // 4,
            lock.top - lock.height // 2,
            lock.width // 2,
            lock.height // 2,
        )
        pygame.draw.arc(
            surface,
            (183, 153, 91),
            shackle,
            0,
            3.14159,
            shackle_width,
        )
        body_color = (93, 105, 92) if self.completed else (157, 119, 55)
        pygame.draw.rect(surface, body_color, lock, border_radius=max(8, lock.width // 8))
        pygame.draw.rect(
            surface,
            (226, 194, 121),
            lock,
            width=max(2, lock.width // 35),
            border_radius=max(8, lock.width // 8),
        )

        keyhole_radius = max(4, lock.width // 16)
        pygame.draw.circle(
            surface,
            (44, 48, 39),
            (lock.centerx, lock.centery - keyhole_radius // 2),
            keyhole_radius,
        )
        pygame.draw.rect(
            surface,
            (44, 48, 39),
            pygame.Rect(
                lock.centerx - keyhole_radius // 2,
                lock.centery - keyhole_radius // 2,
                keyhole_radius,
                keyhole_radius * 2,
            ),
        )

        crack_count = min(self.hits, 5)
        for index in range(crack_count):
            start_x = lock.left + lock.width * (index + 1) // (crack_count + 1)
            start_y = lock.top + lock.height // 3
            offset = max(3, lock.width // 12)
            pygame.draw.lines(
                surface,
                (57, 51, 39),
                False,
                [
                    (start_x, start_y),
                    (start_x - offset // 2, start_y + offset),
                    (start_x + offset // 2, start_y + offset * 2),
                ],
                max(1, lock.width // 45),
            )

    def _draw_progress(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        if self.completed:
            return
        label = font.render(
            f"Hits: {self.hits} / {self.REQUIRED_HITS}",
            True,
            (210, 216, 187),
        )
        surface.blit(
            label,
            label.get_rect(center=(surface.get_width() // 2, self.lock_rect.bottom + 48)),
        )

        bar_width = min(int(surface.get_width() * 0.38), 420)
        bar_height = max(12, int(surface.get_height() * 0.022))
        bar = pygame.Rect(
            surface.get_width() // 2 - bar_width // 2,
            self.lock_rect.bottom + 72,
            bar_width,
            bar_height,
        )
        pygame.draw.rect(surface, (51, 69, 60), bar, border_radius=bar_height // 2)
        fill = bar.copy()
        fill.width = int(bar.width * self.hits / self.REQUIRED_HITS)
        if fill.width:
            pygame.draw.rect(
                surface,
                (204, 164, 80),
                fill,
                border_radius=bar_height // 2,
            )

    @staticmethod
    def _draw_hammer_cursor(
        surface: pygame.Surface,
        position: tuple[int, int],
    ) -> None:
        x, y = position
        handle_end = (x + 22, y + 25)
        pygame.draw.line(surface, (151, 104, 57), (x, y), handle_end, 7)
        pygame.draw.line(surface, (220, 181, 106), (x, y), handle_end, 3)
        pygame.draw.line(surface, (176, 185, 168), (x - 8, y - 5), (x + 9, y - 13), 8)
        pygame.draw.line(surface, (218, 222, 200), (x - 8, y - 5), (x + 9, y - 13), 3)
