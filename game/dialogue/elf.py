"""Command-line smoke test for the game's Elf dialogue integration."""

from __future__ import annotations

import argparse
import sys

from game.dialogue.gemini import GeminiDialogueService


def main() -> int:
    parser = argparse.ArgumentParser(description="Send a test message to the Elf.")
    parser.add_argument("message", help="The player's message to the Elf")
    args = parser.parse_args()

    service = GeminiDialogueService()
    try:
        reply = service.submit_turn("elf", args.message, 0).result()
    except (RuntimeError, ValueError) as error:
        print(f"Gemini request failed: {error}", file=sys.stderr)
        return 1
    finally:
        service.close()

    print(reply.text)
    print(f"Relationship change: {reply.relationship_delta:+d}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())