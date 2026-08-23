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
- **Main menu:**
  - **Adventure** — classic campaign (`level_1` … `level_5`)
  - **Cross Mode** — hybrid fusion campaign (`cross_1` … `cross_3`)
- **Adventure start level:** Edit `START_LEVEL_NUM` in `source/constants.py` (must be within `1`–`MAX_LEVEL`)
  - Level 1–2: Day
  - Level 3: Night
  - Level 4: Moving card select
  - Level 5: Wall-nut bowling (final shipped level; victory returns to the main menu)

### Cross Mode (hybrid plants + merge)

Inspired by hybrid / cross-breed PvZ styles (original tinted sprites only — no third-party Hybrid mod assets).

1. Pick **Cross Mode** on the title screen.
2. Place plants as usual. **Drop a plant onto another plant** to:
   - **Star-merge** the same type (★ → ★★ → ★★★): attack is **more than double** (then ~3.5×), with a small random variance each merge
   - **Fuse any two different plants** into a new creature that **keeps both parents’ traits** and has **higher stats** than either original
3. Showcase recipes still get special names (Pea-Sunflower, Torch-Nut, …). Any other pair becomes e.g. `Peashooter × Wall-Nut`.
4. Hybrid zombies (tinted skins) appear in Cross maps.

| Hybrid | Recipe | Role |
|--------|--------|------|
| Pea-Sunflower | Peashooter + Sunflower | Shoots peas **and** makes sun |
| Pea Gatling | Peashooter + Repeater | Triple-shot volley |
| Sun Cannon | Sunflower + Repeater | Heavy peas + sun |
| Torch-Nut | Wall-Nut + Cherry Bomb (or Jalapeno) | Tank; peas that pass it become fire (2×) |
| Frost Repeater | Snow Pea + Repeater | Double ice peas |
| Spike-Mine | Spikeweed + Potato Mine | Lane spikes + armed explode |

```bash
python -m pytest tests/ -q
```

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
    │   └── map/            # level_1..5.json, cross_1..3.json
    ├── state/
    │   ├── mainmenu.py
    │   ├── screen.py       # Victory / lose screens
    │   └── level.py        # Core gameplay
    └── component/
        ├── map.py
        ├── plant.py
        ├── hybrids.py      # Cross fusion recipes + HybridConfig
        ├── zombie.py
        └── menubar.py
```

---

## Architecture Notes (for maintainers)

### State machine

| State          | Module      | Next transition                                      |
|----------------|-------------|------------------------------------------------------|
| `MAIN_MENU`    | mainmenu.py | Adventure → Adventure levels; Cross → Cross maps |
| `LEVEL`        | level.py    | Win → `GAME_VICTORY`; lose → `GAME_LOSE`             |
| `GAME_VICTORY` | screen.py   | Next map if within mode max (`MAX_LEVEL` / `MAX_CROSS_LEVEL`), else `MAIN_MENU`|
| `GAME_LOSE`    | screen.py   | → `MAIN_MENU`                                        |

Shared progress lives in `Control.game_info` / state `persist` (`LEVEL_NUM`, `CURRENT_TIME`, `GAME_MODE`).

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
- **Cross hybrids:** Pea-Sunflower, Pea Gatling, Sun Cannon, Torch-Nut, Frost Repeater, Spike-Mine
- **Zombies:** Normal, Flag, Conehead, Buckethead, Newspaper
- **Cross hybrid zombies:** Cone-Bucket, Flag-Paper, Ember Cone (tinted skins)
- **Level types:** Day, night, moving card select, wall-nut bowling, Cross fusion campaign

---

## Demo

![demo1](https://raw.githubusercontent.com/marblexu/PythonPlantsVsZombies/master/demo/demo1.jpg)
![demo2](https://raw.githubusercontent.com/marblexu/PythonPlantsVsZombies/master/demo/demo2.jpg)
