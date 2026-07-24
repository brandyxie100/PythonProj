# 1942 — Midway Atoll

Classic vertical shoot-’em-up set in the Pacific Theater of WWII. You fly a U.S. Navy interceptor defending Midway Atoll while Japanese air squadrons press the attack on American carriers.

---

## Run

```bash
cd 1942
pip install -r requirements.txt
python main.py
```

Requires **Python 3.11+** and **Pygame 2.6+**.

---

## Controls

| Input | Action |
|-------|--------|
| WASD / Arrow keys | Fly |
| Space | Fire |
| Shift | Loop dodge (brief invulnerability) |
| B | Bomb (clears nearby threats) |
| Enter | Confirm / launch / continue |
| H | Open hangar (from briefing) |
| Esc | Quit / abort / back |

---

## Campaign

- **20 missions** over Midway’s lagoon, reefs, and carrier lanes
- **Boss sorties** on missions 3, 6, 9, 12, 15, 18, and 20
- **Hangar upgrades** between missions (spend banked score): firepower, spread, engines, armor, bomb bay
- **Pickups** in combat: `P` power, `B` bomb, `S` shield, `$` score

### Enemy roster

| Unit | Role |
|------|------|
| Fighter | Weaving Zero-style escorts |
| Interceptor | Aggressive aimed fire |
| Bomber | Twin-engine formations, heavy spray |
| Dive bomber | Stooping attack runs |
| Gunboat | Surface flak from the lagoon |
| Boss fortress | Multi-phase aerial battleship |

### Player kit

- Procedural Wildcat-style fighter with propeller animation
- Upgradeable forward / spread guns
- Classic **loop** escape
- Limited **bombs** for emergency clears

---

## Project layout

```
1942/
├── main.py          # Entry
├── config.py        # Tunables & palette
├── game.py          # State machine & combat loop
├── missions.py      # All 20 mission / wave definitions
├── entities.py      # Player, enemies, boss, bullets, powerups
├── sprites.py       # Procedural aircraft & VFX drawing
├── world.py         # Scrolling Midway ocean
├── ui.py            # Title, briefing, hangar, HUD
└── requirements.txt
```

Graphics are **procedural** (no external sprite pack) so the game runs immediately after installing Pygame.

---

## Design notes for maintainers

- Missions are pure data in `missions.py` — add waves or retune bosses without touching the loop.
- Scroll speed, HP scaling, and fire cadence derive from mission number.
- A portion of score banks into hangar currency on mission clear (`spendable`).
- Collision uses simple axis-aligned boxes; loop dodge empties the player hitbox.

---

## Disclaimer

Inspired by Capcom’s *1942* and Midway history for learning / noncommercial fun. Not affiliated with Capcom or any military organization.
