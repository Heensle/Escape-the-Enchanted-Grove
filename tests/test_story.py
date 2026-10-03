import unittest

from game.tasks.results import TaskOutcome, TaskResult
from game.state import (
    Choice,
    GameState,
    GardenEnding,
    HouseAction,
    Location,
    PondAction,
)
from game.story import (
    Ending,
    apply_task_result,
    determine_ending,
    record_choice,
)


class StoryRulesTests(unittest.TestCase):
    def test_ending_waits_until_each_location_has_a_choice(self) -> None:
        state = record_choice(GameState(), Location.HOUSE, Choice.HELP_ELF)

        self.assertIsNone(determine_ending(state))

    def test_zero_fae_choices_is_good_ending(self) -> None:
        state = GameState(
            choices=tuple((location, Choice.HELP_ELF) for location in Location)
        )

        self.assertIs(determine_ending(state), Ending.GOOD)

    def test_one_or_two_fae_choices_are_neutral_endings(self) -> None:
        for fae_choice_count in (1, 2):
            with self.subTest(fae_choice_count=fae_choice_count):
                choices = tuple(
                    (
                        location,
                        Choice.HELP_FAE
                        if index < fae_choice_count
                        else Choice.HELP_ELF,
                    )
                    for index, location in enumerate(Location)
                )
                self.assertIs(
                    determine_ending(GameState(choices=choices)),
                    Ending.NEUTRAL,
                )

    def test_three_fae_choices_are_bad_ending(self) -> None:
        state = GameState(
            choices=tuple((location, Choice.HELP_FAE) for location in Location)
        )

        self.assertIs(determine_ending(state), Ending.BAD)

    def test_location_choice_can_only_be_recorded_once(self) -> None:
        state = record_choice(GameState(), Location.HOUSE, Choice.HELP_ELF)

        with self.assertRaises(ValueError):
            record_choice(state, Location.HOUSE, Choice.HELP_FAE)

    def test_cancelled_task_does_not_change_story_state(self) -> None:
        state = GameState()
        result = TaskResult(
            location=Location.HOUSE,
            outcome=TaskOutcome.CANCELLED,
            action=HouseAction.REPAIR_ROOF,
        )

        self.assertEqual(apply_task_result(state, result), state)

    def test_task_result_stores_its_selected_action(self) -> None:
        state = apply_task_result(
            GameState(),
            TaskResult(
                location=Location.POND,
                outcome=TaskOutcome.COMPLETED,
                action=PondAction.CLEAN_POND_AND_SORT_WASTE,
            ),
        )

        self.assertIs(state.pond_action, PondAction.CLEAN_POND_AND_SORT_WASTE)
        self.assertIsNone(state.house_action)
        self.assertIsNone(state.garden_ending)

    def test_task_rejects_an_action_for_an_unrelated_location(self) -> None:
        with self.assertRaises(ValueError):
            apply_task_result(
                GameState(),
                TaskResult(
                    location=Location.HOUSE,
                    outcome=TaskOutcome.COMPLETED,
                    action=PondAction.RETRIEVE_KEY,
                ),
            )

    def test_completed_task_requires_one_selected_action(self) -> None:
        with self.assertRaises(ValueError):
            apply_task_result(
                GameState(),
                TaskResult(
                    location=Location.GARDEN,
                    outcome=TaskOutcome.COMPLETED,
                ),
            )

    def test_garden_ending_is_one_of_two_exclusive_outcomes(self) -> None:
        state = apply_task_result(
            GameState(),
            TaskResult(
                location=Location.GARDEN,
                outcome=TaskOutcome.COMPLETED,
                action=GardenEnding.FAE,
            ),
        )

        self.assertIs(state.garden_ending, GardenEnding.FAE)


if __name__ == "__main__":
    unittest.main()
