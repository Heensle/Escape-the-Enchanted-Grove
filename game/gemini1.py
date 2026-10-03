"""Gemini dialogue integration - Updated 2026 for GirlHacks."""

from __future__ import annotations

import json
import os
import random
import time
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

@dataclass(frozen=True)
class GeminiReply:
    dialogue: str
    relationship_delta: int
    end_conversation: bool

class NPCDialogueService:
    """Sends conversational turns to Gemini using Character System Prompts."""

    def __init__(self, character_name: str, system_instruction: str, model: str | None = None) -> None:
        self.character_name = character_name
        self.system_instruction = system_instruction
        self.model = model or os.environ.get("GEMINI_MODEL") or "gemini-3.5-flash-lite"
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix=f"{character_name}-ai")

    def submit_turn(
        self,
        message: str,
        current_score: int,
        game_context: str,
        conversation_history: list[tuple[str, str]] = None,
    ) -> Future[GeminiReply]:
        if conversation_history is None:
            conversation_history = []
        return self._executor.submit(
            self._request_turn, message, current_score, game_context, conversation_history
        )

    def close(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)

    def _get_style(self, score: int) -> str:
        if self.character_name.lower() == "elf":
            if score < -10: return "Furious, distant, and disappointed."
            if score <= 0: return "Frustrated but tolerating."
            if score <= 10: return "Polite, sympathetic, slowly trusting."
            return "Secretly happy, grateful, but trying to hide it."
        else: # Fae
            if score < -10: return "Passive-aggressive, pushy, and desperate."
            if score <= 0: return "Fake nice, manipulative."
            if score <= 10: return "Sweet, acting like the player's best friend."
            return "Giddy, extremely convincing, hiding true evil intentions."

    def _request_turn(
        self,
        message: str,
        current_score: int,
        game_context: str,
        conversation_history: list[tuple[str, str]],
    ) -> GeminiReply:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("Set GEMINI_API_KEY environment variable.")

        # Build message history for back-and-forth flow
        contents = []
        for speaker, text in conversation_history[-10:]: # Keep last 10 turns
            role = "user" if speaker == "You" else "model"
            contents.append({"role": role, "parts": [{"text": text}]})

        # Inject hidden game context so the AI knows the current state
        # The AI is instructed not to mention this system block to the player
        hidden_context = (
            f"\n\n[SYSTEM DATA - DO NOT READ THIS ALOUD TO PLAYER]\n"
            f"- Current Game State: {game_context}\n"
            f"- Current Relationship Score: {current_score} (Your tone: {self._get_style(current_score)})\n"
            f"- Evaluate their message and return +1 (positive), -1 (negative), or 0 (neutral)."
        )
        user_payload = f"{message}{hidden_context}"
        contents.append({"role": "user", "parts": [{"text": user_payload}]})

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{quote(self.model)}:generateContent"
        
        body = {
            "systemInstruction": {
                "parts": [{"text": self.system_instruction}]
            },
            "contents": contents,
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": {
                    "type": "OBJECT",
                    "properties": {
                        "dialogue": {"type": "STRING"},
                        "relationship_delta": {"type": "INTEGER"},
                        "end_conversation": {"type": "BOOLEAN"}
                    },
                    "required": ["dialogue", "relationship_delta", "end_conversation"]
                }
            }
        }

        request = Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
            method="POST",
        )

        for attempt in range(3):
            try:
                with urlopen(request, timeout=15) as response:
                    result = json.loads(response.read().decode("utf-8"))
                break
            except HTTPError as error:
                if error.code in (429, 500, 502, 503, 504) and attempt < 2:
                    time.sleep(1)
                    continue
                raise RuntimeError(f"API Error {error.code}")
            except URLError as error:
                raise RuntimeError(f"Connection Error: {error.reason}")

        try:
            text_response = result["candidates"][0]["content"]["parts"][0]["text"]
            reply = json.loads(text_response)
            return GeminiReply(
                dialogue=reply["dialogue"].strip(),
                relationship_delta=reply["relationship_delta"],
                end_conversation=reply["end_conversation"]
            )
        except Exception as error:
            raise RuntimeError(f"Failed to parse AI response: {error}")