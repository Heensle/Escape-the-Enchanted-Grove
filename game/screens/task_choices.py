from __future__ import annotations

import random

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
    """Drag gradient roof tiles from the tray into their matching board slots."""

    GRID_SIZE = 3
    GRADIENT_CORNERS = (
        (120, 48, 45),
        (245, 176, 79),
        (75, 43, 48),
        (184, 83, 48),
    )

    def start(self, task_id: str, title: str, description: str) -> None:
        super().start(task_id, title, description)
        self.tray: list[int | None] = list(range(self.GRID_SIZE * self.GRID_SIZE))
        random.shuffle(self.tray)
        if self.tray == list(range(len(self.tray))):
            self.tray[0], self.tray[1] = self.tray[1], self.tray[0]
        self.board: list[int | None] = [None] * len(self.tray)
        self.completed = False
        self._drag_piece: int | None = None
        self._drag_source: tuple[str, int] | None = None
        self._drag_position: tuple[int, int] | None = None
        self.placed_count = 0
        self._update_jigsaw_layout()

    def resize(self, size: tuple[int, int]) -> None:
        self.size = size
        self._update_jigsaw_layout()

    def _update_jigsaw_layout(self) -> None:
        width, height = self.size
        cell_size = min(round(width * 0.1), round(height * 0.14), 120)
        cell_size = max(1, cell_size)
        board_size = cell_size * self.GRID_SIZE
        gap = max(2, cell_size // 18)
        tray_size = board_size + gap * (self.GRID_SIZE - 1)
        preview_size = cell_size * 4 // 3
        panel_gap = max(12, cell_size // 4)
        total_width = preview_size + panel_gap + tray_size + panel_gap + board_size
        left = max(8, (width - total_width) // 2)
        board_left = left + preview_size + panel_gap + tray_size + panel_gap
        tray_left = left + preview_size + panel_gap
        board_top = max(8, (height - board_size) // 2 + round(height * 0.035))

        self.board_rect = pygame.Rect(
            board_left,
            board_top,
            board_size,
            board_size,
        )
        self.board_slot_rects = tuple(
            pygame.Rect(
                board_left + column * cell_size,
                board_top + row * cell_size,
                cell_size,
                cell_size,
            )
            for row in range(self.GRID_SIZE)
            for column in range(self.GRID_SIZE)
        )
        self.tray_slot_rects = tuple(
            pygame.Rect(
                tray_left + column * (cell_size + gap),
                board_top + row * (cell_size + gap),
                cell_size,
                cell_size,
            )
            for row in range(self.GRID_SIZE)
            for column in range(self.GRID_SIZE)
        )
        self.tray_rect = pygame.Rect(tray_left, board_top, tray_size, tray_size)
        self.preview_rect = pygame.Rect(
            left + (preview_size - preview_size) // 2,
            board_top + (board_size - preview_size) // 2,
            preview_size,
            preview_size,
        )
        self._make_gradient_art(cell_size, board_size)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._pending_screen = ScreenId.GROVE
            return
        if self.completed:
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_LEFT:
            self._pick_up_piece(event.pos)
        elif event.type == pygame.MOUSEMOTION and self._drag_piece is not None:
            self._drag_position = event.pos
        elif (
            event.type == pygame.MOUSEBUTTONUP
            and event.button == pygame.BUTTON_LEFT
            and self._drag_piece is not None
        ):
            self._drop_piece(event.pos)

    def _pick_up_piece(self, position: tuple[int, int]) -> None:
        for index, rect in enumerate(self.board_slot_rects):
            piece = self.board[index]
            if piece is not None and rect.collidepoint(position):
                self.board[index] = None
                self._begin_drag(piece, ("board", index), position)
                return
        for index, rect in enumerate(self.tray_slot_rects):
            piece = self.tray[index]
            if piece is not None and rect.collidepoint(position):
                self.tray[index] = None
                self._begin_drag(piece, ("tray", index), position)
                return

    def _begin_drag(
        self,
        piece: int,
        source: tuple[str, int],
        position: tuple[int, int],
    ) -> None:
        self._drag_piece = piece
        self._drag_source = source
        self._drag_position = position

    def _drop_piece(self, position: tuple[int, int]) -> None:
        piece = self._drag_piece
        source = self._drag_source
        if piece is None or source is None:
            return

        destination = self._slot_at(position, self.board_slot_rects)
        destination_kind = "board"
        if destination is None:
            destination = self._slot_at(position, self.tray_slot_rects)
            destination_kind = "tray"

        if destination is None:
            self._put_in_slot(source, piece)
        else:
            target_slots = self.board if destination_kind == "board" else self.tray
            displaced = target_slots[destination]
            target_slots[destination] = piece
            if displaced is not None:
                self._put_in_slot(source, displaced)

        self._drag_piece = None
        self._drag_source = None
        self._drag_position = None
        self.placed_count = sum(piece is not None for piece in self.board)
        if self.board == list(range(len(self.board))):
            self.completed = True
            self._complete_task()

    @staticmethod
    def _slot_at(
        position: tuple[int, int],
        rects: tuple[pygame.Rect, ...],
    ) -> int | None:
        return next(
            (index for index, rect in enumerate(rects) if rect.collidepoint(position)),
            None,
        )

    def _put_in_slot(self, source: tuple[str, int], piece: int) -> None:
        kind, index = source
        slots = self.board if kind == "board" else self.tray
        slots[index] = piece

    def _make_gradient_art(self, cell_size: int, board_size: int) -> None:
        self._tile_surfaces: list[pygame.Surface] = []
        guide = pygame.Surface((board_size, board_size))
        for y in range(board_size):
            global_y = y / max(1, board_size - 1)
            for x in range(board_size):
                global_x = x / max(1, board_size - 1)
                guide.set_at((x, y), self._gradient_color(global_x, global_y))
        for index in range(self.GRID_SIZE * self.GRID_SIZE):
            row, column = divmod(index, self.GRID_SIZE)
            tile_rect = pygame.Rect(
                column * cell_size,
                row * cell_size,
                cell_size,
                cell_size,
            )
            self._tile_surfaces.append(guide.subsurface(tile_rect).copy())
        self._guide_surface = pygame.transform.smoothscale(
            guide,
            self.preview_rect.size,
        )

    @classmethod
    def _gradient_color(cls, x: float, y: float) -> tuple[int, int, int]:
        top_left, top_right, bottom_left, bottom_right = cls.GRADIENT_CORNERS
        return tuple(
            round(
                (1 - y) * ((1 - x) * top + x * top_right_value)
                + y * ((1 - x) * bottom + x * bottom_right_value)
            )
            for top, top_right_value, bottom, bottom_right_value in zip(
                top_left,
                top_right,
                bottom_left,
                bottom_right,
            )
        )

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((18, 34, 31))
        title_font = pygame.font.Font(None, max(34, int(min(self.size) * 0.075)))
        text_font = pygame.font.Font(None, max(18, int(min(self.size) * 0.032)))
        title = title_font.render(self.title, True, (238, 226, 190))
        surface.blit(title, title.get_rect(center=(self.size[0] // 2, int(self.size[1] * 0.09))))
        instruction = text_font.render(
            "Drag each square into the matching spot. Use the gradient as your guide.",
            True,
            (182, 199, 171),
        )
        surface.blit(
            instruction,
            instruction.get_rect(center=(self.size[0] // 2, int(self.size[1] * 0.18))),
        )
        preview_font = pygame.font.Font(None, max(17, int(min(self.size) * 0.028)))
        self._draw_label(surface, preview_font, "REFERENCE", self.preview_rect.centerx)
        self._draw_label(surface, preview_font, "LOOSE PIECES", self.tray_rect.centerx)
        self._draw_label(surface, preview_font, "ROOF", self.board_rect.centerx)
        surface.blit(self._guide_surface, self.preview_rect)
        pygame.draw.rect(surface, (232, 214, 163), self.preview_rect, 2)
        self._draw_grid_lines(surface, self.preview_rect)
        self._draw_tray(surface)
        self._draw_board(surface)
        self._draw_dragged_piece(surface)
        hint_text = f"{self.placed_count} / {len(self.board)} pieces placed  |  Esc to leave"
        hint = preview_font.render(hint_text, True, (145, 165, 145))
        surface.blit(
            hint,
            hint.get_rect(center=(self.size[0] // 2, self.size[1] * 9 // 10)),
        )

    @staticmethod
    def _draw_label(
        surface: pygame.Surface,
        font: pygame.font.Font,
        text: str,
        center_x: int,
    ) -> None:
        label = font.render(text, True, (197, 204, 178))
        surface.blit(label, label.get_rect(center=(center_x, max(16, surface.get_height() * 0.29 - 36))))

    def _draw_grid_lines(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        for index in range(1, self.GRID_SIZE):
            x = rect.left + rect.width * index // self.GRID_SIZE
            y = rect.top + rect.height * index // self.GRID_SIZE
            pygame.draw.line(surface, (245, 218, 167), (x, rect.top), (x, rect.bottom), 1)
            pygame.draw.line(surface, (245, 218, 167), (rect.left, y), (rect.right, y), 1)

    def _draw_tray(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, (33, 49, 42), self.tray_rect, border_radius=8)
        for index, rect in enumerate(self.tray_slot_rects):
            pygame.draw.rect(surface, (52, 66, 55), rect, border_radius=4)
            piece = self.tray[index]
            if piece is not None:
                self._draw_piece(surface, piece, rect)

    def _draw_board(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, (36, 52, 43), self.board_rect, border_radius=5)
        for index, rect in enumerate(self.board_slot_rects):
            piece = self.board[index]
            if piece is None:
                pygame.draw.rect(surface, (26, 40, 35), rect)
                pygame.draw.rect(surface, (106, 126, 101), rect, 2)
                pygame.draw.line(
                    surface,
                    (58, 79, 65),
                    rect.topleft,
                    rect.bottomright,
                    1,
                )
            else:
                self._draw_piece(surface, piece, rect)
        pygame.draw.rect(surface, (183, 168, 125), self.board_rect, 2)

    def _draw_piece(
        self,
        surface: pygame.Surface,
        piece: int,
        rect: pygame.Rect,
    ) -> None:
        surface.blit(self._tile_surfaces[piece], rect)
        pygame.draw.rect(surface, (63, 48, 39), rect, 2)

    def _draw_dragged_piece(self, surface: pygame.Surface) -> None:
        if self._drag_piece is None or self._drag_position is None:
            return
        cell_size = self.board_slot_rects[0].width
        rect = pygame.Rect(0, 0, cell_size, cell_size)
        rect.center = self._drag_position
        rect.inflate_ip(6, 6)
        surface.blit(self._tile_surfaces[self._drag_piece], rect)
        pygame.draw.rect(surface, (250, 220, 159), rect, 3)
