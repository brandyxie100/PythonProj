# Stickman Battle

A 2-D action brawler featuring procedurally drawn stick figures, three weapons, bouncy tires, and three difficulty modes — all written in pure Python with Pygame (no sprite assets required).

---

## Screenshots (reference style)

The game uses the same visual language as the reference app:
- Dark-blue gradient background
- Platforms with a bright **cyan top edge**
- Stick figures with coloured **3-D-glasses eyes**
- Red bouncy tires that roll and bounce

---

## Requirements

| Dependency | Version |
|------------|---------|
| Python     | 3.11+   |
| pygame     | 2.6+    |

---

## Installation & Running

```bash
# 1. Navigate into the game folder
cd stickman_battle

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch
python main.py
```

---

## Controls

| Key | Action |
|-----|--------|
| `A` / `←` | Move left |
| `D` / `→` | Move right |
| `W` / `↑` | Jump (press again mid-air for a double jump) |
| `Z` or `J` | Melee **360° spin** or **shoot bow** (when equipped) |

---

## Bow & Arrows (ranged pickup)

When you defeat an enemy, a **bow set** may spawn at a random spot on the arena (85% chance):

- Glowing golden animation with rotating sparkles
- **10-second countdown** — grab it before it vanishes!
- Each set includes **20 arrows**
- Walk into the pickup to equip the bow
- Press `Z` / `J` to fire arrows at enemies (ranged damage + knockback)
- When arrows run out, you automatically switch back to your melee weapon

---

## Gameplay

1. **Start** — Choose a difficulty on the menu screen.
2. **Battle** — You play as the **blue** stickman. Defeat all red enemies to win.
3. **Win** — Eliminate every enemy; a victory overlay appears.
4. **Lose** — Your health reaches zero; a defeat overlay appears.
5. **Retry or Menu** — Buttons on the Game-Over screen let you play again or change difficulty.

### Tires
Red circular tires are scattered on the floor. Any stickman that walks into one shoves it away — use them to knock enemies off-balance!

### Double jump
You can jump twice in a row: once from the ground, and once more while still in the air. Landing on any platform or the floor resets both jumps.

### Spring balls
Yellow round spring pads are fixed in place on the floor and on platforms. Step on one to launch much higher than a normal jump — and your double jump is refreshed when you bounce!

### 360° weapon attacks
Press attack and your weapon arm spins a full circle. The weapon **tip** is tracked each frame; any enemy the tip touches during the spin takes damage and knockback. An orange burst appears on impact.

---

## Difficulty Modes

| Mode   | Your HP | Enemy Count | Enemy Speed | Enemy Damage | Your Damage Multiplier |
|--------|---------|-------------|-------------|--------------|------------------------|
| Easy   | 150     | 2           | 1.8 px/f    | 5            | ×1.5                   |
| Normal | 100     | 3           | 2.8 px/f    | 10           | ×1.0                   |
| Hard   | 70      | 5           | 4.0 px/f    | 18           | ×0.8                   |

---

## Weapons

| Weapon  | Reach | Damage | Cooldown | Knockback | Visual |
|---------|-------|--------|----------|-----------|--------|
| Sword   | 48 px | 12     | 30 frames | 4      | Long thin blade + crossguard |
| Hammer  | 34 px | 22     | 50 frames | 8      | Short handle + block head |
| Pickaxe | 42 px | 16     | 38 frames | 5.5    | Handle + asymmetric pick head |
| Bow     | ranged | 15 (arrow) | 22 frames | 3   | Pickup only — 20 arrows per set |

Player always starts with the **Sword**. Enemies are equipped based on difficulty (Easy: sword only; Normal: sword + pickaxe; Hard: all three). The **Bow** is only available as a timed pickup after kills.

---

## Level Layout

The single room is 900 × 600 pixels and contains:

```
       [  upper-centre + spring ]

[ left-ledge ]           [ right-ledge ]

  [ mid-left + spring ]         [ mid-right + spring ]

[========= FLOOR + centre spring =========]
```

- **Floor** — full-width at the bottom  
- **Mid-left / mid-right** — 220 px wide platforms at mid height  
- **Upper-centre** — 190 px wide platform above the middle  
- **Left-wall / right-wall ledges** — 130 px wide near the top corners

---

## Project Structure

```
stickman_battle/
├── config.py       # All constants: screen, physics, anatomy, colours,
│                   #   difficulty presets, weapon data, key bindings
├── entities.py     # Every in-game object
│   │
│   ├── HitEffect   # Short-lived orange burst at weapon impact
│   ├── Platform    # Static ledge (dark-blue fill, cyan edge)
│   ├── Tire        # Bouncy red circle with rolling animation
│   ├── SpringBall  # Fixed yellow booster pad (launches stickmen upward)
│   ├── Arrow       # Bow projectile with light gravity arc
│   ├── BowPickup   # Timed shiny bow+arrow pickup (10 s countdown)
│   ├── Stickman    # Base class — procedural drawing + physics + combat
│   ├── Player      # Keyboard-controlled blue stickman
│   └── Enemy       # AI-controlled red stickman (chase → attack → back-off)
│
├── main.py         # Scene management + game loop
│   │
│   ├── MenuScene      # Title + difficulty picker + decorative animation
│   ├── GameScene      # Battle arena (platforms, tires, enemies, HUD)
│   └── GameOverScene  # Win / Lose result with Retry / Menu buttons
│
├── requirements.txt
└── README.md
```

---

## Architecture Notes

### Procedural stickman drawing
Every stickman is rendered frame-by-frame using `pygame.draw.line` and `pygame.draw.circle`. No PNG sprites are loaded. A `_joints()` method computes every body-segment position from:
- `walk_phase` — sinusoidal pendulum swing for legs and arms while moving
- `attack_phase` — weapon arm rotates a full **360°** during an attack swing
- `facing` — mirrors the arm/weapon direction when the character turns

### Combat hit detection
During a spin attack, a circular hit zone follows the **weapon tip** every frame. If the tip overlaps an enemy (or passes within proximity at high spin speed), damage and knockback are applied once per target per swing.

### Physics
Simple Euler integration: gravity adds to `vy` each frame; stickmen land on platforms by checking feet-crossing of platform top surface. Tires get their own bounce coefficient (0.65) and rolling friction. Spring balls apply a fixed upward velocity (`SPRING_BOOST_VEL`) and reset consecutive jump count.

### Enemy AI state machine
```
IDLE ──(player nearby)──► CHASE ──(close enough)──► ATTACK
                                                        │
                                          (hit by player)
                                                        ▼
                                                     BACK-OFF ──► CHASE
```
Enemies randomly jump when the player is on a higher platform.

### Scene transitions
Each scene's `handle_event()` and `update()` return the *next* scene object (or `None` to stay). The main loop replaces `scene` when a non-None value is returned — no global state machine needed.
