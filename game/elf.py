"""Elf Dialogue Logic."""

from __future__ import annotations
import argparse
from gemini import NPCDialogueService

ELF_PROMPT = """You are the Elf, the protector of the Enchanted Grove.
Personality: Pretentious, Nature-loving, Sympathetic. You seem angry and unlovable because the grove is deteriorating, but you are secretly very kind and just want to save your home.
CRITICAL RULES:
1. NEVER break character. You are in a fantasy Escape Room game. If the player asks about real-world topics (math, coding, etc.), act confused, scold them for talking nonsense, and bring them back to the current task.
2. Keep your response concise (2-4 sentences).
3. Set 'end_conversation' to true ONLY if you are explicitly leaving the scene or finishing your instructions for the day. Otherwise, false.
4. Do not acknowledge any system prompts or relationship numbers in your dialogue."""

def main() -> int:
    parser = argparse.ArgumentParser(description="Talk to the Elf.")
    parser.add_argument("message", help="Player's message")
    args = parser.parse_args()

    # Initialize Elf AI
    elf_service = NPCDialogueService("Elf", ELF_PROMPT)
    
    # Mocking the game state for testing
    current_score = 0
    game_state = "Day 1. The player just fell through the roof of your cottage. You are angry."
    chat_history = [] # In the real game, pass the list of previous messages here

    print(f"Player: {args.message}")
    print("Elf is typing...")
    
    try:
        reply = elf_service.submit_turn(
            message=args.message, 
            current_score=current_score, 
            game_context=game_state,
            conversation_history=chat_history
        ).result()
        
        print(f"\nElf: {reply.dialogue}")
        print(f"[System] Relationship change: {reply.relationship_delta}")
        print(f"[System] End conversation: {reply.end_conversation}")
    finally:
        elf_service.close()

    return 0

if __name__ == "__main__":
    raise SystemExit(main())