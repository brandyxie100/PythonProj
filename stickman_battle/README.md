# Stickman Battle

A 2-D action brawler with procedurally drawn stick figures, melee weapons, bow pickups, grenades, bouncy tires, spring boosters, and three difficulty modes — all in pure Python + Pygame (no sprite assets).

---

## Features at a glance

- **Blue player** vs **red/magenta enemies** in a single-room arena
- **Melee** — sword, hammer, pickaxe with **360° spin attacks**
- **Bow pickup** — shiny timed spawn after kills (20 arrows)
- **Loot chest** — mystery chest every 20 seconds (one random reward)
- **AK-47** — automatic rifle from chest loot (30 rounds)
- **Grenades** — 6 per stickman per match; vivid red/orange particle blasts
- **Double jump** and **spring balls** for vertical movement
- **Red bouncy tires** that roll when pushed

---

## Requirements

| Dependency | Version |
|------------|---------|
| Python     | 3.11+   |
| pygame     | 2.6+    |

---

## Installation & Running

```bash
cd stickman_battle
pip install -r requirements.txt
python main.py
```

---

## Controls

| Key | Action |
|-----|--------|
| `A` / `←` | Move left |
| `D` / `→` | Move right |
| `W` / `↑` | Jump (press again mid-air for double jump) |
| `Z` or `J` | Melee **360° spin**, **bow shot**, or **AK-47 auto-fire** (hold) |
| `B` | Throw grenade |

---

## Gameplay flow

1. Choose **Easy**, **Normal**, or **Hard** on the menu.
2. Fight as the **blue** stickman; defeat all enemies to win.
3. Lose if your HP reaches zero.
4. Use **Play Again** or **Main Menu** on the game-over screen.

---

## Combat systems

### Melee (360° spin)

- Press `Z` / `J` to attack. The weapon arm spins a full circle.
- Hit detection follows the **weapon tip** each frame.
- An orange **HitEffect** burst appears on impact.
- The **sword** has the fastest attack rate and spin (see Weapons table).

### Loot chest (every 20 seconds)

A golden **loot chest** spawns at a random map position **every 20 seconds**:

- Shows a **?** until opened — walk into it to collect
- Grants **exactly one** random reward per chest:
  - Bow (20 arrows)
  - AK-47 (30 rounds, hold `Z`/`J` to auto-fire)
  - Sword, hammer, or pickaxe
  - +3 grenades (capped at 6 per match)
- Uncollected chests are **replaced** when the next chest spawns
- AK-47 is **only** obtainable from chests (no fixed 30 s map drop)

### Bow & arrows (pickup)

When you defeat an enemy, a bow set may spawn (**85%** chance):

- Glowing animation with sparkles and a **10-second countdown**
- **20 arrows** per set — walk into the pickup to equip
- Press `Z` / `J` to shoot; arrows arc with light gravity
- **Arrows injure but do not kill** — they cannot reduce HP below 1
- When arrows run out, you switch back to your melee weapon

### Grenades

- Every stickman starts with **6 grenades** per match
- Player throws with **`B`**; grenades arc, bounce, then explode on fuse
- **AoE damage** up to **24** at blast center (higher than sword)
- **Blast visuals**: layered red/orange fireball + **42 particle sparks**
- Enemy AI throws grenades; frequency increases on higher difficulty

### Tires

Red circular tires on the floor roll and bounce when stickmen push them.

### Double jump

Ground jump + one mid-air jump. Landing resets both jumps.

### Spring balls

Fixed yellow pads on the floor and platforms launch you higher than a normal jump and refresh your double jump.

---

## Difficulty modes

| Mode | Your HP | Enemies | Enemy speed | Enemy melee dmg | Your dmg mult | Enemy grenade chance | Grenade cooldown |
|------|---------|---------|-------------|-----------------|---------------|----------------------|------------------|
| Easy | 150 | 2 | 1.8 | 5 | ×1.5 | 32% | 180 f |
| Normal | 100 | 3 | 2.8 | 10 | ×1.0 | 52% | 130 f |
| Hard | 70 | 5 | 4.0 | 18 | ×0.8 | 74% | 90 f |

