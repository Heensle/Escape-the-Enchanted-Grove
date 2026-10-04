import json
import tempfile
import unittest
from pathlib import Path

from game.dialogue.service import DialogueLine, JsonDialogueService


class JsonDialogueServiceTests(unittest.TestCase):
    def test_loads_exact_lines_and_retrieves_event_by_id(self) -> None:
        service = JsonDialogueService()

        event = service.get_event("day_01.scene.intro")

        self.assertEqual(event.day, 1)
        self.assertEqual(event.trigger, "scene.intro")
        self.assertEqual(
            event.lines,
            (
                DialogueLine(
                    "narrator",
                    "You are a lone adventurer that was traveling to the Capital "
                    "to make some money. Unfortunately, you’ve strayed from the "
                    "main path and ended up completely lost. Even worse, when "
                    "you were walking through the forest, you got captured by a "
                    "giant snake. Luckily, it loses interest in you after "
                    "realizing that you were human, but it still throws you "
                    "away, sending you off flying. You eventually land on top "
                    "of a small cottage. You’re alive and well, but the house’s "
                    "ceiling is completely destroyed and in front of you is a "
                    "very angry looking elf.",
                ),
            ),
        )
        with self.assertRaises(KeyError):
            service.get_event("IN HOUSE")
        sleep_event = service.get_event("day_01.scene.fall_asleep")
        self.assertEqual(sleep_event.day, 1)
        self.assertEqual(
            sleep_event.lines[0].text,
            "You’ve had a long day of dealing with mythical creatures. There’s "
            "so much to deal with, but you’re too tired to think about it. You "
            "set up your sleeping bag and quickly nod off to sleep.",
        )

    def test_day_files_load_events_for_their_day(self) -> None:
        service = JsonDialogueService()

        self.assertEqual(
            tuple(event.id for event in service.get_events_for_day(1)),
            (
                "day_01.scene.intro",
                "day_01.scene.elf_dialogue_1",
                "day_01.scene.elf_dialogue_2",
                "day_01.scene.elf_dialogue_3",
                "day_01.scene.elf_dialogue_4",
                "day_01.scene.fae_dialogue_1",
                "day_01.scene.fae_dialogue_2",
                "day_01.scene.fae_dialogue_3",
                "day_01.scene.fae_dialogue_4",
                "day_01.scene.fae_dialogue_5",
                "day_01.scene.fae_dialogue_6",
                "day_01.scene.fae_dialogue_7",
                "day_01.scene.fae_dialogue_8",
                "day_01.scene.fae_dialogue_9",
                "day_01.scene.fall_asleep",
            ),
        )
        self.assertEqual(
            tuple(
                event.id for event in service.get_events_for("scene.intro")
            ),
            (
                "day_01.scene.intro",
                "day_01.scene.elf_dialogue_1",
                "day_01.scene.elf_dialogue_2",
                "day_01.scene.elf_dialogue_3",
                "day_01.scene.elf_dialogue_4",
                "day_01.scene.fae_dialogue_1",
                "day_01.scene.fae_dialogue_2",
                "day_01.scene.fae_dialogue_3",
                "day_01.scene.fae_dialogue_4",
                "day_01.scene.fae_dialogue_5",
                "day_01.scene.fae_dialogue_6",
                "day_01.scene.fae_dialogue_7",
                "day_01.scene.fae_dialogue_8",
                "day_01.scene.fae_dialogue_9",
            ),
        )
        self.assertEqual(service.get_events_for("scene.day_2"), ())
        self.assertEqual(service.get_events_for("scene.day_3"), ())
        self.assertEqual(service.get_events_for("scene.day_4"), ())
        day_three_elf_events = tuple(
            event
            for event in service.get_events_for("interaction.elf")
            if event.day == 3
        )
        self.assertEqual(
            tuple(event.id for event in day_three_elf_events),
            tuple(f"day_03.scene.elf_dialogue_{index}" for index in range(1, 7)),
        )
        self.assertEqual(
            tuple(event.lines[0].speaker for event in day_three_elf_events),
            ("narrator", "elf", "narrator", "elf", "narrator", "elf"),
        )
        day_three_fae_events = tuple(
            event
            for event in service.get_events_for("interaction.fae")
            if event.day == 3
        )
        self.assertEqual(
            tuple(event.id for event in day_three_fae_events),
            tuple(f"day_03.scene.fae_dialogue_{index}" for index in range(1, 7)),
        )
        self.assertEqual(
            tuple(event.lines[0].speaker for event in day_three_fae_events),
            ("narrator", "fae", "narrator", "fae", "narrator", "fae"),
        )
        day_four_elf_events = tuple(
            event
            for event in service.get_events_for("interaction.elf")
            if event.day == 4
        )
        self.assertEqual(
            tuple(event.id for event in day_four_elf_events),
            tuple(f"day_04.scene.elf_dialogue_{index}" for index in range(1, 5)),
        )
        self.assertEqual(
            tuple(event.lines[0].speaker for event in day_four_elf_events),
            ("narrator", "elf", "narrator", "elf"),
        )
        day_four_fae_events = tuple(
            event
            for event in service.get_events_for("interaction.fae")
            if event.day == 4
        )
        self.assertEqual(
            tuple(event.id for event in day_four_fae_events),
            tuple(f"day_04.scene.fae_dialogue_{index}" for index in range(1, 5)),
        )
        self.assertEqual(
            tuple(event.lines[0].speaker for event in day_four_fae_events),
            ("narrator", "fae", "narrator", "fae"),
        )
        day_two_events = service.get_events_for("interaction.elf")
        self.assertEqual(
            tuple(event.id for event in day_two_events),
            tuple(f"day_02.scene.elf_dialogue_{index}" for index in range(1, 7)),
        )
        self.assertEqual(
            tuple(event.day for event in day_two_events),
            (2, 2, 2, 2, 2, 2),
        )
        self.assertEqual(
            tuple(event.lines[0].speaker for event in day_two_events),
            ("narrator", "elf", "narrator", "elf", "narrator", "elf"),
        )
        day_two_fae_events = service.get_events_for("interaction.fae")
        self.assertEqual(
            tuple(event.id for event in day_two_fae_events),
            tuple(f"day_02.scene.fae_dialogue_{index}" for index in range(1, 9)),
        )
        self.assertEqual(
            tuple(event.lines[0].speaker for event in day_two_fae_events),
            ("narrator", "fae", "narrator", "fae", "narrator", "fae", "narrator", "fae"),
        )
        self.assertEqual(
            {event.day for day in range(1, 5) for event in service.get_events_for_day(day)},
            {1, 2, 3, 4},
        )
        with tempfile.TemporaryDirectory() as directory:
            content_dir = Path(directory)
            self._write_day(content_dir / "day_05.json", 5, [])
            with self.assertRaisesRegex(ValueError, "between 1 and 4"):
                JsonDialogueService(content_dir)

    def test_retrieves_all_events_for_a_trigger_in_file_order(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            content_dir = Path(directory)
            self._write_day(
                content_dir / "day_02.json",
                2,
                [
                    self._event("first", "interaction.elf"),
                    self._event("second", "interaction.elf"),
                    self._event("other", "scene.intro"),
                ],
            )
            service = JsonDialogueService(content_dir)

        self.assertEqual(
            tuple(event.id for event in service.get_events_for("interaction.elf")),
            ("first", "second"),
        )
        self.assertEqual(service.get_events_for("interaction.fae"), ())

    def test_rejects_duplicate_event_ids_across_day_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            content_dir = Path(directory)
            self._write_day(content_dir / "day_01.json", 1, [self._event("repeat", "scene.one")])
            self._write_day(content_dir / "day_02.json", 2, [self._event("repeat", "scene.two")])

            with self.assertRaisesRegex(ValueError, "Duplicate dialogue event ID"):
                JsonDialogueService(content_dir)

    def test_unknown_event_id_raises_clear_error(self) -> None:
        service = JsonDialogueService()

        with self.assertRaisesRegex(KeyError, "not-a-real-event"):
            service.get_event("not-a-real-event")

    @staticmethod
    def _event(event_id: str, trigger: str) -> dict[str, object]:
        return {
            "id": event_id,
            "trigger": trigger,
            "lines": [{"speaker": "narrator", "text": "Exact authored line."}],
        }

    @staticmethod
    def _write_day(path: Path, day: int, events: list[dict[str, object]]) -> None:
        path.write_text(
            json.dumps({"day": day, "events": events}),
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
