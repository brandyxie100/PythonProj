# JUMP — Stereo Madness

A Geometry Dash–style auto-runner featuring a **Stereo Madness** course
(cube → ship → cube).

## Run

```bash
cd jump
pip install -r requirements.txt
python main.py
```

## Controls

| Key | Action |
|-----|--------|
| `Space` / `Enter` | Menu: start |
| `Space` / `W` / `↑` | Cube: jump, tap again mid-air to double jump · Ship: hold = up, release = down |
| `Esc` | Menu: quit · In-run: back to menu |

Choose **EDITOR** from the menu, or press `E`. In the editor, click to place the
selected item, right-click to erase, and use `1`-`5` to select spike, block,
portal, orb, or erase. Press `P` to cycle portal modes and `O` to cycle orb
colors. Use the mouse wheel or arrow keys to scroll, `S` to save,
`L` to load, and `N` to clear a new level. The layout is saved as
`custom_level.json` beside the game files.

Press the green **PLAY** button in the editor to test the current layout
without saving it first.

Use the **DOUBLE JUMP: ON/OFF** button to toggle the extra cube jump for the
test run.

Press `P` in the editor to cycle through portal types, including the yellow
speed portal that increases the auto-scroll speed.

Click **SAVE** in the editor to save your level progress, or press `S`.
Saved levels automatically reopen when you enter the editor again.
Click **UNSAVE** to remove the saved copy while keeping the current layout open.

After unlocking the vault, tapping its lock ten times and earning the key from
the first level reveals the ten-level path. Each completed path level awards a
white orb; completing all ten opens the path door.

## Orbs

Click **Space** while touching an orb:
- **Yellow** — jump boost
- **Pink** — stronger jump
- **Blue** — flip gravity
- **Black** — flip gravity

1. **Cube** — learn the spike rhythm and climb short stairs  
2. **Purple ship portal** — weave between floor/ceiling spikes  
3. **Green cube portal** — tougher final stretch to the flag  
