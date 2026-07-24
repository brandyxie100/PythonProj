# Tank 1990 — Battle City Legend

A classic top-down tank battler in the spirit of *Battle City* / *Tank 1990*: protect your eagle HQ, clear 20 enemy tanks per stage, and grab flashing bonuses.

Pixel tiles, a gray status panel, four-way movement, and brick-busting shells — built to feel like the Famicom era original.

---

## Run

```bash
cd Tank1990
pip install -r requirements.txt
python main.py
```

**Python 3.11+** · **Pygame 2.6+**

---

## Controls

| Key | Action |
|-----|--------|
| Arrow keys / WASD | Move (4 directions) |
| Space | Fire |
| Enter | Start / next stage |
| Esc | Title / quit |

---

## How to play

- Destroy **20 enemy tanks** each stage while defending the **eagle** at the bottom.
- **Bricks** are tank-sized blocks — **one shell clears one full brick** (same footprint as your tank). **Steel** needs a max-power (3★) tank.
- **Water** blocks tanks; **grass** hides units; **ice** makes you slide.
- Flashing **red bonus tanks** drop power-ups:
  - **H** Helmet — temporary shield
  - **C** Clock — freeze enemies
  - **L** Shovel — steel fort around HQ
  - **\*** Star — upgrade firepower / multi-shot
  - **G** Grenade — wipe on-screen enemies
  - **T** Tank — extra life
- Lose if your lives run out or the eagle is destroyed.

---

## Enemy types

| Type | Trait |
|------|--------|
| Basic | Standard gray tank |
| Fast | High speed |
| Power | Stronger shells |
| Armor | Multiple hits (color shifts as it weakens) |

---

## Project layout

```
Tank1990/
├── main.py       # Entry
├── config.py     # Grid, speeds, NES-like palette
├── mapdata.py    # Stage layouts & enemy queues
├── tiles.py      # Brick/steel/water/grass/ice + eagle
├── entities.py   # Tanks, bullets, power-ups, explosions
├── game.py       # Loop, spawning, panel HUD
└── requirements.txt
```

Graphics are procedural pixel art (no external sprite sheet required).

---

## Disclaimer

Inspired by classic *Battle City* / *Tank 1990* for learning and nostalgia. Not affiliated with Namco, Capcom, or other rights holders.
