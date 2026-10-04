from __future__ import annotations

import pygame

from game.dialogue.gemini import GameContext, GeminiDialogueService
from game.dialogue.relationships import TASK_SCORE_CHANGE, RelationshipStore
from game.dialogue.service import JsonDialogueService
from game.minigames.garden_maze import GardenMaze
from game.minigames.lock_break_clicker import LockBreakClicker
from game.minigames.pond_cleanup import PondCleanup
from game.minigames.key_retrieval_clicker import KeyRetrievalClicker
from game.screens.epilogue import EpilogueScreen
from game.screens.interaction import InteractionScreen
from game.screens.grove import GroveScreen
from game.screens.screen import ScreenId, ScreenView
from game.screens.task_choices import JigsawScreen, TaskActivityScreen, TaskChoicesScreen
from game.screens.title import TITLE, TitleScreen
from game.state import MAX_DAYS
from game.state import GardenEnding, HouseAction, Location, PondAction
from game.tasks.daily import get_task, tasks_for_day, tasks_for_target
from game.tasks.results import TaskOutcome, TaskResult


class GameApp:
    DAY_FADE_SECONDS = 0.55
    QUIT_DIALOG_SIZE = (440, 190)

    DAY_LOCATIONS = {
        2: "house",
        3: "pond",
        4: "garden",
    }

    TASK_COMPLETION_CONSEQUENCES = {
        (2, "elf"): "You fixed up the roof, it looks good as new.",
        (2, "fae"): "You shattered the lock with the final hit.",
        (
            3,
            "elf",
        ): "You clear the rubble and pollution from the pond, leaving the water clean and the surrounding area free of trash.",
        (
            3,
            "fae",
        ): (
            "You retrieve the key from the bottom of the pond, but as you pull "
            "it free, the dam suddenly breaks loose, sending a rush of water "
            "downstream and leaving the pond completely drained. Trash and rubble "
            "is still scattered around the area. You carefully set the key down "
            "onto a stone and leave."
        ),
        (
            4,
            "elf",
        ): "You gather the fruits and vegetables and leave them next to the garden.",
        (
            4,
            "fae",
        ): "You gather the herbs and hide them away in a nearby bush.",
    }

    def __init__(self) -> None:
        pygame.init()
        self.surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.dialogue_service = JsonDialogueService()
        self.gemini_service = GeminiDialogueService()
        self.relationship_store = RelationshipStore()
        self.relationship_store.reset_to_initial_scores()
        self._elf_task_count = 0
        self._fae_task_count = 0
        self.day_number = 1
        self.screens: dict[ScreenId, ScreenView] = {}
        self._create_screens()
        self.current_screen_id = ScreenId.TITLE
        self.running = True
        self._quit_confirmation_open = False
        self._completed_event_ids: set[str] = set()
        self._sleep_after_dialogue = False
        self._interaction_character: str | None = None
        self._fade_phase: str | None = None
        self._fade_elapsed = 0.0
        self._fade_alpha = 0
        self._fade_destination: ScreenId | None = None

    def _create_screens(self) -> None:
        size = self.surface.get_size()
        self.title_screen = TitleScreen(size)
        self.lock_break_screen = LockBreakClicker(size)
        self.grove_screen = GroveScreen(size)
        self.interaction_screen = InteractionScreen(size)
        self.task_choices_screen = TaskChoicesScreen(size)
        self.task_activity_screen = TaskActivityScreen(size)
        self.jigsaw_screen = JigsawScreen(size)
        self.pond_cleanup_screen = PondCleanup(size)
        self.key_retrieval_screen = KeyRetrievalClicker(size)
        self.garden_maze_screen = GardenMaze(size)
        self.screens = {
            ScreenId.TITLE: self.title_screen,
            ScreenId.GROVE: self.grove_screen,
            ScreenId.INTERACTION: self.interaction_screen,
            ScreenId.LOCK_BREAK: self.lock_break_screen,
            ScreenId.TASK_CHOICES: self.task_choices_screen,
            ScreenId.TASK_ACTIVITY: self.task_activity_screen,
            ScreenId.JIGSAW: self.jigsaw_screen,
            ScreenId.CLEAN_POND: self.pond_cleanup_screen,
            ScreenId.PULL_KEY: self.key_retrieval_screen,
            ScreenId.GARDEN_MAZE: self.garden_maze_screen,
            ScreenId.EPILOGUE: EpilogueScreen(size),
        }

    @property
    def current_screen(self) -> ScreenView:
        return self.screens[self.current_screen_id]

    def _toggle_fullscreen(self) -> None:
        fullscreen = bool(self.surface.get_flags() & pygame.FULLSCREEN)
        flags = 0 if fullscreen else pygame.FULLSCREEN
        self.surface = pygame.display.set_mode((0, 0), flags)
        for screen in self.screens.values():
            screen.resize(self.surface.get_size())

    def _day_five_ending_key(self) -> str:
        if self._elf_task_count >= 3 and self._elf_task_count > self._fae_task_count:
            return "good"
        if self._fae_task_count >= 3 and self._fae_task_count > self._elf_task_count:
            return "bad"
        return "neutral"

    def _dialogue_trigger_for_day(self, trigger: str) -> str:
        if self.day_number != MAX_DAYS:
            return trigger
        ending_key = self._day_five_ending_key()
        if trigger in {"scene.intro", "scene.fall_asleep"}:
            return f"scene.{ending_key}_ending"
        if trigger in {"interaction.elf", "interaction.fae"}:
            return f"scene.{ending_key}_ending"
        return trigger

    def _record_completed_task_count(
        self,
        task_id: str,
        garden_ending: GardenEnding | None = None,
    ) -> None:
        task = get_task(task_id)
        giver = task.giver
        if giver == "elf":
            self._elf_task_count += 1
            return
        if giver == "fae":
            self._fae_task_count += 1
            return
        if task_id == "garden_maze" and garden_ending is not None:
            direction = garden_ending.name.lower()
            if direction == "elf":
                self._elf_task_count += 1
            elif direction == "fae":
                self._fae_task_count += 1

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.running = False
            return
        if self._quit_confirmation_open:
            self._handle_quit_confirmation_event(event)
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if (
                self.current_screen_id is ScreenId.INTERACTION
                and self.interaction_screen.is_conversation
            ):
                self.interaction_screen.handle_event(event)
                return
            if self.current_screen_id in (
                ScreenId.TASK_CHOICES,
                ScreenId.TASK_ACTIVITY,
                ScreenId.JIGSAW,
                ScreenId.CLEAN_POND,
                ScreenId.PULL_KEY,
                ScreenId.LOCK_BREAK,
                ScreenId.GARDEN_MAZE,
            ) or (
                self.current_screen_id is ScreenId.GROVE
                and self.grove_screen.sleep_confirmation_open
            ):
                self.current_screen.handle_event(event)
                return
            self._quit_confirmation_open = True
            return
        if (
            event.type == pygame.KEYDOWN
            and event.key == pygame.K_F11
            and self.current_screen_id is ScreenId.TITLE
        ):
            self._toggle_fullscreen()
            return

        if self._fade_phase is not None:
            return
        self.current_screen.handle_event(event)

    def update(self, delta_seconds: float) -> None:
        if self._fade_phase is not None:
            self._update_day_fade(delta_seconds)
            return

        previous_screen_id = self.current_screen_id
        destination = self.current_screen.update(delta_seconds)

        if previous_screen_id is ScreenId.GROVE:
            trigger = self.grove_screen.consume_dialogue_trigger()
            if trigger is not None:
                character = self._conversation_character_for_trigger(trigger)
                dialogue_trigger = self._dialogue_trigger_for_day(trigger)
                events = tuple(
                    event
                    for event in self.dialogue_service.get_events_for(dialogue_trigger)
                    if event.day == self.day_number
                    and event.id not in self._completed_event_ids
                )
                if not events:
                    if character is not None:
                        game_context = self._build_game_context(character)

                        self._interaction_character = character
                        self.interaction_screen.start_conversation(
                            character=character,
                            relationship_score=self.relationship_store.score(character),
                            submit_turn=self.gemini_service.submit_turn,
                            apply_relationship_delta=self.relationship_store.apply_delta,
                            destination=ScreenId.GROVE,
                            day_number=self.day_number,
                            game_context=game_context,
                        )
                        self.current_screen_id = ScreenId.INTERACTION
                    return
                self._interaction_character = character
                destination = (
                    ScreenId.TITLE
                    if self.day_number == MAX_DAYS
                    else ScreenId.GROVE
                )
                self.interaction_screen.start(events, destination)
                self.current_screen_id = ScreenId.INTERACTION
                return
            if self.grove_screen.consume_sleep_request():
                self._begin_sleep()
                return
            task_target = self.grove_screen.consume_task_target()
            if task_target is not None:
                self._start_task_choices(task_target)
                return

        if destination is None:
            return

        if (
            previous_screen_id is ScreenId.TITLE
            and destination is ScreenId.INTERACTION
        ):
            self._start_dialogue("scene.intro", ScreenId.GROVE)
            return

        if (
            previous_screen_id is ScreenId.INTERACTION
            and destination is ScreenId.GROVE
        ):
            completed_event_ids = self.interaction_screen.consume_completed_event_ids()
            self._completed_event_ids.update(completed_event_ids)
            completed_character = (
                self.interaction_screen.consume_completed_conversation_character()
            )
            if self._interaction_character is not None:
                if (
                    completed_event_ids
                    or completed_character == self._interaction_character
                ):
                    self.grove_screen.mark_character_talked(
                        self._interaction_character
                    )
                self._interaction_character = None
            if self._sleep_after_dialogue:
                self._sleep_after_dialogue = False
                self._start_day_fade(destination)
                return
            self.current_screen_id = destination
            return

        if (
            previous_screen_id is ScreenId.TASK_CHOICES
            and destination is ScreenId.GROVE
        ):
            self.current_screen_id = ScreenId.GROVE
            selected_option = self.task_choices_screen.consume_selected_option()
            if selected_option is not None:
                self._start_selected_task(selected_option)
            return

        if destination is ScreenId.TITLE:
            self.title_screen.reset()
        elif destination is ScreenId.LOCK_BREAK:
            self.lock_break_screen.reset()
        elif destination is ScreenId.PULL_KEY:
            self.key_retrieval_screen.reset()
        elif destination is ScreenId.GROVE and previous_screen_id in (
            ScreenId.TASK_ACTIVITY,
            ScreenId.JIGSAW,
            ScreenId.CLEAN_POND,
            ScreenId.PULL_KEY,
            ScreenId.GARDEN_MAZE,
        ):
            if previous_screen_id is ScreenId.TASK_ACTIVITY:
                task_screen = self.task_activity_screen
            elif previous_screen_id is ScreenId.JIGSAW:
                task_screen = self.jigsaw_screen
            elif previous_screen_id is ScreenId.CLEAN_POND:
                task_screen = self.pond_cleanup_screen
            elif previous_screen_id is ScreenId.GARDEN_MAZE:
                task_screen = self.garden_maze_screen
            else:
                task_screen = self.key_retrieval_screen
            completed_task_id = task_screen.consume_completed_task_id()
            garden_ending = (
                task_screen.consume_garden_ending()
                if previous_screen_id is ScreenId.GARDEN_MAZE
                else None
            )
            if completed_task_id is not None:
                self.grove_screen.complete_task(completed_task_id)
                self._record_completed_task_count(completed_task_id, garden_ending)
                if garden_ending is not None:
                    self.grove_screen.record_character_choice(
                        garden_ending.name.lower()
                    )
                relationship_message = self._record_task_relationship(
                    completed_task_id,
                    TaskOutcome.COMPLETED,
                    garden_ending,
                )
                self.grove_screen.show_message(
                    f"Completed: {get_task(completed_task_id).label}. "
                    f"{relationship_message}"
                )
            else:
                task_id = self._task_id_for_screen(previous_screen_id)
                if task_id is not None:
                    relationship_message = self._record_task_relationship(
                        task_id,
                        TaskOutcome.CANCELLED,
                    )
                    self.grove_screen.show_message(
                        f"You left the task unfinished. {relationship_message}"
                    )
                else:
                    self.grove_screen.show_message("You left the task unfinished.")
        elif (
            destination is ScreenId.GROVE
            and previous_screen_id is ScreenId.LOCK_BREAK
        ):
            if self.lock_break_screen.completed:
                self.grove_screen.complete_task("break_gate_lock")
                self._record_completed_task_count("break_gate_lock")
                relationship_message = self._record_task_relationship(
                    "break_gate_lock",
                    TaskOutcome.COMPLETED,
                )
                self.grove_screen.show_message(
                    f"You broke the gate lock. {relationship_message}"
                )
            else:
                relationship_message = self._record_task_relationship(
                    "break_gate_lock",
                    TaskOutcome.CANCELLED,
                )
                self.grove_screen.show_message(
                    f"You left the task unfinished. {relationship_message}"
                )
        self.current_screen_id = destination

    def _begin_sleep(self) -> None:
        dialogue_trigger = self._dialogue_trigger_for_day("scene.fall_asleep")
        sleep_events = tuple(
            event
            for event in self.dialogue_service.get_events_for(dialogue_trigger)
            if event.day == self.day_number
            and event.id not in self._completed_event_ids
        )
        if sleep_events:
            self.interaction_screen.start(sleep_events, ScreenId.GROVE)
            self._sleep_after_dialogue = True
            self.current_screen_id = ScreenId.INTERACTION
            return
        self._start_day_fade(ScreenId.GROVE)

    def _start_task_choices(self, target: str) -> None:
        titles = {
            "hammer": "Choose how to use the hammer",
            "net": "Choose how to use the net",
            "garden": "The garden maze",
        }
        options = tasks_for_target(self.day_number, target)
        if not options:
            raise ValueError(
                f"No day {self.day_number} tasks are associated with {target!r}."
            )
        try:
            title = titles[target]
        except KeyError:
            raise ValueError(f"Unknown task target: {target!r}") from None
        self.task_choices_screen.start(
            title,
            options,
            unlocked=self.grove_screen.both_characters_talked,
            completed_options=self.grove_screen.completed_tasks,
            failed_options=self.grove_screen.failed_tasks,
            chosen_options=self.grove_screen.chosen_tasks,
        )
        self.current_screen_id = ScreenId.TASK_CHOICES

    def _start_selected_task(self, task_id: str) -> None:
        task = get_task(task_id)
        self.grove_screen.choose_task(task_id)
        if task_id == "repair_roof":
            self.jigsaw_screen.start(task.id, task.choice_title, task.description)
            self.current_screen_id = ScreenId.JIGSAW
        elif task_id == "clean_pond":
            self.pond_cleanup_screen.start(
                task.id,
                task.choice_title,
                task.description,
            )
            self.current_screen_id = ScreenId.CLEAN_POND
        elif task_id == "break_gate_lock":
            self.lock_break_screen.reset()
            self.current_screen_id = ScreenId.LOCK_BREAK
        elif task_id == "retrieve_key":
            self.key_retrieval_screen.reset()
            self.current_screen_id = ScreenId.PULL_KEY
        elif task_id == "garden_maze":
            self.garden_maze_screen.start(
                task.id,
                task.choice_title,
                task.description,
            )
            self.current_screen_id = ScreenId.GARDEN_MAZE
        else:
            self.task_activity_screen.start(
                task.id,
                task.choice_title,
                task.description,
            )
            self.current_screen_id = ScreenId.TASK_ACTIVITY

    @staticmethod
    def _task_id_for_screen(screen_id: ScreenId) -> str | None:
        return {
            ScreenId.TASK_ACTIVITY: "garden_maze",
            ScreenId.JIGSAW: "repair_roof",
            ScreenId.CLEAN_POND: "clean_pond",
            ScreenId.PULL_KEY: "retrieve_key",
            ScreenId.GARDEN_MAZE: "garden_maze",
        }.get(screen_id)

    def _record_task_relationship(
        self,
        task_id: str,
        outcome: TaskOutcome,
        garden_ending: GardenEnding | None = None,
    ) -> str:
        task = get_task(task_id)
        actions = {
            "repair_roof": (Location.HOUSE, HouseAction.REPAIR_ROOF),
            "break_gate_lock": (Location.HOUSE, HouseAction.BREAK_LOCK),
            "clean_pond": (Location.POND, PondAction.CLEAN_POND_AND_SORT_WASTE),
            "retrieve_key": (Location.POND, PondAction.RETRIEVE_KEY),
        }
        if task_id == "garden_maze":
            if outcome is not TaskOutcome.COMPLETED:
                return ""
            if garden_ending is None:
                raise ValueError("A completed garden maze must report its exit.")
            location, action = Location.GARDEN, garden_ending
            character = garden_ending.name.lower()
        else:
            if task.giver is None:
                return ""
            try:
                location, action = actions[task_id]
            except KeyError:
                raise ValueError(
                    f"Task {task_id!r} has no relationship outcome mapping."
                ) from None
            character = task.giver
        score = self.relationship_store.record_task_result(
            TaskResult(location=location, outcome=outcome, action=action)
        )
        delta = TASK_SCORE_CHANGE if outcome is TaskOutcome.COMPLETED else -TASK_SCORE_CHANGE
        return f"{character.title()} relationship {delta:+d} (now {score})."

    @staticmethod
    def _conversation_character_for_trigger(trigger: str) -> str | None:
        characters = {
            "interaction.elf": "elf",
            "interaction.fae": "fae",
        }
        return characters.get(trigger)

    def _build_game_context(self, character: str) -> GameContext:
        normalized_character = character.strip().lower()

        completed_task_ids = tuple(
            sorted(self.grove_screen.completed_tasks)
        )
        failed_task_ids = tuple(
            sorted(self.grove_screen.failed_tasks)
        )
        chosen_task_ids = tuple(
            sorted(self.grove_screen.chosen_tasks)
        )

        daily_tasks = tasks_for_day(self.day_number)

        npc_task = next(
            (
                task
                for task in daily_tasks
                if (task.giver or "").strip().lower() == normalized_character
            ),
            None,
        )

        completed_task = None

        for task_id in completed_task_ids:
            task = get_task(task_id)
            completed_task = task
            break

        completed_owner = None
        completed_consequence = "No task was completed today."

        if completed_task is not None:
            completed_owner = (
                completed_task.giver.strip().lower()
                if completed_task.giver
                else None
            )

            completed_consequence = self.TASK_COMPLETION_CONSEQUENCES.get(
                (self.day_number, completed_owner),
                "The completed task has no recorded consequence.",
            )

        if npc_task is None:
            npc_task_text = "No task assigned."
            npc_task_completed = False
            npc_task_consequence = "No task was assigned to this NPC today."
        else:
            npc_task_text = (
                f"{npc_task.label}: {npc_task.description}"
            )

            npc_task_completed = (
                npc_task.id in completed_task_ids
            )

            if npc_task_completed:
                npc_task_consequence = (
                    self.TASK_COMPLETION_CONSEQUENCES.get(
                        (self.day_number, normalized_character),
                        "The task was completed.",
                    )
                )
            elif npc_task.id in failed_task_ids:
                npc_task_consequence = (
                    "This task was marked as failed because "
                    "the player chose the other task."
                )
            elif npc_task.id in chosen_task_ids:
                npc_task_consequence = (
                    "The player chose this task, but it was not completed."
                )
            else:
                npc_task_consequence = (
                    "The player did not choose this task."
                )

        return GameContext(
            day=self.day_number,
            location=self.DAY_LOCATIONS.get(
                self.day_number,
                "grove",
            ),
            completed_tasks=completed_task_ids,
            failed_tasks=failed_task_ids,
            chosen_tasks=chosen_task_ids,
            completed_task=(
                completed_task.id
                if completed_task is not None
                else None
            ),
            completed_task_owner=completed_owner,
            completed_task_consequence=completed_consequence,
            npc_task=npc_task_text,
            npc_task_completed=npc_task_completed,
            npc_task_consequence=npc_task_consequence,
        )

    def draw(self) -> None:
        self.current_screen.draw(self.surface)
        if self._fade_alpha:
            overlay = pygame.Surface(self.surface.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, self._fade_alpha))
            self.surface.blit(overlay, (0, 0))
        if self._quit_confirmation_open:
            self._draw_quit_confirmation()
        pygame.display.flip()

    def _handle_quit_confirmation_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_n):
                self._quit_confirmation_open = False
            elif event.key in (pygame.K_RETURN, pygame.K_y):
                self.running = False
            return
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        _, yes_button, no_button = self._quit_confirmation_rects()
        if yes_button.collidepoint(event.pos):
            self.running = False
        elif no_button.collidepoint(event.pos):
            self._quit_confirmation_open = False

    def _quit_confirmation_rects(
        self,
    ) -> tuple[pygame.Rect, pygame.Rect, pygame.Rect]:
        width, height = self.surface.get_size()
        dialog = pygame.Rect(0, 0, *self.QUIT_DIALOG_SIZE)
        dialog.center = (width // 2, height // 2)
        button_width = 140
        button_height = 44
        button_y = dialog.bottom - 64
        yes_button = pygame.Rect(0, 0, button_width, button_height)
        yes_button.center = (dialog.centerx - 82, button_y)
        no_button = pygame.Rect(0, 0, button_width, button_height)
        no_button.center = (dialog.centerx + 82, button_y)
        return dialog, yes_button, no_button

    def _draw_quit_confirmation(self) -> None:
        overlay = pygame.Surface(self.surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.surface.blit(overlay, (0, 0))

        dialog, yes_button, no_button = self._quit_confirmation_rects()
        pygame.draw.rect(self.surface, (24, 39, 31), dialog, border_radius=14)
        pygame.draw.rect(
            self.surface,
            (177, 163, 115),
            dialog,
            width=2,
            border_radius=14,
        )
        title_font = pygame.font.Font(None, 38)
        hint_font = pygame.font.Font(None, 25)
        title = title_font.render("Leave the grove?", True, (237, 212, 146))
        title_rect = title.get_rect(center=(dialog.centerx, dialog.top + 48))
        self.surface.blit(title, title_rect)

        for button, label, color in (
            (yes_button, "Yes, quit", (130, 74, 57)),
            (no_button, "Keep playing", (63, 91, 65)),
        ):
            pygame.draw.rect(self.surface, color, button, border_radius=8)
            rendered = hint_font.render(label, True, (242, 237, 219))
            self.surface.blit(rendered, rendered.get_rect(center=button.center))

        hint = hint_font.render("Y: quit    N or Esc: cancel", True, (183, 198, 166))
        self.surface.blit(hint, hint.get_rect(center=(dialog.centerx, dialog.top + 90)))

    def _start_dialogue(self, trigger: str, destination: ScreenId) -> None:
        dialogue_trigger = self._dialogue_trigger_for_day(trigger)
        events = tuple(
            event
            for event in self.dialogue_service.get_events_for(dialogue_trigger)
            if event.day == self.day_number
        )
        if not events:
            raise ValueError(f"No dialogue is authored for trigger {trigger!r}.")
        if self.day_number == MAX_DAYS and trigger in {"scene.intro", "scene.fall_asleep"}:
            destination = ScreenId.TITLE
        self.interaction_screen.start(events, destination)
        self.current_screen_id = ScreenId.INTERACTION

    def _start_day_fade(self, destination: ScreenId) -> None:
        self._fade_destination = destination
        self._fade_elapsed = 0.0
        self._fade_alpha = 0
        self._fade_phase = "out"

    def _update_day_fade(self, delta_seconds: float) -> None:
        self._fade_elapsed = min(
            self._fade_elapsed + max(0.0, delta_seconds),
            self.DAY_FADE_SECONDS,
        )
        progress = self._fade_elapsed / self.DAY_FADE_SECONDS
        if self._fade_phase == "out":
            self._fade_alpha = round(255 * progress)
            if progress == 1:
                if self._fade_destination is None:
                    raise RuntimeError("Day fade has no destination screen.")
                if self.day_number >= MAX_DAYS:
                    self.current_screen_id = ScreenId.EPILOGUE
                else:
                    self.current_screen_id = self._fade_destination
                    self.day_number += 1
                    self.grove_screen.begin_day(self.day_number)
                self._completed_event_ids.clear()
                self._fade_phase = "in"
                self._fade_elapsed = 0.0
            return

        self._fade_alpha = round(255 * (1 - progress))
        if progress == 1:
            self._fade_phase = None
            self._fade_alpha = 0
            self._fade_destination = None

    def run(self) -> None:
        try:
            while self.running:
                delta_seconds = self.clock.tick(60) / 1000
                for event in pygame.event.get():
                    self.handle_event(event)
                self.update(delta_seconds)
                self.draw()
        finally:
            self.gemini_service.close()
            pygame.quit()
