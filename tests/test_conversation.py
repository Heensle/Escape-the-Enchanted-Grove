import io
import json
import tempfile
import unittest
from concurrent.futures import Future
from pathlib import Path
from urllib.error import HTTPError
from unittest.mock import patch

import pygame

from game.app import GameApp
from game.dialogue.gemini import (
    GeminiDialogueService,
    GeminiReply,
    relationship_response_style,
)
from game.dialogue.relationships import RelationshipStore
from game.screens.interaction import ConversationMessage, InteractionScreen
from game.screens.screen import ScreenId
from game.state import GardenEnding, HouseAction, Location
from game.tasks.results import TaskOutcome, TaskResult


class RelationshipStoreTests(unittest.TestCase):
    def test_new_relationships_start_at_character_specific_scores(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = RelationshipStore(Path(directory) / "relationships.json")

        self.assertEqual(store.score("elf"), -5)
        self.assertEqual(store.score("fae"), 5)

    def test_relationship_scores_are_saved_per_character(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "relationships.json"
            store = RelationshipStore(path)

            self.assertEqual(store.apply_delta("elf", 1), -4)
            self.assertEqual(store.apply_delta("fae", -1), 4)

            loaded = RelationshipStore(path)
            self.assertEqual(loaded.score("elf"), -4)
            self.assertEqual(loaded.score("fae"), 4)

    def test_conversation_changes_are_limited_to_plus_or_minus_one(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = RelationshipStore(Path(directory) / "relationships.json")

            for delta in (0, 2, -3, True):
                with self.subTest(delta=delta):
                    with self.assertRaisesRegex(ValueError, r"-1 or \+1"):
                        store.apply_delta("elf", delta)

    def test_task_results_change_selected_relationship_by_three(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = RelationshipStore(Path(directory) / "relationships.json")

            completed = TaskResult(
                Location.HOUSE,
                TaskOutcome.COMPLETED,
                HouseAction.REPAIR_ROOF,
            )
            not_completed = TaskResult(
                Location.GARDEN,
                TaskOutcome.CANCELLED,
                GardenEnding.FAE,
            )

            self.assertEqual(store.record_task_result(completed), -2)
            self.assertEqual(store.record_task_result(not_completed), 2)


class GeminiDialogueTests(unittest.TestCase):
    def test_sends_relationship_context_and_parses_reply(self) -> None:
        response_data = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": json.dumps(
                                    {
                                        "response": "The Fae smiles.",
                                        "relationship_delta": 1,
                                    }
                                )
                            }
                        ]
                    }
                }
            ]
        }
        with (
            patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}),
            patch(
                "game.dialogue.gemini.urlopen",
                return_value=io.BytesIO(
                    json.dumps(response_data).encode("utf-8")
                ),
            ) as urlopen,
        ):
            reply = GeminiDialogueService()._request_turn(
                "fae",
                "Hello.",
                7,
                (("You", "I can help with the gate."), ("Fae", "Can you?")),
            )

        request = urlopen.call_args.args[0]
        request_body = json.loads(request.data)
        prompt = request_body["contents"][0]["parts"][0]["text"]
        self.assertEqual(reply, GeminiReply("The Fae smiles.", 1))
        self.assertIn("relationship score (7", prompt)
        self.assertIn("Excited and manipulative", prompt)
        self.assertIn("exactly +1", prompt)
        self.assertIn("exactly -1", prompt)
        self.assertIn("Player: I can help with the gate.", prompt)
        self.assertIn("Fae: Can you?", prompt)
        self.assertIn("Player: Hello.", prompt)
        self.assertIn("gemini-3.5-flash-lite:generateContent", request.full_url)
        self.assertEqual(request.get_header("X-goog-api-key"), "test-key")
        self.assertNotIn("test-key", request.full_url)

    def test_default_model_is_the_high_throughput_flash_lite_model(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(
                GeminiDialogueService().model,
                "gemini-3.5-flash-lite",
            )

    def test_rejects_invalid_relationship_delta(self) -> None:
        response_data = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": json.dumps(
                                    {
                                        "response": "Hello.",
                                        "relationship_delta": 2,
                                    }
                                )
                            }
                        ]
                    }
                }
            ]
        }
        with (
            patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}),
            patch(
                "game.dialogue.gemini.urlopen",
                return_value=io.BytesIO(
                    json.dumps(response_data).encode("utf-8")
                ),
            ),
        ):
            with self.assertRaisesRegex(RuntimeError, "invalid relationship change"):
                GeminiDialogueService()._request_turn("elf", "Hello.", 0)

    def test_character_style_matches_each_relationship_band_boundary(self) -> None:
        expected_styles = (
            (-21, "Furious.", "Furious, rude, and trying to be convincing."),
            (-20, "Frustrated.", "Fake nice and desperate."),
            (-6, "Frustrated.", "Fake nice and desperate."),
            (-5, "Annoyed or polite.", "Caring and friendly."),
            (5, "Annoyed or polite.", "Caring and friendly."),
            (6, "Neutral or satisfied.", "Excited and manipulative."),
            (20, "Neutral or satisfied.", "Excited and manipulative."),
            (
                21,
                "Overjoyed and grateful.",
                "Giddy, snapping at the player, or ignoring them.",
            ),
        )
        for score, elf_style, fae_style in expected_styles:
            with self.subTest(score=score):
                self.assertEqual(
                    relationship_response_style("elf", score),
                    elf_style,
                )
                self.assertEqual(
                    relationship_response_style("fae", score),
                    fae_style,
                )

    def test_missing_api_key_is_reported(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "GEMINI_API_KEY"):
                GeminiDialogueService()._request_turn("elf", "Hello.", 0)

    def test_http_error_includes_gemini_message_and_selected_model(self) -> None:
        error_body = json.dumps(
            {
                "error": {
                    "message": (
                        "Model is not found or is not supported for generateContent."
                    )
                }
            }
        ).encode("utf-8")
        error = HTTPError(
            url="https://generativelanguage.googleapis.com",
            code=404,
            msg="Not Found",
            hdrs=None,
            fp=io.BytesIO(error_body),
        )
        with (
            patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}),
            patch("game.dialogue.gemini.urlopen", side_effect=error),
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "HTTP 404 for model 'gemini-3.5-flash-lite'.*not found",
            ):
                GeminiDialogueService()._request_turn("elf", "Hello.", 0)

    def test_retries_transient_service_error_then_returns_gemini_reply(self) -> None:
        response_data = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": json.dumps(
                                    {
                                        "response": "Welcome back.",
                                        "relationship_delta": 1,
                                    }
                                )
                            }
                        ]
                    }
                }
            ]
        }
        busy_error = HTTPError(
            url="https://generativelanguage.googleapis.com",
            code=503,
            msg="Unavailable",
            hdrs=None,
            fp=io.BytesIO(b'{"error":{"message":"Busy"}}'),
        )
        with (
            patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}),
            patch(
                "game.dialogue.gemini.urlopen",
                side_effect=[
                    busy_error,
                    io.BytesIO(json.dumps(response_data).encode("utf-8")),
                ],
            ) as urlopen,
            patch("game.dialogue.gemini.time.sleep"),
        ):
            reply = GeminiDialogueService()._request_turn("elf", "Hello.", -5)

        self.assertEqual(reply, GeminiReply("Welcome back.", 1))
        self.assertEqual(urlopen.call_count, 2)


class ConversationScreenTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()

    def tearDown(self) -> None:
        pygame.key.stop_text_input()
        pygame.quit()

    def test_turns_display_reply_and_persist_score_before_next_turn(self) -> None:
        screen = InteractionScreen((800, 600))
        future: Future[GeminiReply] = Future()
        sent: list[tuple[str, str, int, tuple[tuple[str, str], ...]]] = []
        stored_scores: list[tuple[str, int]] = []

        def submit(
            character: str,
            message: str,
            score: int,
            history: tuple[tuple[str, str], ...],
        ) -> Future[GeminiReply]:
            sent.append((character, message, score, history))
            return future

        def save_delta(character: str, delta: int) -> int:
            stored_scores.append((character, delta))
            return 2 + delta

        screen.start_conversation("fae", 2, submit, save_delta, ScreenId.GROVE)
        screen.handle_event(pygame.event.Event(pygame.TEXTINPUT, text="Hello Fae"))
        screen.handle_event(
            pygame.event.Event(
                pygame.KEYDOWN,
                key=pygame.K_RETURN,
                mod=pygame.KMOD_NONE,
            )
        )
        self.assertEqual(sent, [("fae", "Hello Fae", 2, ())])
        self.assertEqual(screen._status, "The Fae is thinking...")

        future.set_result(GeminiReply("The Fae answers.", 1))
        self.assertIsNone(screen.update(0))
        self.assertEqual(stored_scores, [("fae", 1)])
        self.assertEqual(screen._relationship_score, 3)
        self.assertEqual(
            screen._history[-1],
            ConversationMessage(1, "Fae", "The Fae answers."),
        )
        screen.draw(pygame.Surface((800, 600)))

        screen.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        self.assertIs(screen.update(0), ScreenId.GROVE)
        self.assertFalse(screen.is_conversation)

    def test_pending_reply_prompt_matches_relationship_mood(self) -> None:
        screen = InteractionScreen((800, 600))

        def submit(
            _character: str,
            _message: str,
            _score: int,
            _history: tuple[tuple[str, str], ...],
        ) -> Future[GeminiReply]:
            return Future()

        def save_delta(_character: str, delta: int) -> int:
            return delta

        cases = (
            ("elf", -6, "The Elf grimaces while thinking..."),
            ("fae", -5, "The Fae is thinking..."),
            ("elf", 21, "The Elf is thinking..."),
        )
        for character, score, expected_status in cases:
            with self.subTest(character=character, score=score):
                screen.start_conversation(
                    character,
                    score,
                    submit,
                    save_delta,
                    ScreenId.GROVE,
                )
                screen.handle_event(pygame.event.Event(pygame.TEXTINPUT, text="Hello"))
                screen.handle_event(
                    pygame.event.Event(
                        pygame.KEYDOWN,
                        key=pygame.K_RETURN,
                        mod=pygame.KMOD_NONE,
                    )
                )

                self.assertEqual(screen._status, expected_status)
                screen.draw(pygame.Surface((800, 600)))

    def test_failed_request_logs_error_and_shows_generic_character_reply(self) -> None:
        screen = InteractionScreen((800, 600))
        future: Future[GeminiReply] = Future()

        def submit(
            _character: str,
            _message: str,
            _score: int,
            _history: tuple[tuple[str, str], ...],
        ) -> Future[GeminiReply]:
            return future

        saved: list[tuple[str, int]] = []

        def save_delta(character: str, delta: int) -> int:
            saved.append((character, delta))
            return delta

        screen.start_conversation("elf", -5, submit, save_delta, ScreenId.GROVE)
        screen.handle_event(pygame.event.Event(pygame.TEXTINPUT, text="Hello."))
        screen.handle_event(
            pygame.event.Event(
                pygame.KEYDOWN,
                key=pygame.K_RETURN,
                mod=pygame.KMOD_NONE,
            )
        )
        future.set_exception(RuntimeError("service overloaded"))

        with self.assertLogs("game.screens.interaction", level="ERROR") as logs:
            self.assertIsNone(screen.update(0))

        self.assertTrue(any("service overloaded" in line for line in logs.output))
        self.assertEqual(
            screen._history[-1],
            ConversationMessage(1, "Elf", "The elf has nothing to say to that."),
        )
        self.assertEqual(screen._status, "The conversation can continue.")
        self.assertEqual(saved, [])

    def test_escape_during_request_returns_after_score_is_saved(self) -> None:
        screen = InteractionScreen((800, 600))
        future: Future[GeminiReply] = Future()
        saved: list[tuple[str, int]] = []

        def submit(
            _character: str,
            _message: str,
            _score: int,
            _history: tuple[tuple[str, str], ...],
        ) -> Future[GeminiReply]:
            return future

        def save_delta(character: str, delta: int) -> int:
            saved.append((character, delta))
            return delta

        screen.start_conversation("elf", 0, submit, save_delta, ScreenId.GROVE)
        screen.handle_event(pygame.event.Event(pygame.TEXTINPUT, text="Hello."))
        screen.handle_event(
            pygame.event.Event(
                pygame.KEYDOWN,
                key=pygame.K_RETURN,
                mod=pygame.KMOD_NONE,
            )
        )
        screen.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        self.assertTrue(screen.is_conversation)
        self.assertIn("Finishing", screen._status)

        future.set_result(GeminiReply("Hello back.", 1))
        self.assertIs(screen.update(0), ScreenId.GROVE)
        self.assertEqual(saved, [("elf", 1)])
        self.assertFalse(screen.is_conversation)

    def test_history_continues_across_days_and_can_scroll_to_older_messages(self) -> None:
        screen = InteractionScreen((800, 600))
        futures = [Future(), Future()]
        sent: list[tuple[str, str, int, tuple[tuple[str, str], ...]]] = []

        def submit(
            character: str,
            message: str,
            score: int,
            history: tuple[tuple[str, str], ...],
        ) -> Future[GeminiReply]:
            sent.append((character, message, score, history))
            return futures[len(sent) - 1]

        def save_delta(_character: str, delta: int) -> int:
            return delta

        screen.start_conversation(
            "elf", 0, submit, save_delta, ScreenId.GROVE, day_number=1
        )
        screen.handle_event(pygame.event.Event(pygame.TEXTINPUT, text="Good morning"))
        screen.handle_event(
            pygame.event.Event(
                pygame.KEYDOWN,
                key=pygame.K_RETURN,
                mod=pygame.KMOD_NONE,
            )
        )
        futures[0].set_result(GeminiReply("A lovely day.", 1))
        screen.update(0)
        screen.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        screen.update(0)

        screen.start_conversation(
            "elf", 1, submit, save_delta, ScreenId.GROVE, day_number=2
        )
        self.assertEqual(
            screen._history,
            [
                ConversationMessage(1, "You", "Good morning"),
                ConversationMessage(1, "Elf", "A lovely day."),
            ],
        )
        screen.handle_event(pygame.event.Event(pygame.TEXTINPUT, text="Remember me?"))
        screen.handle_event(
            pygame.event.Event(
                pygame.KEYDOWN,
                key=pygame.K_RETURN,
                mod=pygame.KMOD_NONE,
            )
        )

        self.assertEqual(
            sent[1],
            (
                "elf",
                "Remember me?",
                1,
                (("You", "Good morning"), ("Elf", "A lovely day.")),
            ),
        )
        futures[1].set_result(GeminiReply("Of course.", 1))
        screen.update(0)
        self.assertEqual(
            screen._history[-1],
            ConversationMessage(2, "Elf", "Of course."),
        )
        screen.handle_event(
            pygame.event.Event(pygame.MOUSEWHEEL, y=1, x=0)
        )
        self.assertEqual(screen._history_scroll, 1)
        screen.draw(pygame.Surface((800, 600)))


