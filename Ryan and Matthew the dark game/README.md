# Dungeon 67: The Crypt Below

An original first-person 3D-style dungeon crawler made with Pygame raycasting.
Use the **map menu** to pick a room, or run the full campaign:
Crypt of 67 → Warden's Depths → **Boss 3** (1000 HP) in the Abyssal Halls.

## Run

```bash
python3 -m pip install -r requirements.txt
python3 main.py
```

## Menu

| Key | Action |
|---|---|
| ↑↓ / W S | Move selection |
| Enter / 1–6 | Start selected option |
| Esc | Quit |

Options: Full Campaign, six room maps (Crypt, Depths, Abyss/Boss 3, Sunlit
Grove, Spiral, and Level 6: Guardian Arena), Create LAN room, and Join LAN room.

## In-game controls

| Key | Action |
|---|---|
| W / S or Up / Down | Move forward / backward |
| A / D | Strafe |
| Mouse | Look around |
| 1-5 | Select a hotbar slot |
| Left click / Space | Use the selected item |
| Left / Right arrows | Turn |
| R | Restart the current room |
| Esc | Back to map menu |

When your health reaches zero, movement and combat stop. You automatically
respawn at the start of the current level after five seconds with full health.
Your equipment and remaining potions are kept, but enemies in that level
return.

The hotbar starts with an infinite-use blade and three healing potions.
Select the potion and use it to restore up to 40 health. The other three
slots are empty.

The crypt enemies have been made tougher: zombies have 45 HP and deal 12
damage, while boss 67 has 134 HP and deals 25 damage per hit.

Defeated zombies drop a random Grave Axe or Bone Guard. Level 2 zombies drop
stronger Shadow Greatswords (+30 damage) or Dreadplate (blocks 12 damage).
Walk over a drop to equip it:
weapons increase attack damage, while armor reduces incoming damage. Boss 67
drops an Iron Sword. Equipped weapons change appearance and can be used from
their weapon hotbar slot.

Defeat every enemy in level 1 to enter level 2 automatically. Your health,
potions, and equipment carry over. The level 2 boss has 600 HP; defeating it
automatically replaces the Iron Sword with a stronger Gold Sword. Clear level
2 to finish the game.

The standalone Level 6: Guardian Arena features a 1500-HP boss, a healer, and
an arena protector. The protectors shield the boss from your attacks, and the
healer restores its health until both protectors are defeated. Boss 6
teleports around the arena and can unleash a special attack that deals 50
health points.

The first-person view is drawn with a small raycasting renderer; no 3D engine
or external art is needed. The mouse is captured while the game runs.

## Same-WiFi co-op (~3 minutes, two windows)

Both PCs must be on the same WiFi. macOS may ask to allow local network for
Python — allow it. Up to 4 players. One person hosts; the others join. Everyone
shares one map, the same enemies, and the same loot.

1. Window A: menu → **Create LAN room**. Note the 6-digit code. Pick a map and press Enter.
2. Window B: menu → **Join LAN room**. Type that code.
3. Both windows show the same zombies. A kill on one PC disappears on the other.
4. Esc leaves the room and returns to the menu.

Solo menu rows still start a game with no room open.
