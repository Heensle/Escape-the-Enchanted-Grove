import pygame

from game.screens.screen import ScreenId


class PlaceholderScreen:
    def __init__(
        self,
        size: tuple[int, int],
        title: str,
        next_screen: ScreenId | None = None,
    ) -> None:
        self.size = size
        self.title = title
        self.next_screen = next_screen
        self._pending_screen: ScreenId | None = None

    def resize(self, size: tuple[int, int]) -> None:
        self.size = size

    def handle_event(self, event: pygame.event.Event) -> None:
        if (
            self.next_screen is not None
            and event.type == pygame.KEYDOWN
            and event.key in (pygame.K_RETURN, pygame.K_SPACE)
        ):
            self._pending_screen = self.next_screen

    def update(self, _delta_seconds: float) -> ScreenId | None:
        _ = _delta_seconds
        destination = self._pending_screen
        self._pending_screen = None
        return destination

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((0, 0, 0))
        font = pygame.font.Font(None, max(24, int(min(self.size) * 0.055)))
        title = font.render(self.title, True, (186, 198, 168))
        surface.blit(title, title.get_rect(center=surface.get_rect().center))
        if self.next_screen is not None:
            hint_font = pygame.font.Font(None, max(16, int(min(self.size) * 0.028)))
            hint = hint_font.render("Press Enter to continue", True, (105, 119, 108))
            surface.blit(
                hint,
                hint.get_rect(
                    center=(
                        surface.get_width() // 2,
                        surface.get_height() // 2 + title.get_height(),
                    )
                ),
            )