class ConversationRoutingTests(unittest.TestCase):
    def test_unwritten_character_interaction_opens_gemini_conversation(self) -> None:
        pygame.init()
        try:
            class Grove:
                trigger = "interaction.elf"

                def update(self, _delta_seconds: float) -> None:
                    return None

                def consume_dialogue_trigger(self) -> str | None:
                    trigger = self.trigger
                    self.trigger = ""
                    return trigger or None

                def mark_character_talked(self, _character: str) -> None:
                    pass

            class DialogueData:
                def get_events_for(self, _trigger: str) -> tuple[object, ...]:
                    return ()

            class Scores:
                def score(self, character: str) -> int:
                    return 6 if character == "elf" else 0

                def apply_delta(self, _character: str, delta: int) -> int:
                    return delta

            class Gemini:
                def submit_turn(
                    self,
                    _character: str,
                    _message: str,
                    _score: int,
                    _history: tuple[tuple[str, str], ...],
                ) -> Future[GeminiReply]:
                    return Future()

            grove = Grove()
            screen = InteractionScreen((800, 600))
            app = GameApp.__new__(GameApp)
            app.current_screen_id = ScreenId.GROVE
            app.day_number = 1
            app.screens = {ScreenId.GROVE: grove, ScreenId.INTERACTION: screen}
            app.grove_screen = grove
            app.interaction_screen = screen
            app.dialogue_service = DialogueData()
            app.relationship_store = Scores()
            app.gemini_service = Gemini()
            app._fade_phase = None
            app._completed_event_ids = set()

            app.update(0)

            self.assertIs(app.current_screen_id, ScreenId.INTERACTION)
            self.assertTrue(screen.is_conversation)
            self.assertEqual(screen._conversation_character, "Elf")
            self.assertEqual(screen._relationship_score, 6)
        finally:
            pygame.key.stop_text_input()
            pygame.quit()


if __name__ == "__main__":
    unittest.main()
