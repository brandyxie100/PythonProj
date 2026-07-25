# Ragdoll-Hit — Versus Projectile Duel

Pillar-top throwing duels across **30 stages**, with a hit-coin economy, weapon
shop, and defense gear.

- Earn coins by hitting the enemy:
  - **Arms / legs:** +5 coins (1x)
  - **Body (torso):** +10 coins (2x)
  - **Head:** +15 coins (3x)
- Each stage opens with a popup showing the **coin goal** required to pass.
- **Left shop:** weapons (Spear free → Bow → Javelin → Trident → Axe → Broadsword).
  Owning more weapons **slows your dodge** — a full arsenal is heavier to carry.
- **Right shop (from stage 6):** helmets & shields (higher price = stronger
  damage reduction / more durability). Helmets can block instant head-kills
  while intact.
- Stages **16–30** add a **taller second pillar** with an extra enemy.
- Late-stage foes may wear helmets/shields of their own.
- Pass only when the **coin goal** is met and **all enemies** are defeated.
- You start with **3 lives**; each death respawns you on the pillar with a short
  invulnerability window. Game over only when all lives are spent.
- Strafe with `A` / `D` to dodge. Step too far past the pillar edge and you fall.
- Hits spray a small blood burst; a kill triggers a larger multi-layer blood geyser.

## Run

```bash
pip install -r requirements.txt
python main.py
```

## Controls

- `A / D` or `Left / Right`: dodge left / right on the pillar (don't fall off!)
- `W / S` or `Up / Down`: raise / lower aim
- `Space` (hold): charge throw power; release to throw
- Click left shop: buy/equip weapons
- Click right shop: buy/equip helmets & shields
- `E`: cycle owned weapons only