Enemy melee weapons by mode: **Easy** — sword; **Normal** — sword + pickaxe; **Hard** — sword + pickaxe + hammer.

---

## Weapons & items

| Item | Reach / type | Damage | Cooldown / fuse | Notes |
|------|----------------|--------|-----------------|-------|
| Sword | 48 px melee | 12 | 1 f, fast spin | Player default weapon |
| Hammer | 34 px melee | 22 | 10 f | Hard-mode enemies |
| Pickaxe | 42 px melee | 16 | 5 f | Normal/Hard enemies |
| Bow | ranged | 15 / arrow | 18 f between shots | Kill pickup or chest; non-lethal |
| AK-47 | ranged | 15 / bullet | 3 f auto-fire | Chest only; lethal |
| Grenade | AoE (~78 px) | 24 center | ~95 f fuse | 6/match; chest can add +3 |

Values come from `config.py` and may be tuned there.

---

## Level layout

Arena size: **900 × 600** px.

```
       [  upper-centre + spring ]

[ left-ledge ]           [ right-ledge ]

  [ mid-left + spring ]         [ mid-right + spring ]

[========= FLOOR + centre spring + tires =========]
```

- Full-width **floor**
- **Mid-left / mid-right** platforms (220 px)
- **Upper-centre** platform (190 px)
- **Wall ledges** left and right (130 px)
- **4 spring balls** and **4 tires** placed on floor/platforms

---

## Project structure

```
stickman_battle/
├── config.py       # Constants: physics, colours, weapons, difficulties, keys
├── entities.py     # Game objects
│   ├── HitEffect     # Orange impact flash
│   ├── Platform      # Cyan-edged ledges
│   ├── Tire          # Bouncy red circles
│   ├── SpringBall    # Yellow jump boosters
│   ├── Arrow         # Bow projectile
│   ├── BlastParticle # Grenade explosion sparks
│   ├── Grenade       # Throwable AoE bomb
│   ├── BowPickup     # Timed bow spawn (10 s)
│   ├── ChestPickup   # Mystery loot chest (20 s interval)
│   ├── Stickman      # Base stick figure + combat
│   ├── Player        # Keyboard control
│   └── Enemy         # Chase / attack / grenade AI
├── main.py         # MenuScene, GameScene, GameOverScene, game loop
├── requirements.txt
└── README.md
```

---

## Architecture notes

### Procedural drawing

Stickmen are drawn with `pygame.draw` each frame. `_joints()` positions head, torso, limbs, and weapons from `walk_phase`, `attack_phase`, and `facing`.

### Hit detection

- **Melee**: weapon-tip hitbox during spin (`WEAPON_HIT_RADIUS`).
- **Arrows**: tip proximity; damage capped so targets stay at ≥ 1 HP.
- **Rifle bullets**: swept segment hit test; lethal damage.
- **Grenades**: radial falloff inside `GRENADE_RADIUS` on detonation.

### Grenade blast rendering

On explode, `Grenade` spawns `BlastParticle` embers (red/orange palette) and draws a multi-layer fireball (core → inner → mid → outer → smoke) with an early white-hot flash.

### Enemy AI

```
CHASE ──(in melee range)──► ATTACK
   │
   └──(hurt)──► BACK-OFF ──► CHASE

Separately: maybe_throw_grenade() when in range, based on difficulty chance/cooldown.
```

### Scenes

`MenuScene` → `GameScene` → `GameOverScene`. Each scene’s `handle_event()` / `update()` may return the next scene object.

---

## Tuning

Edit `config.py` to adjust damage, cooldowns, grenade blast colours, particle count, difficulty presets, and key bindings without changing game logic.
