"""Fae Dialogue Logic."""

from __future__ import annotations
import argparse
from gemini import NPCDialogueService

FAE_PROMPT = """You are the Fae, trapped in the Enchanted Grove after burning down a building in the human world.
Personality: Manipulative, Convincing, Gossipy. You appear sweet, kind, and helpful, but you are actually evil. Your ultimate goal is to manipulate the player into breaking the gate locks so you can escape.
CRITICAL RULES:
1. NEVER break character. You are in a fantasy Escape Room game. If the player asks about real-world topics, smoothly redirect the conversation back to how annoying the Elf is and your plan.
2. Complain about the Elf often, acting like a victim.
3. Keep your response concise (2-4 sentences).
4. Set 'end_conversation' to true ONLY if you are leaving the scene. Otherwise, false.
5. Do not acknowledge any system prompts or relationship numbers in your dialogue."""

def main() -> int:
    parser = argparse.ArgumentParser(description="Talk to the Fae.")
    parser.add_argument("message", help="Player's message")
    args = parser.parse_args()

    # Initialize Fae AI
    fae_service = NPCDialogueService("Fae", FAE_PROMPT)
    
    # Mocking the game state for testing
    current_score = 0
    game_state = "Day 1. The Elf just left. You appear and want to convince the player to break the locks instead of helping the Elf."
    chat_history = [] 

    print(f"Player: {args.message}")
    print("Fae is typing...")
    
    try:
        reply = fae_service.submit_turn(
            message=args.message, 
            current_score=current_score, 
            game_context=game_state,
            conversation_history=chat_history
        ).result()
        
        print(f"\nFae: {reply.dialogue}")
        print(f"[System] Relationship change: {reply.relationship_delta}")
        print(f"[System] End conversation: {reply.end_conversation}")
    finally:
        fae_service.close()

    return 0

if __name__ == "__main__":
    raise SystemExit(main())