# Dungeon 67: The Crypt Below

An original first-person 3D-style dungeon crawler made with Pygame raycasting.
Clear the Crypt of 67, then descend automatically into the tougher Warden's
Depths for a second dungeon and a final boss fight.

## Run

```bash
python3 -m pip install -r requirements.txt
python3 main.py
```

## Controls

| Key | Action |
|---|---|
| W / S or Up / Down | Move forward / backward |
| A / D | Strafe |
| Mouse | Look around |
| 1-5 | Select a hotbar slot |
| Left click / Space | Use the selected item |
| Left / Right arrows | Turn |
| R | Restart the dungeon |
| Esc | Quit |

The hotbar starts with an infinite-use blade and three healing potions.
Select the potion and use it to restore up to 40 health. The other three
slots are empty.

The crypt enemies have been made tougher: zombies have 45 HP and deal 12
damage, while boss 67 has 134 HP and deals 25 damage per hit.

Defeated zombies drop a random Grave Axe or Bone Guard. Walk over a drop to
equip it: axes increase your attack damage, while armor reduces incoming
damage. Boss 67 drops an Iron Sword.

Defeat every enemy in level 1 to enter level 2 automatically. Your health,
potions, and equipment carry over. The level 2 boss has 100 HP; defeating it
automatically replaces the Iron Sword with a stronger Gold Sword. Clear level
2 to finish the game.

The first-person view is drawn with a small raycasting renderer; no 3D engine,
external art, or network service is needed. The mouse is captured while the
game runs.
