# Ragdoll-Hit — Versus Projectile Duel

Pillar-top throwing duels with a **hit-coin economy** and **weapon shop**.

- Earn coins by hitting the enemy:
  - **Arms / legs:** +5 coins (1x)
  - **Body (torso):** +10 coins (2x)
  - **Head:** +15 coins (3x)
- Each stage opens with a popup showing the **coin goal** required to pass.
- Spend coins in the left **weapon shop**. Stronger weapons cost more and deal
  more damage (Spear free → Bow → Javelin → Trident → Axe → Broadsword).
- Pass a stage only when you have **earned the coin goal** and **defeated the
  enemy**. If you kill them early, a new foe spawns so you can keep farming.
- Clear all **7 stages** to win.
- Strafe with `A` / `D` to dodge. Step too far past the pillar edge and you fall.

## Run

```bash
pip install -r requirements.txt
python main.py
```

## Controls

- `A / D` or `Left / Right`: dodge left / right on the pillar (don't fall off!)
- `W / S` or `Up / Down`: raise / lower aim
- `Space` (hold): charge throw power; release to throw
- Click the left shop: buy a locked weapon or equip an owned one
- `E`: cycle owned weapons only
