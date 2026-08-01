# JUMP

A small **Geometry Dash–style** auto-runner with cube, ship, ball, and UFO modes.

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
| `Space` / `W` / `↑` | Mode action (see below) |
| `Esc` | Menu: quit · In-run: back to menu |

## Gamemodes & portals

| Portal | Mode | Control |
|--------|------|---------|
| **Green** | Cube | Jump 2 blocks (hold to keep hopping) |
| **Purple** | Ship | **Hold** = fly up · **Release** = fly down |
| **Orange** | Ball | Click to invert gravity |
| **Yellow** | UFO | Click to jump 2 blocks anytime (mid-air OK) |

Ship floor / ceiling contact crashes you. Reach the checkered flag to clear the level.
