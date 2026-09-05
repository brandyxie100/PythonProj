# Kid Minecraft Sandbox

Small creative voxel sandbox for kids. **Original** classic-looking block textures (generated with Pillow)—not Minecraft/Mojang assets.

## Run

```bash
cd MineCraft
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Or with the repo game venv:

```bash
cd MineCraft
../.gamevenv/bin/pip install -r requirements.txt
../.gamevenv/bin/python main.py
```

## Two-world workflow

1. **Demo Island (key `1` on menu)** — prebuilt island + house for you to show first.
2. **New Creative (key `2`)** — flat grass pad so your child can build freely.
3. **Load My World (key `3` or `F9`)** — opens `worlds/my_world.json`.
4. **Save (`F5`)** — writes the current world to `worlds/my_world.json`.

Press **`M`** anytime to return to the menu.

## Controls

| Action | Input |
|--------|--------|
| Move | WASD |
| Look | Mouse (click game to lock) |
| Unlock mouse | Esc |
| Break block | Left mouse |
| Place block | Right mouse |
| Hotbar | Keys `1`–`8` |
| Save | `F5` |
| Load my world | `F9` |
| Menu | `M` |

## Blocks

Grass, Dirt, Stone, Wood, Leaves, Sand, Water, Planks. Bedrock under the map cannot be broken.

## Notes

- World is ~12×12 (~300 cubes) so it stays smooth on a laptop. Huge older save files are rejected automatically.
- Textures are created in `textures/` on first run.
- Demo is rewritten to `worlds/demo_island.json` when you press `1`.
- If the game ever froze before: delete `worlds/*.json` and relaunch.
