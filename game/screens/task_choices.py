from __future__ import annotations

import pygame

from game.screens.screen import ScreenId
from game.tasks.daily import DailyTask


class TaskChoicesScreen:
    def __init__(self, size: tuple[int, int]) -> None:
        pygame.font.init()
        self.size = size
        self._options: tuple[DailyTask, ...] = ()
        self._unlocked = False
        self._completed_options: frozenset[str] = frozenset()
        self._pending_screen: ScreenId | None = None
        self._selected_option: str | None = None
        self._update_layout()

    def start(
        self,
        title: str,
        options: tuple[DailyTask, ...],
        unlocked: bool,
        completed_options: frozenset[str] = frozenset(),
        failed_options: frozenset[str] = frozenset(),
        chosen_options: frozenset[str] = frozenset(),
    ) -> None:
        if not options:
            raise ValueError("A task choice screen needs at least one option.")
        self.title = title
        self._options = options
        self._unlocked = unlocked
        self._completed_options = completed_options
        self._failed_options = failed_options
        self._chosen_options = chosen_options
        self._pending_screen = None
        self._selected_option = None
        self._update_layout()

    def _update_layout(self) -> None:
        width, height = self.size
        panel_width = min(round(width * 0.78), 760)
        row_height = max(74, round(height * 0.13))
        panel_height = max(240, row_height * (len(self._options) + 2))
        self.panel_rect = pygame.Rect(
            (width - panel_width) // 2,
            (height - panel_height) // 2,
            panel_width,
            panel_height,
        )
        self.option_rects = tuple(
            pygame.Rect(
                self.panel_rect.left + 24,
                self.panel_rect.top + 94 + index * row_height,
                self.panel_rect.width - 48,
                row_height - 10,
            )
            for index in range(len(self._options))
        )
        self._cancel_rect = pygame.Rect(
            self.panel_rect.left + 24,
            self.panel_rect.bottom - 54,
            self.panel_rect.width - 48,
            38,
        )

    def resize(self, size: tuple[int, int]) -> None:
        self.size = size
        self._update_layout()

    def _choose(self, index: int) -> None:
        if (
            not self._unlocked
            or not 0 <= index < len(self._options)
            or self._options[index].id in self._completed_options
            or self._options[index].id in self._failed_options
        ):
            return
        self._selected_option = self._options[index].id
        self._pending_screen = ScreenId.GROVE

    def _choose_next_available(self) -> None:
        for index, option in enumerate(self._options):
            if (
                option.id not in self._completed_options
                and option.id not in self._failed_options
            ):
                self._choose(index)
                return

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._pending_screen = ScreenId.GROVE
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE) and self._unlocked:
                self._choose_next_available()
            elif event.key in (pygame.K_1, pygame.K_2) and self._unlocked:
                self._choose(event.key - pygame.K_1)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_LEFT:
            for index, rect in enumerate(self.option_rects):
                if rect.collidepoint(event.pos):
                    self._choose(index)
                    return
            if self._cancel_rect.collidepoint(event.pos):
                self._pending_screen = ScreenId.GROVE

    def consume_selected_option(self) -> str | None:
        selected = self._selected_option
        self._selected_option = None
        return selected

    def update(self, _delta_seconds: float) -> ScreenId | None:
        _ = _delta_seconds
        destination = self._pending_screen
        self._pending_screen = None
        return destination

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((16, 31, 28))
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 96))
        surface.blit(overlay, (0, 0))
        pygame.draw.rect(surface, (30, 48, 39), self.panel_rect, border_radius=18)
        pygame.draw.rect(surface, (193, 181, 133), self.panel_rect, 3, border_radius=18)

        title_font = pygame.font.Font(None, max(30, int(min(self.size) * 0.055)))
        option_font = pygame.font.Font(None, max(21, int(min(self.size) * 0.034)))
        detail_font = pygame.font.Font(None, max(17, int(min(self.size) * 0.026)))
        title = title_font.render(self.title, True, (240, 232, 201))
        surface.blit(title, title.get_rect(midtop=(self.panel_rect.centerx, self.panel_rect.top + 22)))

        for option, rect in zip(self._options, self.option_rects):
            complete = option.id in self._completed_options
            failed = option.id in self._failed_options
            chosen = option.id in self._chosen_options
            available = self._unlocked and not complete and not failed
            fill = (53, 75, 57) if available else (48, 53, 49)
            foreground = (239, 233, 204) if available else (139, 145, 137)
            border = (196, 179, 122) if available else (91, 99, 91)
            pygame.draw.rect(surface, fill, rect, border_radius=10)
            pygame.draw.rect(surface, border, rect, 2, border_radius=10)
            heading = option_font.render(option.choice_title, True, foreground)
            detail = detail_font.render(option.description, True, foreground)
            surface.blit(heading, (rect.left + 16, rect.top + 10))
            surface.blit(detail, (rect.left + 16, rect.top + 10 + heading.get_height()))
            if complete:
                lock_text = "Completed"
            elif failed:
                lock_text = "Failed"
            elif chosen:
                lock_text = "Chosen"
            elif not self._unlocked:
                lock_text = "Talk to both characters first"
            else:
                lock_text = ""
            if lock_text:
                lock_label = detail_font.render(lock_text, True, foreground)
                surface.blit(
                    lock_label,
                    lock_label.get_rect(midright=(rect.right - 14, rect.centery)),
                )

        pygame.draw.rect(surface, (41, 55, 46), self._cancel_rect, border_radius=8)
        cancel = detail_font.render("Cancel (Esc)", True, (200, 205, 187))
        surface.blit(cancel, cancel.get_rect(center=self._cancel_rect.center))


