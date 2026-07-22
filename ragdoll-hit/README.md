# Ragdoll-Hit Stickman Stage Mode

Single-player stickman battle game with:

- Red, blue, and yellow fighters
- Weapons: spear, trident, broadsword, bow, axe, javelin
- Keyboard-controlled movement + limb control
- 180-degree weapon attack swings
- Consecutive jump system (ground jump + one mid-air jump)
- Sequential stage mode (Levels 1 to 6) with multi-tier platforms, ramps,
  floating pads, and hazards for jump combat
- Increasing enemy strength and terrain complexity
- Gold coin rewards per cleared level

## Run

```bash
pip install -r requirements.txt
python main.py
```

## Controls

- `A / D`: move
- `W`: jump (supports one extra mid-air jump)
- `J / L`: rotate primary (weapon) arm
- `U / O`: rotate off-hand arm
- `N / M`: adjust leg pose
- `Space` or `K`: attack (180-degree weapon swing)
- `E`: cycle weapon (spear / trident / broadsword / bow / axe / javelin)

## Stage Goal

Defeat all enemies in each stage to clear the level and earn coins.
Clear Levels **1 -> 6** sequentially to win.

## Versus Projectile Duel Mode

A second, stationary artillery mode inspired by classic stick-figure throwing
duels. Two fighters stand atop pillars and lob weapons across a parabolic arc.

- Weapons: spear, trident, broadsword, and bow (arrows) — each with its own
  damage, drawn shape, and launch speed.
- Projectiles fly along a realistic gravity-driven parabola and **embed** in the
  body on impact.
- Damaged body segments **glow red**. A fighter dies when it takes a **direct
  head wound** or when **more than 80%** of its body has turned red.
- You cannot move — only aim and throw.
- Clear all **5 stages** of escalating AI accuracy to win; each cleared stage
  awards coins.

### Duel Controls

- `W / S` or `Up / Down`: raise / lower aim
- `Space` (hold): charge throw power; release to throw (the stickman winds up
  and throws)
- `E`: cycle weapon
