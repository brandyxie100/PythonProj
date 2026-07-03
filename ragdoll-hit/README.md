# Ragdoll Hit

A physics-driven stick-figure brawler inspired by [Ragdoll Hit](https://poki.com/en/g/ragdoll-hit). Characters are **pymunk ragdolls** — each limb is a rigid body linked by joints. Weapons swing with real inertia and deal damage from collision momentum.

**Milestone 1** (current): single-player stage, default staff weapon, one AI opponent, win/lose loop.

---

## Requirements

| Dependency | Version |
|------------|---------|
| Python     | 3.11+   |
| pygame     | 2.6+    |
| pymunk     | 7.2+    |

---

## Installation and running

```bash
cd ragdoll-hit
pip install -r requirements.txt
python main.py
```

From the project virtualenv:

```bash
/Users/brandyxie/Downloads/09Education/PythonProj/.gamevenv/bin/pip install -r requirements.txt
/Users/brandyxie/Downloads/09Education/PythonProj/.gamevenv/bin/python main.py
```

---

## Controls (Milestone 1)

| Key | Action |
|-----|--------|
| `A` / `←` | Move left |
| `D` / `→` | Move right |
| `W` / `↑` | Jump |
| `Space` / `J` | Swing staff |

Mouse: click **1 PLAYER** on the menu, then fight until one health bar is empty.

---

## Milestone 1 scope

- Pymunk ragdoll (head, torso, arms, legs, joints, torso stabilizer / stagger)
- Staff weapon with swing motor and impact-based damage
- One stage: ground + raised platform
- AI opponent (approach → attack → recover)
- Menu → Stage → Game Over (Play Again / Main Menu)

**Not in Milestone 1:** weapon shop, gold, save file, multi-stage progression, wheels/spikes/destructibles, local 2-player versus.

---

## Roadmap

### Milestone 2 — Weapon shop and progression

- Gold currency and JSON save/load
- Left-side shop panel (weapon rows with icon, name, price, equip)
- 6–8 weapons with distinct mass, length, damage, and swing speed

### Milestone 3 — Interactive terrain and multi-stage

- Rolling wheels, spike traps, destructible tiles
- Level 1…N with scaling AI and terrain
- Coin rewards per stage clear

### Milestone 4 — Local 2-player versus

- Second keyboard layout (e.g. arrows + `/`)
- Fixed arena, dual health HUD
- Reuses ragdoll/weapon systems from Milestone 1

---

## Project layout

```
ragdoll-hit/
├── main.py           # Scenes and game loop
├── config.py         # Constants and WEAPON_DATA
├── physics_world.py  # Pymunk space and damage
├── ragdoll.py        # Ragdoll bodies and joints
├── weapon.py         # Staff weapon
├── ai_controller.py  # Enemy AI state machine
├── terrain.py        # Ground and platform
├── coords.py         # Pygame ↔ pymunk coordinates
├── requirements.txt
├── README.md
└── tests/
```

---

## Tests

```bash
cd ragdoll-hit
pytest tests/ -v
```

---

## Development workflow

Branch: `feature/ragdoll-hit-core-combat` off `main`. Tests written before domain logic per project rules.
