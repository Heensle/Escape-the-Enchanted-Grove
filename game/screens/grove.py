from __future__ import annotations

import math
import random

import pygame

from game.screens.screen import ScreenId


class GroveScreen:
    """Playable top-down enchanted grove with generated placeholder scenery."""

    BASE_SIZE = (1600, 1000)
    PLAYER_SPEED = 300
    FOREST_BORDER = 105
    INTERACTION_RADIUS = 82

    FEATURES = (
        ("House", pygame.Rect(205, 150, 335, 245), "The house needs attention."),
        ("Pond", pygame.Rect(1050, 145, 330, 235), "The pond is waiting to be cleaned."),
        ("Garden", pygame.Rect(1040, 675, 360, 175), "A maze of food grows in the garden."),
        ("Gate", pygame.Rect(710, 850, 180, 55), "The gate leads out of the clearing."),
    )
    CHARACTERS = (
        ("Elf", (635, 345), "The Elf looks like they could use some help."),
        ("Fae", (950, 365), "The Fae watches you from the path."),
    )
    TOOLS = (
        ("Hammer", (585, 595), "The hammer is ready for the house lock."),
        ("Net", (1115, 555), "The net can help with things in the pond."),
    )

    def __init__(self, size: tuple[int, int]) -> None:
        pygame.font.init()
        self.size = size
        self._pressed_keys: set[int] = set()
        self._pending_screen: ScreenId | None = None
        self._message = "Explore the grove. Approach something and press E."
        self._message_seconds = 0.0
        self._setup_world((0.5, 0.5))

    def _setup_world(self, player_fraction: tuple[float, float]) -> None:
        width, height = self.size
        self.world_size = (
            max(self.BASE_SIZE[0], int(width * 1.45)),
            max(self.BASE_SIZE[1], int(height * 1.45)),
        )
        self.scale_x = self.world_size[0] / self.BASE_SIZE[0]
        self.scale_y = self.world_size[1] / self.BASE_SIZE[1]
        self.scale = min(self.scale_x, self.scale_y)
        self.forest_bounds = pygame.Rect(
            round(self.FOREST_BORDER * self.scale_x),
            round(self.FOREST_BORDER * self.scale_y),
            self.world_size[0] - round(2 * self.FOREST_BORDER * self.scale_x),
            self.world_size[1] - round(2 * self.FOREST_BORDER * self.scale_y),
        )
        self.feature_rects = {
            name: self._scale_rect(rect) for name, rect, _ in self.FEATURES
        }
        self.character_positions = {
            name: self._scale_point(position) for name, position, _ in self.CHARACTERS
        }
        self.tool_positions = {
            name: self._scale_point(position) for name, position, _ in self.TOOLS
        }
        self.player_position = pygame.Vector2(
            self.forest_bounds.left + self.forest_bounds.width * player_fraction[0],
            self.forest_bounds.top + self.forest_bounds.height * player_fraction[1],
        )
        self.player_radius = max(12, round(17 * self.scale))
        self.player_speed = self.PLAYER_SPEED * self.scale
        self.solid_rects = [
            self.feature_rects[name] for name in ("House", "Pond", "Garden", "Gate")
        ]
        self.solid_rects.extend(
            pygame.Rect(
                round(position[0] - 19 * self.scale),
                round(position[1] - 14 * self.scale),
                round(38 * self.scale),
                round(28 * self.scale),
            )
            for position in self.character_positions.values()
        )
        self.camera = pygame.Vector2()
        self.background = self._build_background()
        self._update_camera()

    def _scale_point(self, point: tuple[int, int]) -> tuple[int, int]:
        return round(point[0] * self.scale_x), round(point[1] * self.scale_y)

    def _scale_rect(self, rect: pygame.Rect) -> pygame.Rect:
        x, y = self._scale_point(rect.topleft)
        width, height = self._scale_point(rect.size)
        return pygame.Rect(x, y, width, height)

    def _build_background(self) -> pygame.Surface:
        background = pygame.Surface(self.world_size)
        background.fill((27, 57, 39))
        pygame.draw.rect(background, (99, 123, 70), self.forest_bounds)
        pygame.draw.rect(
            background,
            (118, 139, 79),
            self.forest_bounds.inflate(-round(38 * self.scale), -round(38 * self.scale)),
            border_radius=max(20, round(80 * self.scale)),
        )

        self._draw_paths(background)
        self._draw_features(background)
        self._draw_forest_edge(background)
        self._draw_ground_details(background)
        return background

    def _draw_paths(self, background: pygame.Surface) -> None:
        points = [
            self._scale_point(point)
            for point in ((800, 500), (690, 410), (470, 330), (365, 285))
        ]
        pygame.draw.lines(
            background,
            (143, 126, 82),
            False,
            points,
            max(16, round(92 * self.scale)),
        )
        pygame.draw.lines(
            background,
            (163, 145, 97),
            False,
            points,
            max(12, round(68 * self.scale)),
        )
        for path in (
            ((800, 500), (970, 420), (1120, 335)),
            ((800, 500), (990, 635), (1120, 730)),
            ((800, 500), (800, 720), (800, 865)),
            ((800, 500), (680, 575), (585, 595)),
            ((800, 500), (1035, 530), (1115, 555)),
        ):
            scaled = [self._scale_point(point) for point in path]
            pygame.draw.lines(
                background,
                (143, 126, 82),
                False,
                scaled,
                max(12, round(54 * self.scale)),
            )
            pygame.draw.lines(
                background,
                (163, 145, 97),
                False,
                scaled,
                max(8, round(36 * self.scale)),
            )

    def _draw_features(self, background: pygame.Surface) -> None:
        house = self.feature_rects["House"]
        pygame.draw.ellipse(
            background,
            (72, 89, 53),
            house.inflate(round(50 * self.scale_x), round(42 * self.scale_y)),
        )
        roof_points = [
            (house.left - round(13 * self.scale_x), house.top + round(72 * self.scale_y)),
            (house.centerx, house.top - round(25 * self.scale_y)),
            (house.right + round(13 * self.scale_x), house.top + round(72 * self.scale_y)),
        ]
        pygame.draw.polygon(background, (102, 59, 47), roof_points)
        pygame.draw.polygon(
            background,
            (156, 91, 62),
            [
                (house.left + round(12 * self.scale_x), house.top + round(70 * self.scale_y)),
                (house.centerx, house.top + round(5 * self.scale_y)),
                (house.right - round(12 * self.scale_x), house.top + round(70 * self.scale_y)),
            ],
        )
        pygame.draw.rect(
            background,
            (197, 166, 113),
            house,
            border_radius=max(5, round(15 * self.scale)),
        )
        pygame.draw.rect(
            background,
            (125, 80, 51),
            pygame.Rect(
                house.centerx - round(23 * self.scale_x),
                house.bottom - round(88 * self.scale_y),
                round(46 * self.scale_x),
                round(88 * self.scale_y),
            ),
            border_radius=max(4, round(8 * self.scale)),
        )
        for x_fraction in (0.19, 0.73):
            window = pygame.Rect(
                house.left + round(house.width * x_fraction),
                house.top + round(107 * self.scale_y),
                round(49 * self.scale_x),
                round(44 * self.scale_y),
            )
            pygame.draw.rect(background, (94, 147, 147), window, border_radius=4)
            pygame.draw.line(
                background,
                (231, 211, 157),
                window.midtop,
                window.midbottom,
                max(2, round(4 * self.scale)),
            )

        pond = self.feature_rects["Pond"]
        pygame.draw.ellipse(
            background,
            (62, 107, 108),
            pond.inflate(round(52 * self.scale_x), round(48 * self.scale_y)),
        )
        pygame.draw.ellipse(background, (62, 136, 150), pond)
        pygame.draw.ellipse(
            background,
            (118, 182, 174),
            pond.inflate(-round(28 * self.scale_x), -round(25 * self.scale_y)),
            width=max(2, round(5 * self.scale)),
        )
        for fraction in (0.28, 0.52, 0.73):
            x = pond.left + round(pond.width * fraction)
            y = pond.top + round(pond.height * (0.42 if fraction == 0.52 else 0.65))
            pygame.draw.ellipse(
                background,
                (166, 194, 139),
                pygame.Rect(x, y, round(36 * self.scale_x), round(17 * self.scale_y)),
            )

        garden = self.feature_rects["Garden"]
        pygame.draw.rect(
            background,
            (91, 111, 56),
            garden.inflate(round(20 * self.scale_x), round(20 * self.scale_y)),
            border_radius=max(5, round(12 * self.scale)),
        )
        pygame.draw.rect(
            background,
            (155, 133, 82),
            garden,
            width=max(2, round(7 * self.scale)),
            border_radius=max(4, round(9 * self.scale)),
        )
        for row in range(3):
            for column in range(6):
                x = garden.left + round((column + 0.7) * garden.width / 6)
                y = garden.top + round((row + 0.65) * garden.height / 3)
                pygame.draw.circle(
                    background,
                    (68 + (column % 2) * 20, 117 + row * 9, 58),
                    (x, y),
                    max(4, round(11 * self.scale)),
                )
                pygame.draw.circle(
                    background,
                    (203, 173, 93),
                    (x + round(5 * self.scale), y - round(4 * self.scale)),
                    max(2, round(4 * self.scale)),
                )

        gate = self.feature_rects["Gate"]
        post_width = max(8, round(20 * self.scale_x))
        pygame.draw.rect(
            background,
            (113, 76, 45),
            pygame.Rect(gate.left, gate.top, post_width, gate.height),
        )
        pygame.draw.rect(
            background,
            (113, 76, 45),
            pygame.Rect(gate.right - post_width, gate.top, post_width, gate.height),
        )
        pygame.draw.rect(
            background,
            (137, 91, 52),
            pygame.Rect(gate.left, gate.top, gate.width, max(8, round(18 * self.scale_y))),
        )

    def _draw_forest_edge(self, background: pygame.Surface) -> None:
        rng = random.Random(21)
        canopy_colors = ((24, 51, 36), (31, 66, 42), (39, 75, 46), (49, 83, 48))
        step_x = max(36, round(78 * self.scale_x))
        step_y = max(36, round(76 * self.scale_y))
        tree_radius = max(28, round(56 * self.scale))

        for x in range(-tree_radius, self.world_size[0] + tree_radius, step_x):
            for y in (
                range(-tree_radius, self.forest_bounds.top + tree_radius, step_y),
                range(
                    self.forest_bounds.bottom - tree_radius,
                    self.world_size[1] + tree_radius,
                    step_y,
                ),
            ):
                for row_y in y:
                    offset_x = rng.randint(-step_x // 3, step_x // 3)
                    offset_y = rng.randint(-step_y // 3, step_y // 3)
                    self._draw_tree(
                        background,
                        (x + offset_x, row_y + offset_y),
                        tree_radius + rng.randint(-8, 12),
                        rng.choice(canopy_colors),
                    )

        for y in range(self.forest_bounds.top, self.forest_bounds.bottom, step_y):
            for x in (
                range(-tree_radius, self.forest_bounds.left + tree_radius, step_x),
                range(
                    self.forest_bounds.right - tree_radius,
                    self.world_size[0] + tree_radius,
                    step_x,
                ),
            ):
                for column_x in x:
                    offset_x = rng.randint(-step_x // 3, step_x // 3)
                    offset_y = rng.randint(-step_y // 3, step_y // 3)
                    self._draw_tree(
                        background,
                        (column_x + offset_x, y + offset_y),
                        tree_radius + rng.randint(-8, 12),
                        rng.choice(canopy_colors),
                    )

    @staticmethod
    def _draw_tree(
        surface: pygame.Surface,
        center: tuple[int, int],
        radius: int,
        color: tuple[int, int, int],
    ) -> None:
        x, y = center
        pygame.draw.circle(surface, (22, 44, 32), (x + 5, y + 7), radius + 2)
        pygame.draw.circle(surface, color, (x, y), radius)
        pygame.draw.circle(
            surface,
            (color[0] + 12, color[1] + 15, color[2] + 8),
            (x - radius // 4, y - radius // 4),
            max(3, radius // 2),
        )

    def _draw_ground_details(self, background: pygame.Surface) -> None:
        rng = random.Random(8)
        for _ in range(300):
            x = rng.randint(self.forest_bounds.left + 10, self.forest_bounds.right - 10)
            y = rng.randint(self.forest_bounds.top + 10, self.forest_bounds.bottom - 10)
            if any(rect.inflate(30, 30).collidepoint((x, y)) for rect in self.feature_rects.values()):
                continue
            color = rng.choice(((125, 143, 82), (108, 132, 72), (139, 148, 83)))
            radius = max(1, round(rng.uniform(1, 3) * self.scale))
            pygame.draw.circle(background, color, (x, y), radius)

    def _player_rect(self, position: pygame.Vector2 | None = None) -> pygame.Rect:
        center = self.player_position if position is None else position
        diameter = self.player_radius * 2
        return pygame.Rect(
            round(center.x - self.player_radius),
            round(center.y - self.player_radius),
            diameter,
            diameter,
        )

    def _can_occupy(self, position: pygame.Vector2) -> bool:
        player = self._player_rect(position)
        return (
            self.forest_bounds.contains(player)
            and not any(player.colliderect(solid) for solid in self.solid_rects)
        )

    def _move(self, delta: pygame.Vector2) -> None:
        for axis in ("x", "y"):
            amount = getattr(delta, axis)
            if amount == 0:
                continue
            candidate = self.player_position.copy()
            setattr(candidate, axis, getattr(candidate, axis) + amount)
            if self._can_occupy(candidate):
                self.player_position = candidate

    def _interact(self) -> None:
        target = self._nearest_interactable()
        if target is None:
            self._set_message("There is nothing close enough to interact with.")
            return

        name, description = target
        if name == "Hammer":
            self._pressed_keys.clear()
            self._pending_screen = ScreenId.LOCK_BREAK
            return
        if name == "Net":
            self._set_message("You picked up the net. It will be useful at the pond.")
            return
        self._set_message(description)

    def _nearest_interactable(self) -> tuple[str, str] | None:
        candidates: list[tuple[str, tuple[int, int], str]] = []
        candidates.extend(
            (name, self._scale_point(position), message)
            for name, position, message in self.CHARACTERS
        )
        candidates.extend(
            (name, self._scale_point(position), message)
            for name, position, message in self.TOOLS
        )
        for name, _, message in self.FEATURES:
            rect = self.feature_rects[name]
            candidates.append(
                (
                    name,
                    (
                        min(max(round(self.player_position.x), rect.left), rect.right),
                        min(max(round(self.player_position.y), rect.top), rect.bottom),
                    ),
                    message,
                )
            )
        max_distance = self.INTERACTION_RADIUS * self.scale
        nearest = min(
            candidates,
            key=lambda item: math.dist(self.player_position, item[1]),
        )
        if math.dist(self.player_position, nearest[1]) > max_distance:
            return None
        return nearest[0], nearest[2]

    def _set_message(self, message: str) -> None:
        self._message = message
        self._message_seconds = 4.0

    def _update_camera(self) -> None:
        width, height = self.size
        self.camera.x = min(
            max(0, self.player_position.x - width / 2),
            max(0, self.world_size[0] - width),
        )
        self.camera.y = min(
            max(0, self.player_position.y - height / 2),
            max(0, self.world_size[1] - height),
        )

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            self._pressed_keys.add(event.key)
            if event.key in (pygame.K_e, pygame.K_RETURN):
                self._interact()
        elif event.type == pygame.KEYUP:
            self._pressed_keys.discard(event.key)

    def update(self, delta_seconds: float) -> ScreenId | None:
        delta_seconds = min(max(delta_seconds, 0), 0.1)
        direction = pygame.Vector2(
            int(pygame.K_RIGHT in self._pressed_keys or pygame.K_d in self._pressed_keys)
            - int(pygame.K_LEFT in self._pressed_keys or pygame.K_a in self._pressed_keys),
            int(pygame.K_DOWN in self._pressed_keys or pygame.K_s in self._pressed_keys)
            - int(pygame.K_UP in self._pressed_keys or pygame.K_w in self._pressed_keys),
        )
        if direction.length_squared():
            direction = direction.normalize()
            self._move(direction * self.player_speed * delta_seconds)
        if self._message_seconds > 0:
            self._message_seconds = max(0, self._message_seconds - delta_seconds)
            if self._message_seconds == 0:
                self._message = "Explore the grove. Approach something and press E."
        self._update_camera()
        destination = self._pending_screen
        self._pending_screen = None
        return destination

    def resize(self, size: tuple[int, int]) -> None:
        old_world_size = self.world_size
        fraction = (
            self.player_position.x / old_world_size[0],
            self.player_position.y / old_world_size[1],
        )
        self.size = size
        self._setup_world(fraction)

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.background, (-round(self.camera.x), -round(self.camera.y)))
        self._draw_tools(surface)
        self._draw_characters(surface)
        self._draw_player(surface)
        self._draw_world_labels(surface)
        self._draw_hud(surface)

    def _screen_point(self, point: tuple[int, int]) -> tuple[int, int]:
        return round(point[0] - self.camera.x), round(point[1] - self.camera.y)

    def _draw_tools(self, surface: pygame.Surface) -> None:
        hammer_x, hammer_y = self._screen_point(self.tool_positions["Hammer"])
        pygame.draw.line(
            surface,
            (126, 80, 45),
            (hammer_x, hammer_y + round(19 * self.scale)),
            (hammer_x + round(7 * self.scale), hammer_y - round(4 * self.scale)),
            max(4, round(7 * self.scale)),
        )
        pygame.draw.rect(
            surface,
            (182, 189, 169),
            pygame.Rect(
                hammer_x - round(10 * self.scale),
                hammer_y - round(10 * self.scale),
                round(23 * self.scale),
                round(12 * self.scale),
            ),
            border_radius=max(2, round(3 * self.scale)),
        )
        net_x, net_y = self._screen_point(self.tool_positions["Net"])
        pygame.draw.line(
            surface,
            (125, 85, 53),
            (net_x - round(10 * self.scale), net_y + round(20 * self.scale)),
            (net_x + round(7 * self.scale), net_y - round(7 * self.scale)),
            max(3, round(5 * self.scale)),
        )
        pygame.draw.ellipse(
            surface,
            (190, 206, 169),
            pygame.Rect(
                net_x - round(3 * self.scale),
                net_y - round(24 * self.scale),
                round(27 * self.scale),
                round(22 * self.scale),
            ),
            width=max(2, round(3 * self.scale)),
        )

    def _draw_characters(self, surface: pygame.Surface) -> None:
        for name, position in self.character_positions.items():
            x, y = self._screen_point(position)
            tint = (212, 190, 139) if name == "Elf" else (176, 163, 202)
            pygame.draw.ellipse(
                surface,
                (75, 82, 55),
                pygame.Rect(
                    x - round(18 * self.scale),
                    y + round(10 * self.scale),
                    round(36 * self.scale),
                    round(12 * self.scale),
                ),
            )
            pygame.draw.ellipse(
                surface,
                tint,
                pygame.Rect(
                    x - round(13 * self.scale),
                    y - round(15 * self.scale),
                    round(26 * self.scale),
                    round(30 * self.scale),
                ),
            )
            pygame.draw.circle(
                surface,
                (228, 195, 153),
                (x, y - round(19 * self.scale)),
                max(5, round(9 * self.scale)),
            )
            ear_offset = round(13 * self.scale)
            pygame.draw.polygon(
                surface,
                tint,
                [
                    (x - ear_offset, y - round(20 * self.scale)),
                    (x - round(22 * self.scale), y - round(31 * self.scale)),
                    (x - round(12 * self.scale), y - round(14 * self.scale)),
                ],
            )
            pygame.draw.polygon(
                surface,
                tint,
                [
                    (x + ear_offset, y - round(20 * self.scale)),
                    (x + round(22 * self.scale), y - round(31 * self.scale)),
                    (x + round(12 * self.scale), y - round(14 * self.scale)),
                ],
            )

    def _draw_player(self, surface: pygame.Surface) -> None:
        x, y = self._screen_point(
            (round(self.player_position.x), round(self.player_position.y))
        )
        pygame.draw.ellipse(
            surface,
            (53, 68, 45),
            pygame.Rect(
                x - self.player_radius,
                y + self.player_radius // 2,
                self.player_radius * 2,
                max(5, self.player_radius // 2),
            ),
        )
        pygame.draw.circle(surface, (73, 112, 132), (x, y), self.player_radius)
        pygame.draw.circle(
            surface,
            (229, 193, 148),
            (x, y - self.player_radius // 2),
            max(5, self.player_radius * 2 // 3),
        )
        pygame.draw.arc(
            surface,
            (93, 68, 49),
            pygame.Rect(
                x - self.player_radius,
                y - self.player_radius,
                self.player_radius * 2,
                self.player_radius,
            ),
            math.pi,
            2 * math.pi,
            max(3, self.player_radius // 3),
        )

    def _draw_world_labels(self, surface: pygame.Surface) -> None:
        font = pygame.font.Font(None, max(16, round(22 * self.scale)))
        labels = [
            (name, self._screen_point(rect.midtop), -round(15 * self.scale))
            for name, rect in self.feature_rects.items()
        ]
        labels.extend(
            (
                name,
                self._screen_point(position),
                -round(35 * self.scale),
            )
            for name, position in (*self.character_positions.items(), *self.tool_positions.items())
        )
        for text, point, y_offset in labels:
            label = font.render(text, True, (243, 234, 204))
            label_rect = label.get_rect(midbottom=(point[0], point[1] + y_offset))
            backing = label_rect.inflate(round(12 * self.scale), round(6 * self.scale))
            pygame.draw.rect(
                surface,
                (30, 43, 31),
                backing,
                border_radius=max(3, round(5 * self.scale)),
            )
            surface.blit(label, label_rect)

    def _draw_hud(self, surface: pygame.Surface) -> None:
        width, height = surface.get_size()
        padding = max(12, round(min(width, height) * 0.022))
        font = pygame.font.Font(None, max(20, int(min(width, height) * 0.032)))
        hint_font = pygame.font.Font(None, max(17, int(min(width, height) * 0.025)))
        panel = pygame.Surface((width - 2 * padding, padding * 3 + font.get_height()), pygame.SRCALPHA)
        panel.fill((20, 35, 27, 218))
        surface.blit(panel, (padding, height - panel.get_height() - padding))
        message = font.render(self._message, True, (240, 232, 201))
        surface.blit(message, (padding * 2, height - panel.get_height() + padding // 2))
        controls = hint_font.render(
            "Move: WASD / arrows     Interact: E     Esc: quit",
            True,
            (183, 198, 166),
        )
        surface.blit(controls, (padding * 2, height - padding - controls.get_height()))
        target = self._nearest_interactable()
        if target is not None:
            prompt = hint_font.render(f"E  {target[0]}", True, (252, 214, 128))
            surface.blit(
                prompt,
                prompt.get_rect(center=(width // 2, height - panel.get_height() - padding)),
            )