class TaskActivityScreen:
    """Temporary task activity surface for mechanics that are not implemented yet."""

    def __init__(self, size: tuple[int, int]) -> None:
        pygame.font.init()
        self.size = size
        self.task_id = ""
        self.title = ""
        self.description = ""
        self._pending_screen: ScreenId | None = None
        self._completed_task_id: str | None = None
        self._update_layout()

    def start(self, task_id: str, title: str, description: str) -> None:
        if not task_id:
            raise ValueError("A task activity needs a task ID.")
        self.task_id = task_id
        self.title = title
        self.description = description
        self._pending_screen = None
        self._completed_task_id = None
        self._update_layout()

    def resize(self, size: tuple[int, int]) -> None:
        self.size = size
        self._update_layout()

    def _update_layout(self) -> None:
        width, height = self.size
        self.complete_rect = pygame.Rect(
            width // 2 - min(210, round(width * 0.25)),
            round(height * 0.68),
            min(420, round(width * 0.5)),
            max(52, round(height * 0.085)),
        )

    def _complete_task(self) -> None:
        self._completed_task_id = self.task_id
        self._pending_screen = ScreenId.GROVE

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._pending_screen = ScreenId.GROVE
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._complete_task()
        elif (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == pygame.BUTTON_LEFT
            and self.complete_rect.collidepoint(event.pos)
        ):
            self._complete_task()

    def update(self, _delta_seconds: float) -> ScreenId | None:
        _ = _delta_seconds
        destination = self._pending_screen
        self._pending_screen = None
        return destination

    def consume_completed_task_id(self) -> str | None:
        task_id = self._completed_task_id
        self._completed_task_id = None
        return task_id

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((18, 34, 31))
        title_font = pygame.font.Font(None, max(34, int(min(self.size) * 0.075)))
        text_font = pygame.font.Font(None, max(21, int(min(self.size) * 0.035)))
        title = title_font.render(self.title, True, (238, 226, 190))
        surface.blit(title, title.get_rect(center=(self.size[0] // 2, self.size[1] // 3)))
        description = text_font.render(self.description, True, (182, 199, 171))
        surface.blit(
            description,
            description.get_rect(center=(self.size[0] // 2, self.size[1] // 2)),
        )
        pygame.draw.rect(surface, (53, 75, 57), self.complete_rect, border_radius=10)
        pygame.draw.rect(
            surface,
            (196, 179, 122),
            self.complete_rect,
            2,
            border_radius=10,
        )
        complete = text_font.render("Complete task (temporary scaffold)", True, (239, 233, 204))
        surface.blit(complete, complete.get_rect(center=self.complete_rect.center))
        hint = text_font.render("Press Esc to leave without completing.", True, (145, 165, 145))
        surface.blit(
            hint,
            hint.get_rect(center=(self.size[0] // 2, self.size[1] * 4 // 5)),
        )


class JigsawScreen(TaskActivityScreen):
    """Roof-repair task entry point; the puzzle board can replace this scaffold."""

    def start(self, task_id: str, title: str, description: str) -> None:
        super().start(task_id, title, description)
        self._update_board_layout()

    def resize(self, size: tuple[int, int]) -> None:
        super().resize(size)
        self._update_board_layout()

    def _update_board_layout(self) -> None:
        width, height = self.size
        self.board_rect = pygame.Rect(
            width // 2 - round(width * 0.2),
            round(height * 0.35),
            round(width * 0.4),
            round(height * 0.25),
        )

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((18, 34, 31))
        title_font = pygame.font.Font(None, max(34, int(min(self.size) * 0.075)))
        text_font = pygame.font.Font(None, max(21, int(min(self.size) * 0.035)))
        title = title_font.render(self.title, True, (238, 226, 190))
        surface.blit(title, title.get_rect(center=(self.size[0] // 2, self.size[1] // 5)))
        description = text_font.render(self.description, True, (182, 199, 171))
        surface.blit(
            description,
            description.get_rect(center=(self.size[0] // 2, self.size[1] * 2 // 7)),
        )
        pygame.draw.rect(surface, (38, 54, 44), self.board_rect, border_radius=12)
        pygame.draw.rect(surface, (177, 163, 117), self.board_rect, 3, border_radius=12)
        font = pygame.font.Font(None, max(20, int(min(self.size) * 0.033)))
        label = font.render("Jigsaw board", True, (197, 204, 178))
        surface.blit(label, label.get_rect(center=self.board_rect.center))
        pygame.draw.rect(surface, (53, 75, 57), self.complete_rect, border_radius=10)
        pygame.draw.rect(
            surface,
            (196, 179, 122),
            self.complete_rect,
            2,
            border_radius=10,
        )
        complete = text_font.render(
            "Finish roof repair (temporary scaffold)",
            True,
            (239, 233, 204),
        )
        surface.blit(complete, complete.get_rect(center=self.complete_rect.center))
        hint = text_font.render("Press Esc to leave without completing.", True, (145, 165, 145))
        surface.blit(
            hint,
            hint.get_rect(center=(self.size[0] // 2, self.size[1] * 4 // 5)),
        )
