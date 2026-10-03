from __future__ import annotations

import math
import random
from pathlib import Path

import pygame

from game.screens.screen import ScreenId
from game.ui.widgets import Button


TITLE = "Escape the Enchanted Grove"
TITLE_BACKGROUND_PATH = (
    Path(__file__).resolve().parents[2] / "assets" / "images" / "title_background.png"
)
TRANSITION_SECONDS = 2.2


class TitleScreen:
    def __init__(self, size: tuple[int, int]) -> None:
        self.size = size
        self.background_image = self._load_background_image()
        self.background = pygame.Surface(size)
        self.gradient = pygame.Surface(size, pygame.SRCALPHA)
        self.ui = pygame.Surface(size, pygame.SRCALPHA)
        self.start_button = Button(pygame.Rect(0, 0, 0, 0), "Start Game")
        self.transition_elapsed = 0.0
        self.transition_started = False
        self._build_layers()

    def resize(self, size: tuple[int, int]) -> None:
        if size == self.size:
            return
        self.size = size
        self.background = pygame.Surface(size)
        self.gradient = pygame.Surface(size, pygame.SRCALPHA)
        self.ui = pygame.Surface(size, pygame.SRCALPHA)
        self._build_layers()

    def _load_background_image(self) -> pygame.Surface | None:
        if not TITLE_BACKGROUND_PATH.exists():
            return None
        return pygame.image.load(TITLE_BACKGROUND_PATH).convert()

    def _build_layers(self) -> None:
        self._build_background()
        self._build_gradient()
        self._build_ui()

    def _build_background(self) -> None:
        width, height = self.size
        if self.background_image is not None:
            image_width, image_height = self.background_image.get_size()
            scale = max(width / image_width, height / image_height)
            scaled_size = (
                math.ceil(image_width * scale),
                math.ceil(image_height * scale),
            )
            scaled = pygame.transform.smoothscale(self.background_image, scaled_size)
            crop = scaled.get_rect(center=(width // 2, height // 2))
            self.background.blit(scaled, crop)
            return

        for y in range(height):
            amount = y / max(1, height - 1)
            color = (
                int(18 + 20 * amount),
                int(32 + 24 * amount),
                int(42 + 8 * amount),
            )
            pygame.draw.line(self.background, color, (0, y), (width, y))

        pygame.draw.circle(
            self.background,
            (206, 218, 193),
            (int(width * 0.77), int(height * 0.24)),
            max(18, int(min(width, height) * 0.065)),
        )
        pygame.draw.circle(
            self.background,
            (35, 53, 57),
            (int(width * 0.80), int(height * 0.21)),
            max(16, int(min(width, height) * 0.061)),
        )

        pygame.draw.polygon(
            self.background,
            (28, 52, 51),
            [
                (0, int(height * 0.62)),
                (int(width * 0.22), int(height * 0.39)),
                (int(width * 0.43), int(height * 0.65)),
                (int(width * 0.68), int(height * 0.43)),
                (width, int(height * 0.67)),
                (width, height),
                (0, height),
            ],
        )
        pygame.draw.polygon(
            self.background,
            (15, 36, 34),
            [
                (0, int(height * 0.76)),
                (int(width * 0.28), int(height * 0.57)),
                (int(width * 0.52), int(height * 0.78)),
                (int(width * 0.78), int(height * 0.55)),
                (width, int(height * 0.74)),
                (width, height),
                (0, height),
            ],
        )

        rng = random.Random(17)
        for index in range(13):
            x = int(width * index / 12)
            tree_height = int(height * (0.25 + rng.random() * 0.19))
            base_y = int(height * (0.84 + rng.random() * 0.13))
            half_width = max(20, int(tree_height * 0.29))
            pygame.draw.rect(
                self.background,
                (9, 25, 25),
                (x - max(4, half_width // 9), base_y - tree_height // 3, 10, tree_height),
            )
            for tier in range(3):
                top = base_y - tree_height + tier * tree_height // 4
                tier_width = half_width * (tier + 1) // 2
                pygame.draw.polygon(
                    self.background,
                    (10 + tier, 30 + tier * 2, 29 + tier),
                    [
                        (x, top),
                        (x - tier_width, top + tree_height // 2),
                        (x + tier_width, top + tree_height // 2),
                    ],
                )

        for _ in range(34):
            x = rng.randrange(width)
            y = rng.randrange(int(height * 0.25), int(height * 0.82))
            radius = rng.choice((1, 1, 2))
            pygame.draw.circle(self.background, (154, 190, 139), (x, y), radius)

    def _build_gradient(self) -> None:
        width, height = self.size
        start_y = int(height * 0.43)
        for y in range(start_y, height):
            amount = (y - start_y) / max(1, height - start_y - 1)
            alpha = int(238 * amount * amount)
            pygame.draw.line(self.gradient, (0, 0, 0, alpha), (0, y), (width, y))

    def _build_ui(self) -> None:
        width, height = self.size
        scale = max(0.35, min(1.4, min(width / 1280, height / 720)))
        center_x = width // 2
        title_color = (239, 233, 204)
        subtitle_color = (186, 198, 168)
        kicker_font = pygame.font.Font(None, max(13, int(27 * scale)))
        title_size = max(24, int(86 * scale))
        title_font = pygame.font.Font(None, title_size)
        while title_size > 16 and title_font.size("Enchanted Grove")[0] > width * 0.88:
            title_size -= 1
            title_font = pygame.font.Font(None, title_size)
        button_font = pygame.font.Font(None, max(18, int(35 * scale)))
        hint_font = pygame.font.Font(None, max(13, int(22 * scale)))

        kicker = kicker_font.render(
            "A TALE OF THE WILD AND WONDROUS",
            True,
            subtitle_color,
        )
        self.ui.blit(kicker, kicker.get_rect(center=(center_x, int(height * 0.18))))

        title_center_y = int(height * 0.39)
        title_line_spacing = int(title_size * 1.12)
        for line, center_y in (
            ("Escape the", title_center_y - title_line_spacing // 2),
            ("Enchanted Grove", title_center_y + title_line_spacing // 2),
        ):
            title = title_font.render(line, True, title_color)
            self.ui.blit(title, title.get_rect(center=(center_x, center_y)))

        button_width = min(int(width * 0.76), int(340 * scale))
        button_height = max(44, int(70 * scale))
        self.start_button = Button(
            pygame.Rect(
                center_x - button_width // 2,
                int(height * 0.62),
                button_width,
                button_height,
            ),
            "Start Game",
        )
        self.start_button.draw(self.ui, button_font)

        hint = hint_font.render("Press Enter to begin", True, subtitle_color)
        self.ui.blit(
            hint,
            hint.get_rect(
                center=(center_x, self.start_button.rect.bottom + int(22 * scale))
            ),
        )

    def _start_transition(self) -> None:
        if not self.transition_started:
            self.transition_started = True

    def reset(self) -> None:
        self.transition_elapsed = 0.0
        self.transition_started = False

    def handle_event(self, event: pygame.event.Event) -> None:
        if (
            event.type == pygame.KEYDOWN
            and event.key in (pygame.K_RETURN, pygame.K_SPACE)
        ):
            self._start_transition()
        elif (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.start_button.contains(event.pos)
        ):
            self._start_transition()

    def update(self, delta_seconds: float) -> ScreenId | None:
        if not self.transition_started:
            return None
        self.transition_elapsed += delta_seconds
        if self.transition_elapsed >= TRANSITION_SECONDS:
            return ScreenId.INTERACTION
        return None

    def draw(self, surface: pygame.Surface) -> None:
        _, height = self.size
        raw_progress = min(1.0, self.transition_elapsed / TRANSITION_SECONDS)
        progress = raw_progress * raw_progress * (3 - 2 * raw_progress)
        offset = int(height * progress)
        surface.fill((0, 0, 0))
        surface.blit(self.background, (0, -offset))
        surface.blit(self.gradient, (0, -offset))

        if progress < 1:
            self.ui.set_alpha(int(255 * (1 - progress)))
            surface.blit(self.ui, (0, -offset))
            self.ui.set_alpha(None)
            if (
                not self.transition_started
                and self.start_button.contains(pygame.mouse.get_pos())
            ):
                self.start_button.draw_hover(surface)
