# WRITERS: add dialogue in this folder

Add or edit the JSON file for the relevant day here:

- `day_01.json` — Day 1 dialogue
- `day_02.json` — Day 2 dialogue
- `day_03.json` — Day 3 dialogue
- `day_04.json` — Day 4 dialogue
- `day_05.json` — Day 5 dialogue
- Continue the same `day_NN.json` naming pattern if the story adds more days.

Do not add dialogue text to the Python files in `game/dialogue/`. Those files
load and provide the authored dialogue to the game.

Each file must contain a day number and an `events` list. Each event needs:

- A unique, stable `id` that describes the story moment.
- A `trigger` label: use `scene.*` for mandatory scenes or `interaction.*`
  for dialogue started by a player interaction.
- An ordered `lines` list. Each line needs a `speaker` and exact `text`.
  Use `narrator` for exposition.

Example event:

```json
{
  "id": "day_01.scene.cottage_crash",
  "trigger": "scene.cottage_crash",
  "lines": [
    {
      "speaker": "narrator",
      "text": "You land on top of a small cottage."
    },
    {
      "speaker": "elf",
      "text": "Look what you've done to my roof!"
    }
  ]
}
```

Add the event object to the day's `events` list, separating it from adjacent
events with a comma. Keep event IDs unique across all day files. JSON does not
support literal comments. Put day-specific notes in the optional top-level
`writer_notes` array instead. These notes are for writers only; the game ignores
them and only loads entries in `events`.

## Day 1 writing status

The opening narration and the narration before sleep are entered as events in
`day_01.json`. The `writer_notes` array in that file marks where dialogue is
still needed for the Elf in the house, the Elf at the gate, and the Fae. It
also records the stage direction for the Elf leaving and the Fae appearing.
