# Plants vs Zombies (Python)

A Plants vs Zombies–style tower defense game built with Pygame.

> **Disclaimer:** For personal learning and noncommercial use only. If this infringes copyright, please contact the maintainer.

---

## Requirements

- **Python 3.12+**
- **Pygame 2.6+**

```bash
pip install -r requirements.txt
```

---

## How to Run

From this project directory:

```bash
python main.py
```

Or from the parent directory:

```bash
python GamePlantsVsZombies/main.py
```

Asset paths resolve from `__file__`, so either launch path works.

---

## How to Play

- **Mouse:** Collect sun, select plant cards, place plants on the grid
- **Start level:** Edit `START_LEVEL_NUM` in `source/constants.py` (must be within `1`–`MAX_LEVEL`)
  - Level 1–2: Day
  - Level 3: Night
  - Level 4: Moving card select
  - Level 5: Wall-nut bowling (final shipped level; victory returns to the main menu)

---

## Project Structure

```
GamePlantsVsZombies/
├── main.py                 # Entry point → source.main.main()
├── requirements.txt
├── README.md
├── demo/                   # Screenshot images
├── resources/
│   └── graphics/           # Sprites (loaded by tool.load_all_gfx)
│       ├── Bullets/
│       ├── Plants/
│       ├── Zombies/
│       ├── Cards/
│       └── Screen/         # UI / menu / victory / lose images
└── source/
    ├── main.py             # Registers states and starts Control loop
    ├── tool.py             # State machine, GFX loader, bootstrap_display()
    ├── constants.py        # Screen, grid, states, plant/zombie names, MAX_LEVEL
    ├── data/
    │   ├── entity/         # plant.json, zombie.json (sprite rects)
    │   └── map/            # level_1.json … level_5.json
    ├── state/
    │   ├── mainmenu.py
    │   ├── screen.py       # Victory / lose screens
    │   └── level.py        # Core gameplay
    └── component/
        ├── map.py
        ├── plant.py
        ├── zombie.py
        └── menubar.py
```

---

## Architecture Notes (for maintainers)

### State machine

| State          | Module      | Next transition                                      |
|----------------|-------------|------------------------------------------------------|
| `MAIN_MENU`    | mainmenu.py | Adventure → `LEVEL`                                  |
| `LEVEL`        | level.py    | Win → `GAME_VICTORY`; lose → `GAME_LOSE`             |
| `GAME_VICTORY` | screen.py   | Next map if `LEVEL_NUM ≤ MAX_LEVEL`, else `MAIN_MENU`|
| `GAME_LOSE`    | screen.py   | → `MAIN_MENU`                                        |

Shared progress lives in `Control.game_info` / state `persist` (`LEVEL_NUM`, `CURRENT_TIME`).

### Data flow

1. `tool.bootstrap_display()` initializes Pygame, loads `GFX`, `PLANT_RECT`, `ZOMBIE_RECT`
2. Level maps: `source/data/map/level_N.json` → background, sun, zombie spawn list, optional choose-bar type
3. Gameplay entities are pygame sprites managed per row in `level.Level`

### Adding a new level

1. Add `source/data/map/level_N.json` (copy an existing map and edit `zombie_list` / `background_type`)
2. Bump `MAX_LEVEL` in `source/constants.py` to match
3. Keep filenames contiguous: `level_1.json` … `level_{MAX_LEVEL}.json`

### Choose-bar types (`choosebar_type` in map JSON)

| Value | Constant             | Behavior                          |
|-------|----------------------|-----------------------------------|
| `0`   | `CHOOSEBAR_STATIC`   | Classic pick-8 then play          |
| `1`    | `CHOOSEBAR_MOVE`     | Conveyor / moving cards           |
| `2`    | `CHOOSEBAR_BOWLING`  | Wall-nut bowling (no grid plant)  |

### Stability conventions

- Do **not** mutate sprite lists while iterating (e.g. cars use list rebuild after collisions)
- HypnoShroom only converts a zombie when `kill_zombie` was set by a real eat
- Invalid / missing level numbers are clamped; missing JSON raises a clear `RuntimeError`
- Unknown state transitions raise from `Control.flip_state` instead of KeyErroring silently
- MenuBar / Panel restore a clean background copy before redrawing sun digits (avoids ghosting)

### Optional env

| Variable            | Effect                                      |
|---------------------|---------------------------------------------|
| `PVZ_SKIP_DISPLAY=1`| Skip display bootstrap (non-game tooling)   |

---

## Implemented Content

- **Plants:** Sunflower, Peashooter, SnowPea, WallNut, CherryBomb, Threepeater, RepeaterPea, Chomper, PuffShroom, PotatoMine, Squash, Spikeweed, Jalapeno, ScaredyShroom, SunShroom, IceShroom, HypnoShroom, bowling nuts
- **Zombies:** Normal, Flag, Conehead, Buckethead, Newspaper
- **Level types:** Day, night, moving card select, wall-nut bowling

---

## Demo

![demo1](https://raw.githubusercontent.com/marblexu/PythonPlantsVsZombies/master/demo/demo1.jpg)
![demo2](https://raw.githubusercontent.com/marblexu/PythonPlantsVsZombies/master/demo/demo2.jpg)
