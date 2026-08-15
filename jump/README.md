# JUMP — Stereo Madness

A Geometry Dash–style auto-runner featuring a **Stereo Madness** course
(cube → ship → cube).

## Run

On macOS, use `python3` and `pip3` if `python` or `pip` are not available.

```bash
cd jump
python3 -m pip install -r requirements.txt
python3 main.py
```

Or use the provided setup helper:

```bash
cd jump
sh setup_env.sh
source .venv/bin/activate
python main.py
```

If macOS prompts for developer tools, run:

```bash
xcode-select --install
```

## Controls

| Key | Action |
|-----|--------|
| `Space` / `Enter` | Menu: start |
| `Space` / `W` / `↑` | Cube: jump, tap again mid-air to double jump · Ship: hold = up, release = down |
| `Esc` | Menu: quit · In-run: back to menu |

## Orbs

Click **Space** while touching an orb:
- **Yellow** — jump boost
- **Pink** — stronger jump
- **Blue** — flip gravity

1. **Cube** — learn the spike rhythm and climb short stairs  
2. **Purple ship portal** — weave between floor/ceiling spikes  
3. **Green cube portal** — tougher final stretch to the flag  
