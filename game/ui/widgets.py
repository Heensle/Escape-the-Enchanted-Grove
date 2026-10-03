import pygame


class Button:
    def __init__(self, rect: pygame.Rect, label: str) -> None:
        self.rect = rect
        self.label = label

    def contains(self, position: tuple[int, int]) -> bool:
        return self.rect.collidepoint(position)

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        pygame.draw.rect(
            surface,
            (20, 38, 34, 235),
            self.rect,
            border_radius=max(8, int(self.rect.height * 0.23)),
        )
        pygame.draw.rect(
            surface,
            (209, 204, 165, 255),
            self.rect,
            width=max(1, int(self.rect.height * 0.03)),
            border_radius=max(8, int(self.rect.height * 0.23)),
        )
        label = font.render(self.label, True, (239, 233, 204))
        surface.blit(label, label.get_rect(center=self.rect.center))

    def draw_hover(self, surface: pygame.Surface) -> None:
        overlay = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        pygame.draw.rect(
            overlay,
            (225, 218, 177, 32),
            overlay.get_rect(),
            border_radius=max(8, int(self.rect.height * 0.23)),
        )
        surface.blit(overlay, self.rect.topleft)
