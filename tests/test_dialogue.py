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

    def test_empty_day_files_load_without_events(self) -> None:
        service = JsonDialogueService()

        self.assertEqual(
            tuple(event.id for event in service.get_events_for_day(1)),
            ("day_01.scene.intro", "day_01.scene.fall_asleep"),
        )
        self.assertEqual(service.get_events_for("scene.day_2"), ())
        self.assertEqual(service.get_events_for("scene.day_3"), ())
        self.assertEqual(service.get_events_for("scene.day_4"), ())
        self.assertEqual(service.get_events_for("scene.day_5"), ())

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
