# Escape the Enchanted Grove

## Run

Install the dependency and launch the game:

```powershell
python -m pip install -r requirements.txt
python main.py
```

The title screen opens fullscreen. Select **Start Game** or press Enter to pan
into the intro-screen placeholder. Press Escape to quit; F11 toggles fullscreen.

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
- `game/tasks/` contains the house, pond, and garden task briefs and
  the result contract.
- `game/dialogue/` isolates character dialogue behind a service interface.
- `game/ui/` contains reusable presentation widgets.

To reduce merge conflicts, work primarily within the module for your feature.
Coordinate edits to `game/state.py`, `game/story.py`, `game/app.py`, and shared
interfaces before changing them.
