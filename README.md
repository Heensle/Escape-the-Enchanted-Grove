# Escape the Enchanted Grove

## Run

Install the dependency and launch the game:

```powershell
python -m pip install -r requirements.txt
python main.py
```

The title screen opens fullscreen. Select **Start Game** or press Enter to
read the opening narration and enter the grove. Press Escape to quit; F11
toggles fullscreen from the title screen.

## Grove playtest

Use **WASD** or the **arrow keys** to move. The camera follows the player while
keeping the room in view. The current day is shown in the top-left corner.
Approach the Elf and the Fae and press **E** to talk. The task list beside the
day count tracks both conversations and reveals their daily requests. Tasks
remain visibly locked until you have talked to both characters that day.
Interact with the day's object (the hammer on day 2, net on day 3, or garden on
day 4) to choose an available task. The roof-repair choice opens the jigsaw
task scaffold, ready for puzzle mechanics to be added; the other unfinished
tasks open their own task placeholders. The gate remains a solid obstacle and
does nothing when interacted with.

To end any day, complete every item in the task list, approach the bedroll box
beside the house, press **E**, then click **Sleep** to confirm. Day 1 requires
both conversations; days 2 and 3 also require both assigned tasks; day 4
requires the garden maze and is the final day. After sleeping on day 4, the
story ends at the epilogue; there is no fifth day. Until the actual jigsaw,
pond, and maze mechanics are
implemented, their task screens expose an explicit temporary completion
button. On days 2 and 3, choosing one of the two tasks for the hammer or net
locks out the other path; the unchosen request is marked **FAILED**.
Authored interaction events play when their trigger is available. When no
interaction event is authored, speaking to the Elf or Fae opens a Gemini chat.

The Grove uses the transparent character and broken-house PNGs in
`assets_images/` as its player, Elf, Fae, and house art.

## Conversing with the Elf and Fae

Approach the Elf or Fae and press **E** to open a conversation. Type a message,
press **Enter** to send it, and use **Shift+Enter** for a new line. Gemini
generates the character's response and evaluates a relationship change from
-1 or +1. New saves start the Elf at -5 and the Fae at +5. Completing an
assigned character task adds 3 points; not completing it subtracts 3. Each
character's score is saved separately, and their relationship band influences
future responses: below -20, -20 to -6, -5 to 5, 6 to 20, and above 20.

Set `GEMINI_API_KEY` in the environment before launching the game. In
PowerShell, for example:

```powershell
$env:GEMINI_API_KEY = "your-gemini-api-key"
python main.py
```

The default model is `gemini-3.5-flash-lite`, which Google describes as
optimized for low latency and high throughput; this may help during busy
periods, but no model is guaranteed to be free of demand-related errors.
Transient rate-limit and service errors are retried briefly. Set
`GEMINI_MODEL` to use another Gemini model. Relationship scores are saved under
the current user's local
application data directory (`%LOCALAPPDATA%\EscapeTheEnchantedGrove` on
Windows, or the standard XDG data directory on other platforms). Authored
character dialogue continues to use the existing dialogue files when present.

## Title-screen artwork

Place a 2D background image at `assets/images/title_background.png` to replace
the procedural placeholder forest. The image is scaled to cover the screen, so
it can use any aspect ratio. Keep title text and interface elements separate
from the image so they remain readable and scale independently.

## Project structure

- `game/app.py` owns the event loop and screen transitions.
- `game/screens/` contains one module per screen; screens share the contract in
  `game/screens/screen.py`.
- `game/state.py` defines shared story data; `game/story.py` owns choice and
  ending rules.
- `game/tasks/` contains the daily task catalog, house/pond/garden briefs,
  and the task result contract.
- `game/minigames/` contains self-contained minigames. The lock-break clicker
  is registered as `ScreenId.LOCK_BREAK`; `game/screens/task_choices.py`
  contains the daily option gate and the roof jigsaw scaffold.
- `game/dialogue/` contains the authored-dialogue loader and Gemini client; do
  not add authored dialogue here.
- `data/dialogue/` contains writer-authored dialogue files, one JSON file per
  day, with instructions in `data/dialogue/README.md`.
- `game/ui/` contains reusable presentation widgets.

## Writing dialogue

Add a `day_NN.json` file under `data/dialogue/`. Give every event a unique
`id`, a `trigger`, and an ordered `lines` list containing exact `speaker` and
`text` values. Use a `scene.*` trigger for mandatory scenes and an
`interaction.*` trigger for player interactions; trigger names are labels, so
game code can request events the same way for either kind.

The game loads all day files through `JsonDialogueService` and can retrieve an
event by ID with `get_event("day_01.scene.intro")`, or retrieve all events
for a trigger with `get_events_for("interaction.elf")`. A speaker named
`narrator` can be used for exposition. Keep IDs unique across all days so
content can be referenced reliably as the story grows.

To reduce merge conflicts, work primarily within the module for your feature.
Coordinate edits to `game/state.py`, `game/story.py`, `game/app.py`, and shared
interfaces before changing them.
