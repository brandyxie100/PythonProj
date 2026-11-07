"""First-person ray-cast dungeon crawler with zombies and the boss 67."""

from __future__ import annotations

import math
import random
import sys
from dataclasses import dataclass

import pygame as pg

from lan import LanSession, create_room_code, validate_room_code

SCREEN_W = 960
SCREEN_H = 600
FPS = 60
FOV = math.pi / 3
MAX_DEPTH = 16
RAY_COUNT = 240
RAY_WIDTH = SCREEN_W // RAY_COUNT
PLAYER_SPEED = 3.2
MOUSE_SENSITIVITY = 0.003
ATTACK_COOLDOWN = 0.35
HOTBAR_SIZE = 5
POTION_HEAL = 40
ZOMBIE_HP = 45
BOSS_HP = 134
WARDEN_HP = 600
BOSS3_HP = 1000
GOLD_SWORD_DAMAGE = 24
DIAMOND_SWORD_DAMAGE = 18
DIAMOND_SWORD_CHANCE = 0.10
VOID_BLADE_DAMAGE = 40
ZOMBIE_DAMAGE = 12
BOSS_DAMAGE = 25
BOSS3_DAMAGE = 35
ZOMBIE_ATTACK_INTERVAL = 0.85
BOSS_ATTACK_INTERVAL = 0.75
ZOMBIE_SPEED = 0.55
BOSS_SPEED = 0.75
BOSS3_SPEED = 0.85
LOOT_PICKUP_DISTANCE = 0.55
RESPAWN_DELAY = 5.0
MINIMAP_SIZE = 148
MINIMAP_MARGIN = 12

DUNGEON = (
    "###############",
    "#.....#.......#",
    "#.....#.......#",
    "#.....#.......#",
    "#.............#",
    "###.#######.###",
    "#...#.....#...#",
    "#...#.....#...#",
    "#...#.....#...#",
    "#...###.###...#",
    "#.....#.......#",
    "#.....#.......#",
    "#.....#.......#",
    "#.............#",
    "###############",
)

DUNGEON_TWO = (
    "###############",
    "#.......#.....#",
    "#.###...#.....#",
    "#...#...#..##.#",
    "#...#.........#",
    "#.#####.#####.#",
    "#.......#.....#",
    "###.##..#..##.#",
    "#...#...#.....#",
    "#...#..###.##.#",
    "#..##..###....#",
    "#.............#",
    "#.............#",
    "###############",
)

# Open center arena so Boss 3 is reachable (not stuck in a wall).
DUNGEON_THREE = (
    "#################",
    "#.......#.......#",
    "#.###...#...###.#",
    "#.#.............#",
    "#.#...#######...#",
    "#.....#.....#...#",
    "###...#.....#.###",
    "#.....#.....#...#",
    "#.....#.....#...#",
    "#.....#.....#...#",
    "#....#########..#",
    "#...............#",
    "#.###.......###.#",
    "#...............#",
    "#################",
)

DUNGEON_FOUR = (
    "###############",
    "#.............#",
    "#.###...###...#",
    "#.#.......#...#",
    "#.#..###..#.###",
    "#....#.#......#",
    "###..#.#..#####",
    "#....#.#......#",
    "#.###...###...#",
    "#.#.......#...#",
    "#.#..###..#.###",
    "#....#........#",
    "#.............#",
    "###############",
)

DUNGEON_FIVE = (
    "#################",
    "#...............#",
    "#.#############.#",
    "#.#...........#.#",
    "#.#.#########.#.#",
    "#.#.#.......#.#.#",
    "#.#.#.#####.#.#.#",
    "#.#.#.#...#.#.#.#",
    "#.#.#.#.#.#.#.#.#",
    "#.#.#...#...#.#.#",
    "#.#.#########.#.#",
    "#.#...........#.#",
    "#.#############.#",
    "#...............#",
    "#################",
)


@dataclass
class RemotePlayer:
    """Another co-op player sharing this dungeon."""

    player_id: str
    name: str
    x: float
    y: float
    angle: float
    hp: int
    weapon_bonus: int = 0


REMOTE_COLORS = {
    "P2": (255, 196, 87),
    "P3": (120, 220, 255),
    "P4": (255, 140, 90),
}
SPAWN_NUDGES = ((0.0, 0.0), (0.7, 0.0), (0.0, 0.7), (0.7, 0.7))


@dataclass
class Enemy:
    x: float
    y: float
    name: str
    hp: int
    max_hp: int
    boss: bool = False
    kind: str = "zombie"  # zombie | boss67 | warden | boss3
    alive: bool = True
    attack_timer: float = 0.0
    wander_angle: float = 0.0


@dataclass(frozen=True)
class Loot:
    name: str
    kind: str
    value: int
    color: tuple[int, int, int]


@dataclass
class LootDrop:
    x: float
    y: float
    loot: Loot


ZOMBIE_LOOT = (
    Loot("Grave Axe", "weapon", 6, (206, 119, 80)),
    Loot("Bone Guard", "armor", 4, (177, 219, 167)),
)
DEPTH_ZOMBIE_LOOT = (
    Loot("Shadow Greatsword", "weapon", 30, (156, 106, 231)),
    Loot("Dreadplate", "armor", 12, (109, 188, 195)),
)
BOSS_LOOT = Loot("Iron Sword", "weapon", 12, (210, 216, 225))
DIAMOND_SWORD_LOOT = Loot(
    "Diamond Sword", "weapon", DIAMOND_SWORD_DAMAGE, (120, 220, 255)
)
GOLD_SWORD_LOOT = Loot("Gold Sword", "weapon", GOLD_SWORD_DAMAGE, (255, 209, 79))
VOID_BLADE_LOOT = Loot("Void Blade", "weapon", VOID_BLADE_DAMAGE, (180, 120, 255))


def _loot_by_name() -> dict[str, Loot]:
    """Lookup table so a snapshot can rebuild a drop from its name."""
    items = (
        BOSS_LOOT,
        DIAMOND_SWORD_LOOT,
        GOLD_SWORD_LOOT,
        VOID_BLADE_LOOT,
        *ZOMBIE_LOOT,
        *DEPTH_ZOMBIE_LOOT,
    )
    return {item.name: item for item in items}


@dataclass(frozen=True)
class RoomMap:
    """A selectable dungeon room / campaign stage."""

    key: str
    name: str
    blurb: str
    dungeon: tuple[str, ...]
    spawn: tuple[float, float]
    theme: str = "dungeon"  # dungeon | forest


ROOM_MAPS: tuple[RoomMap, ...] = (
    RoomMap("crypt", "Crypt of 67", "Boss 1: Big Bear (Bloxd)", DUNGEON, (2.5, 2.5)),
    RoomMap("depths", "Warden's Depths", "Boss 2: Ghost (Bloxd)", DUNGEON_TWO, (2.5, 1.5)),
    RoomMap(
        "abyss",
        "Abyssal Halls",
        "Boss 3: Deer (Bloxd, 1000 HP)",
        DUNGEON_THREE,
        (1.5, 1.5),
    ),
    RoomMap(
        "crossroads",
        "Sunlit Grove",
        "Bright forest — trees, not stone",
        DUNGEON_FOUR,
        (2.5, 2.5),
        theme="forest",
    ),
    RoomMap("spiral", "Spiral Pit", "Tight spiral corridors", DUNGEON_FIVE, (1.5, 1.5)),
)

# Full campaign order (Boss 3 is the finale).
CAMPAIGN_KEYS: tuple[str, ...] = ("crypt", "depths", "abyss")
ROOM_BY_KEY: dict[str, RoomMap] = {room.key: room for room in ROOM_MAPS}

# Decorative tree billboards for the bright forest map (open floor cells).
FOREST_TREES: tuple[tuple[float, float], ...] = (
    (5.5, 1.5),
    (12.5, 2.5),
    (4.5, 3.5),
    (8.5, 3.5),
    (2.5, 5.5),
    (11.5, 5.5),
    (2.5, 7.5),
    (4.5, 9.5),
    (2.5, 11.5),
    (7.5, 12.5),
    (9.5, 12.5),
)


class DungeonGame:
    def __init__(self) -> None:
        self.rng = random.Random()
        self.campaign_mode = True
        self.room_key = CAMPAIGN_KEYS[0]
        self.net_role = "solo"  # solo | host | client
        self.net_id = ""
        self.net_slot = 0
        self.remote_players: list[RemotePlayer] = []
        self.pending_attack = False
        self._grant_seq = 0
        self._grant_buffer: list[dict] = []
        self._seen_grants: set[int] = set()
        self._hurt_cooldown = 0.0
        self._applied_room: str | None = None
        self.reset()

    def reset(self) -> None:
        self.health = 100
        self.kills = 0
        self.weapon_bonus = 0
        self.weapon_name = "Crypt Blade"
        self.armor_value = 0
        self.armor_name = "None"
        self.loot_drops: list[LootDrop] = []
        self.attack_timer = 0.0
        self.attack_flash = 0.0
        self.selected_slot = 0
        self.health_potions = 3
        self.stage_index = 0
        self.respawn_timer = 0.0
        self.won = False
        self.message = ""
        self.message_timer = 0.0
        self.remote_players = []
        self.pending_attack = False
        self._grant_buffer = []
        self._applied_room = None
        self._hurt_cooldown = 0.0
        if self.campaign_mode:
            self._load_room(CAMPAIGN_KEYS[0])
        else:
            self._load_room(self.room_key)

    def start_campaign(self) -> None:
        """Begin the 3-stage campaign ending with Boss 3."""
        self.campaign_mode = True
        self.room_key = CAMPAIGN_KEYS[0]
        self.reset()

    def start_room(self, room_key: str) -> None:
        """Play a single selected map."""
        if room_key not in ROOM_BY_KEY:
            raise KeyError(room_key)
        self.campaign_mode = False
        self.room_key = room_key
        self.reset()

    @property
    def living_enemies(self) -> list[Enemy]:
        return [enemy for enemy in self.enemies if enemy.alive]

    @property
    def stage_name(self) -> str:
        return ROOM_BY_KEY[self.room_key].name

    def _load_stage(self, stage_index: int) -> None:
        """Campaign helper: load stage by index into CAMPAIGN_KEYS."""
        stage_index = max(0, min(stage_index, len(CAMPAIGN_KEYS) - 1))
        self.campaign_mode = True
        self._load_room(CAMPAIGN_KEYS[stage_index])

    def _load_room(self, room_key: str) -> None:
        room = ROOM_BY_KEY[room_key]
        self.room_key = room_key
        if self.campaign_mode and room_key in CAMPAIGN_KEYS:
            self.stage_index = CAMPAIGN_KEYS.index(room_key)
        self.dungeon_map = room.dungeon
        self.theme = room.theme
        self.x, self.y = room.spawn
        self.angle = 0.0
        self.attack_timer = 0.0
        self.attack_flash = 0.0
        self.loot_drops.clear()
        self.enemies = self._enemies_for_room(room_key)
        self.message = f"{room.name} — {room.blurb}"
        self.message_timer = 4.0

    def _enemies_for_room(self, room_key: str) -> list[Enemy]:
        if room_key == "crypt":
            return [
                Enemy(9.5, 2.5, "Crypt Zombie", ZOMBIE_HP, ZOMBIE_HP, wander_angle=2.1),
                Enemy(11.5, 7.5, "Crypt Zombie", ZOMBIE_HP, ZOMBIE_HP, wander_angle=4.4),
                Enemy(3.5, 11.5, "Crypt Zombie", ZOMBIE_HP, ZOMBIE_HP, wander_angle=0.8),
                Enemy(10.5, 11.5, "67", BOSS_HP, BOSS_HP, boss=True, kind="boss67"),
            ]
        if room_key == "depths":
            return [
                Enemy(11.5, 1.5, "Depth Zombie", 60, 60, wander_angle=1.4),
                Enemy(12.5, 4.5, "Depth Zombie", 60, 60, wander_angle=4.2),
                Enemy(2.5, 8.5, "Depth Zombie", 60, 60, wander_angle=3.0),
                Enemy(11.5, 12.5, "Depth Zombie", 60, 60, wander_angle=0.7),
                Enemy(7.5, 12.5, "The Warden", WARDEN_HP, WARDEN_HP, boss=True, kind="warden"),
            ]
        if room_key == "abyss":
            # Positions verified as open floor cells (Boss 3 in the center arena).
            return [
                Enemy(3.5, 3.5, "Abyss Wraith", 80, 80, wander_angle=1.1),
                Enemy(13.5, 3.5, "Abyss Wraith", 80, 80, wander_angle=2.7),
                Enemy(3.5, 11.5, "Abyss Wraith", 80, 80, wander_angle=4.0),
                Enemy(13.5, 11.5, "Abyss Wraith", 80, 80, wander_angle=0.5),
                Enemy(8.5, 8.5, "Boss 3", BOSS3_HP, BOSS3_HP, boss=True, kind="boss3"),
            ]
        if room_key == "crossroads":
            return [
                Enemy(7.5, 2.5, "Grove Beast", ZOMBIE_HP, ZOMBIE_HP, wander_angle=0.9),
                Enemy(12.5, 7.5, "Grove Beast", ZOMBIE_HP + 10, ZOMBIE_HP + 10, wander_angle=2.2),
                Enemy(4.5, 11.5, "Grove Beast", 55, 55, wander_angle=3.5),
                Enemy(11.5, 11.5, "Grove Beast", 55, 55, wander_angle=5.0),
            ]
        # spiral
        return [
            Enemy(8.5, 2.5, "Crypt Zombie", ZOMBIE_HP, ZOMBIE_HP, wander_angle=1.2),
            Enemy(14.5, 8.5, "Depth Zombie", 60, 60, wander_angle=2.8),
            Enemy(8.5, 8.5, "Depth Zombie", 60, 60, wander_angle=4.1),
            Enemy(3.5, 12.5, "Abyss Wraith", 70, 70, wander_angle=0.4),
        ]

    def _advance_stage(self) -> None:
        for drop in self.loot_drops:
            if drop.loot.kind == "weapon" and drop.loot.value > self.weapon_bonus:
                self.weapon_bonus = drop.loot.value
                self.weapon_name = drop.loot.name
            elif drop.loot.kind == "armor" and drop.loot.value > self.armor_value:
                self.armor_value = drop.loot.value
                self.armor_name = drop.loot.name
        self.loot_drops.clear()
        if not self.campaign_mode:
            self.won = True
            self.message = f"{self.stage_name} cleared! Esc menu · R replay."
            self.message_timer = 999
            return
        if self.stage_index < len(CAMPAIGN_KEYS) - 1:
            self._load_stage(self.stage_index + 1)
        else:
            self.won = True
            self.message = "Campaign cleared — Boss 3 falls! Esc menu · R replay."
            self.message_timer = 999

    def is_wall(self, x: float, y: float) -> bool:
        cell_x, cell_y = int(x), int(y)
        if not (0 <= cell_y < len(self.dungeon_map) and 0 <= cell_x < len(self.dungeon_map[cell_y])):
            return True
        return self.dungeon_map[cell_y][cell_x] == "#"

    def move(self, forward: float, sideways: float, dt: float) -> None:
        if self.health <= 0 or self.won:
            return
        dx = (math.cos(self.angle) * forward - math.sin(self.angle) * sideways) * PLAYER_SPEED * dt
        dy = (math.sin(self.angle) * forward + math.cos(self.angle) * sideways) * PLAYER_SPEED * dt
        radius = 0.2
        if not self.is_wall(self.x + dx + math.copysign(radius, dx), self.y):
            self.x += dx
        if not self.is_wall(self.x, self.y + dy + math.copysign(radius, dy)):
            self.y += dy

    def attack(self) -> bool:
        """Swing the held weapon. Clients only record the swing; the host applies it."""
        if self.attack_timer > 0 or self.won or self.health <= 0:
            return False
        self.attack_timer = ATTACK_COOLDOWN
        self.attack_flash = 0.16
        if self.net_role == "client":
            # One pose flag. The host resolves range so both PCs cannot double-hit.
            self.pending_attack = True
            self.message = "You swing."
            self.message_timer = 0.35
            return True
        return self.resolve_strike(self.x, self.y, self.angle, self.weapon_bonus)

    def resolve_strike(
        self,
        origin_x: float,
        origin_y: float,
        facing: float,
        weapon_bonus: int,
        *,
        striker_id: str = "",
    ) -> bool:
        """Apply one melee hit from a world position. Solo and host only."""
        hit_any = False
        for enemy in self.living_enemies:
            dx, dy = enemy.x - origin_x, enemy.y - origin_y
            distance = math.hypot(dx, dy)
            facing_error = abs((math.atan2(dy, dx) - facing + math.pi) % (2 * math.pi) - math.pi)
            if distance <= (1.75 if enemy.boss else 1.45) and facing_error < (0.8 if enemy.boss else 0.65):
                base_damage = 10 if enemy.boss else 15
                enemy.hp -= base_damage + weapon_bonus
                hit_any = True
                if enemy.hp <= 0:
                    enemy.alive = False
                    self.kills += 1
                    if enemy.kind == "warden":
                        self._give_loot(GOLD_SWORD_LOOT, striker_id)
                        self.message = "The Warden falls! Gold Sword replaces your Iron Sword."
                    elif enemy.kind == "boss3":
                        self._give_loot(VOID_BLADE_LOOT, striker_id)
                        self.message = "Boss 3 falls! Void Blade surges into your grip."
                    else:
                        self._drop_loot(enemy)
                        rare = (
                            enemy.kind == "boss67"
                            and self.loot_drops
                            and self.loot_drops[-1].loot.name == DIAMOND_SWORD_LOOT.name
                        )
                        if rare:
                            self.message = f"{enemy.name} defeated! Rare Diamond Sword dropped!"
                        else:
                            self.message = f"{enemy.name} defeated!"
                    self.message_timer = 1.8
                else:
                    self.message = f"{enemy.name}: {enemy.hp} HP"
                    self.message_timer = 0.8
                break
        if not hit_any and not striker_id:
            self.message = "Your blade cuts through the dark."
            self.message_timer = 0.45
        return hit_any

    def _give_loot(self, loot: Loot, striker_id: str) -> None:
        """Equip boss loot locally, or queue it for the joiner who landed the hit."""
        if not striker_id:
            if loot.kind == "weapon":
                self.weapon_name = loot.name
                self.weapon_bonus = loot.value
            elif loot.kind == "armor":
                self.armor_name = loot.name
                self.armor_value = loot.value
            return
        self._grant_seq += 1
        self._grant_buffer.append(
            {"id": striker_id, "name": loot.name, "nonce": self._grant_seq, "ttl": 8}
        )

    def _coop_spawn(self) -> tuple[float, float]:
        """Spawn point nudged so co-op players do not stack on one cell."""
        base_x, base_y = ROOM_BY_KEY[self.room_key].spawn
        dx, dy = SPAWN_NUDGES[self.net_slot % len(SPAWN_NUDGES)]
        x, y = base_x + dx, base_y + dy
        if self.is_wall(x, y):
            return base_x, base_y
        return x, y

    def _drop_loot(self, enemy: Enemy) -> None:
        """Drop loot at the enemy. Boss 67: 10% Diamond Sword, else Iron Sword."""
        if enemy.kind == "boss67":
            loot = (
                DIAMOND_SWORD_LOOT
                if self.rng.random() < DIAMOND_SWORD_CHANCE
                else BOSS_LOOT
            )
        elif enemy.boss:
            loot = BOSS_LOOT
        else:
            if self.room_key in ("depths", "abyss", "spiral"):
                loot_table = DEPTH_ZOMBIE_LOOT
            else:
                loot_table = ZOMBIE_LOOT
            loot = self.rng.choice(loot_table)
        self.loot_drops.append(LootDrop(enemy.x, enemy.y, loot))

    def _equip(self, loot: Loot) -> None:
        """Keep a drop when it is stronger than what is already held."""
        if loot.kind == "weapon":
            if loot.value > self.weapon_bonus:
                self.weapon_bonus = loot.value
                self.weapon_name = loot.name
                self.message = f"Equipped {loot.name}: +{loot.value} damage."
            else:
                self.message = f"Found {loot.name}, but your weapon is stronger."
        elif loot.kind == "armor":
            if loot.value > self.armor_value:
                self.armor_value = loot.value
                self.armor_name = loot.name
                self.message = f"Equipped {loot.name}: blocks {loot.value} damage."
            else:
                self.message = f"Found {loot.name}, but your armor is stronger."
        self.message_timer = 1.8

    def _collect_loot(self) -> None:
        """Pick up nearby drops. The host can also award a drop to a joiner."""
        seekers: list[tuple[float, float, str]] = []
        if self.health > 0:
            seekers.append((self.x, self.y, ""))
        if self.net_role == "host":
            for peer in self.remote_players:
                if peer.hp > 0:
                    seekers.append((peer.x, peer.y, peer.player_id))
        remaining: list[LootDrop] = []
        for drop in self.loot_drops:
            taken_by: str | None = None
            for seek_x, seek_y, who in seekers:
                if math.hypot(drop.x - seek_x, drop.y - seek_y) <= LOOT_PICKUP_DISTANCE:
                    taken_by = who
                    break
            if taken_by is None:
                remaining.append(drop)
                continue
            if taken_by == "":
                self._equip(drop.loot)
            else:
                self._give_loot(drop.loot, taken_by)
        self.loot_drops = remaining

    def select_slot(self, slot: int) -> None:
        if 0 <= slot < HOTBAR_SIZE:
            self.selected_slot = slot

    def use_selected_item(self) -> bool:
        if self.won or self.health <= 0:
            return False
        if self.selected_slot == 0:
            return self.attack()
        if self.selected_slot == 2 and self.weapon_bonus > 0:
            return self.attack()
        if self.selected_slot == 1:
            if self.health_potions <= 0:
                self.message = "Your health-potion slot is empty."
                self.message_timer = 1.0
                return False
            if self.health >= 100:
                self.message = "You are already at full health."
                self.message_timer = 1.0
                return False
            self.health_potions -= 1
            self.health = min(100, self.health + POTION_HEAL)
            self.message = f"Health restored. {self.health_potions} potion(s) left."
            self.message_timer = 1.2
            return True
        self.message = "That hotbar slot is empty."
        self.message_timer = 0.8
        return False

    def update(self, dt: float, keys: pg.key.ScancodeWrapper) -> None:
        if self.won:
            return
        if self.health <= 0:
            self.respawn_timer = max(0.0, self.respawn_timer - dt)
            if self.respawn_timer == 0:
                self._respawn()
            # Solo and joiners freeze on death. The host still runs the shared fight.
            if self.net_role != "host":
                return
        if self.health > 0:
            self.attack_timer = max(0.0, self.attack_timer - dt)
            self.attack_flash = max(0.0, self.attack_flash - dt)
            self.message_timer = max(0.0, self.message_timer - dt)

            forward = float(keys[pg.K_w] or keys[pg.K_UP]) - float(keys[pg.K_s] or keys[pg.K_DOWN])
            sideways = float(keys[pg.K_d]) - float(keys[pg.K_a])
            if keys[pg.K_LEFT]:
                self.angle -= 1.8 * dt
            if keys[pg.K_RIGHT]:
                self.angle += 1.8 * dt
            if forward or sideways:
                length = math.hypot(forward, sideways)
                self.move(forward / length, sideways / length, dt)

        if self.net_role == "client":
            # Joiners mirror enemy positions from the host. They only feel hits.
            self._hurt_from_enemies(dt)
            return

        for enemy in self.living_enemies:
            enemy.attack_timer = max(0.0, enemy.attack_timer - dt)
            target_x, target_y = self._chase_target(enemy)
            distance = math.hypot(enemy.x - target_x, enemy.y - target_y)
            self_distance = math.hypot(enemy.x - self.x, enemy.y - self.y)
            # Contact damage hits the local body only. Joiners apply their own.
            if self.health > 0 and self_distance < 0.58:
                if enemy.attack_timer <= 0:
                    incoming_damage, cooldown = self._contact_hit(enemy)
                    enemy.attack_timer = cooldown
                    self.health -= max(1, incoming_damage - self.armor_value)
                    self.message = f"{enemy.name} hit you!"
                    self.message_timer = 0.8
                    if self.health <= 0:
                        self._begin_death()
                        if self.net_role != "host":
                            return
            elif 0.05 < distance < (7.0 if enemy.kind == "boss3" else 6.0 if enemy.boss else 5.0):
                dx = (target_x - enemy.x) / distance
                dy = (target_y - enemy.y) / distance
                speed = self._chase_speed(enemy)
                new_x = enemy.x + dx * speed * dt
                new_y = enemy.y + dy * speed * dt
                if not self.is_wall(new_x, enemy.y):
                    enemy.x = new_x
                if not self.is_wall(enemy.x, new_y):
                    enemy.y = new_y

        self._collect_loot()

        if not self.living_enemies and (self.health > 0 or self.net_role == "host"):
            self._advance_stage()

    def _chase_target(self, enemy: Enemy) -> tuple[float, float]:
        """Solo chases the player. The host chases whoever is closest."""
        if self.net_role != "host" or not self.remote_players:
            return self.x, self.y
        options: list[tuple[float, float]] = []
        if self.health > 0:
            options.append((self.x, self.y))
        for peer in self.remote_players:
            if peer.hp > 0:
                options.append((peer.x, peer.y))
        if not options:
            return enemy.x, enemy.y
        return min(options, key=lambda point: math.hypot(enemy.x - point[0], enemy.y - point[1]))

    def _contact_hit(self, enemy: Enemy) -> tuple[int, float]:
        """Damage and cooldown for one enemy melee swing."""
        if enemy.kind == "boss3":
            return BOSS3_DAMAGE, 0.55
        if enemy.kind == "warden":
            return BOSS_DAMAGE + 10, 0.6
        if enemy.boss:
            return BOSS_DAMAGE, BOSS_ATTACK_INTERVAL
        if self.room_key in ("depths", "abyss", "spiral"):
            return ZOMBIE_DAMAGE + 4, 0.7
        return ZOMBIE_DAMAGE, ZOMBIE_ATTACK_INTERVAL

    def _chase_speed(self, enemy: Enemy) -> float:
        """Move speed while an enemy is chasing a player."""
        if enemy.kind == "boss3":
            return BOSS3_SPEED
        if enemy.kind == "warden":
            return BOSS_SPEED + 0.2
        if enemy.boss:
            return BOSS_SPEED
        if self.room_key in ("depths", "abyss", "spiral"):
            return ZOMBIE_SPEED + 0.1
        return ZOMBIE_SPEED

    def _hurt_from_enemies(self, dt: float) -> None:
        """Client-side contact damage using the host's enemy positions."""
        self._hurt_cooldown = max(0.0, self._hurt_cooldown - dt)
        self.message_timer = max(0.0, self.message_timer - dt)
        if self._hurt_cooldown > 0 or self.health <= 0:
            return
        for enemy in self.living_enemies:
            if math.hypot(enemy.x - self.x, enemy.y - self.y) >= 0.58:
                continue
            incoming_damage, cooldown = self._contact_hit(enemy)
            self._hurt_cooldown = cooldown
            self.health -= max(1, incoming_damage - self.armor_value)
            self.message = f"{enemy.name} hit you!"
            self.message_timer = 0.8
            if self.health <= 0:
                self._begin_death()
            return

    def _begin_death(self) -> None:
        if self.health <= 0 and self.respawn_timer > 0:
            return
        self.health = 0
        self.respawn_timer = RESPAWN_DELAY
        self.attack_timer = 0.0
        self.attack_flash = 0.0
        self.message = "You died. Respawning in 5 seconds..."
        self.message_timer = RESPAWN_DELAY

    def _respawn(self) -> None:
        self.health = 100
        self.respawn_timer = 0.0
        if self.net_role == "solo":
            self._load_stage(self.stage_index)
        else:
            # Co-op death reloads this player only. The host keeps the enemies.
            self.x, self.y = self._coop_spawn()
        self.message = "Respawned. Your equipment and potions are safe."
        self.message_timer = 2.5

    def build_snapshot(self) -> dict:
        """Pack the host world so joiners can mirror it."""
        players = [
            {
                "id": self.net_id,
                "name": "P1",
                "x": round(self.x, 3),
                "y": round(self.y, 3),
                "angle": round(self.angle, 4),
                "hp": int(self.health),
            }
        ]
        for peer in self.remote_players:
            players.append(
                {
                    "id": peer.player_id,
                    "name": peer.name,
                    "x": round(peer.x, 3),
                    "y": round(peer.y, 3),
                    "angle": round(peer.angle, 4),
                    "hp": int(peer.hp),
                }
            )
        enemies = [
            {
                "name": enemy.name,
                "x": round(enemy.x, 3),
                "y": round(enemy.y, 3),
                "hp": int(enemy.hp),
                "max_hp": int(enemy.max_hp),
                "alive": enemy.alive,
                "boss": enemy.boss,
                "kind": enemy.kind,
            }
            for enemy in self.enemies
        ]
        loot = [{"x": drop.x, "y": drop.y, "name": drop.loot.name} for drop in self.loot_drops]
        grants = [{key: value for key, value in grant.items() if key != "ttl"} for grant in self._grant_buffer]
        for grant in self._grant_buffer:
            grant["ttl"] = int(grant.get("ttl", 1)) - 1
        self._grant_buffer = [grant for grant in self._grant_buffer if int(grant.get("ttl", 0)) > 0]
        return {
            "room_key": self.room_key,
            "campaign": self.campaign_mode,
            "seq": self._grant_seq,
            "players": players,
            "enemies": enemies,
            "loot": loot,
            "grants": grants,
            "won": self.won,
        }

    def apply_snapshot(self, snap: dict) -> None:
        """Copy the host's map, enemies, loot, and other players. Do not run AI."""
        room_key = str(snap.get("room_key") or self.room_key)
        if room_key not in ROOM_BY_KEY:
            return
        campaign = bool(snap.get("campaign"))
        players = snap.get("players") if isinstance(snap.get("players"), list) else []
        slot = 1
        for index, player in enumerate(players):
            if isinstance(player, dict) and player.get("id") == self.net_id:
                slot = index
                break
        self.net_slot = slot
        if self._applied_room != room_key or self.campaign_mode != campaign:
            health = self.health
            potions = self.health_potions
            weapon_name, weapon_bonus = self.weapon_name, self.weapon_bonus
            armor_name, armor_value = self.armor_name, self.armor_value
            self.campaign_mode = campaign
            self._load_room(room_key)
            self.health = health
            self.health_potions = potions
            self.weapon_name = weapon_name
            self.weapon_bonus = weapon_bonus
            self.armor_name = armor_name
            self.armor_value = armor_value
            self.x, self.y = self._coop_spawn()
            self._applied_room = room_key
        catalog = _loot_by_name()
        self.enemies = []
        for raw in snap.get("enemies") or []:
            if not isinstance(raw, dict):
                continue
            self.enemies.append(
                Enemy(
                    x=float(raw.get("x", 0)),
                    y=float(raw.get("y", 0)),
                    name=str(raw.get("name", "Enemy")),
                    hp=int(raw.get("hp", 1)),
                    max_hp=int(raw.get("max_hp", 1)),
                    boss=bool(raw.get("boss")),
                    kind=str(raw.get("kind", "zombie")),
                    alive=bool(raw.get("alive", True)),
                )
            )
        self.loot_drops = []
        for raw in snap.get("loot") or []:
            if not isinstance(raw, dict):
                continue
            loot = catalog.get(str(raw.get("name", "")))
            if loot is None:
                continue
            self.loot_drops.append(LootDrop(float(raw.get("x", 0)), float(raw.get("y", 0)), loot))
        self.remote_players = []
        for raw in players:
            if not isinstance(raw, dict) or raw.get("id") == self.net_id:
                continue
            self.remote_players.append(
                RemotePlayer(
                    player_id=str(raw.get("id", "")),
                    name=str(raw.get("name", "P?")),
                    x=float(raw.get("x", 0)),
                    y=float(raw.get("y", 0)),
                    angle=float(raw.get("angle", 0)),
                    hp=int(raw.get("hp", 100)),
                )
            )
        for grant in snap.get("grants") or []:
            if not isinstance(grant, dict) or grant.get("id") != self.net_id:
                continue
            nonce = grant.get("nonce")
            if type(nonce) is not int or nonce in self._seen_grants:
                continue
            loot = catalog.get(str(grant.get("name", "")))
            if loot is None:
                continue
            self._seen_grants.add(nonce)
            if loot.name in (GOLD_SWORD_LOOT.name, VOID_BLADE_LOOT.name):
                self.weapon_name = loot.name
                self.weapon_bonus = loot.value
                self.message = f"Equipped {loot.name}."
                self.message_timer = 1.8
            else:
                self._equip(loot)
        self.won = bool(snap.get("won"))


def _voxel_block(
    screen: pg.Surface,
    rect: pg.Rect,
    fill: tuple[int, int, int],
    rim: tuple[int, int, int] | None = None,
) -> None:
    """One Bloxd.io-style cube face: flat fill, dark edge, no round corners."""
    pg.draw.rect(screen, fill, rect)
    edge = rim if rim is not None else (
        max(0, fill[0] - 35),
        max(0, fill[1] - 35),
        max(0, fill[2] - 35),
    )
    pg.draw.rect(screen, edge, rect, max(1, min(3, max(1, rect.width // 14))))


def draw_boss_bear(screen: pg.Surface, cx: int, cy: int, size: int) -> pg.Rect:
    """Bloxd.io Bear: huge light-brown body, dark top stripe, darker legs, red eyes."""
    body_w = max(28, int(size * 0.72))
    body_h = max(32, int(size * 0.82))
    body = pg.Rect(cx - body_w // 2, cy - body_h // 2, body_w, body_h)
    light = (176, 126, 78)
    mid = (140, 92, 52)
    dark = (96, 60, 32)
    stripe = (110, 70, 38)
    # Ground shadow
    pg.draw.ellipse(screen, (28, 16, 8), body.inflate(size // 6, size // 10).move(0, size // 9))
    # Darker lower half (wiki: darker the lower down)
    _voxel_block(screen, body, mid, dark)
    lower = pg.Rect(body.x, body.centery, body_w, body_h // 2)
    _voxel_block(screen, lower, dark, (60, 35, 18))
    # Darker stripe along the top of the back
    top_stripe = pg.Rect(body.x + body_w // 10, body.y, body_w * 4 // 5, max(6, body_h // 7))
    _voxel_block(screen, top_stripe, stripe, dark)
    # Upper light-brown chest / head plate
    head = pg.Rect(body.x + body_w // 8, body.y + body_h // 9, body_w * 3 // 4, body_h // 3)
    _voxel_block(screen, head, light, mid)
    # Block ears
    ear = max(7, size // 9)
    left_ear = pg.Rect(body.x + ear // 3, body.y - ear // 3, ear, ear)
    right_ear = pg.Rect(body.right - ear - ear // 3, body.y - ear // 3, ear, ear)
    _voxel_block(screen, left_ear, mid, dark)
    _voxel_block(screen, right_ear, mid, dark)
    _voxel_block(screen, left_ear.inflate(-ear // 3, -ear // 3), light, mid)
    _voxel_block(screen, right_ear.inflate(-ear // 3, -ear // 3), light, mid)
    # Short snout
    muzzle = pg.Rect(head.centerx - body_w // 7, head.centery, body_w // 3, body_h // 8)
    _voxel_block(screen, muzzle, (198, 150, 100), mid)
    pg.draw.rect(
        screen,
        (40, 24, 14),
        (muzzle.centerx - max(2, size // 30), muzzle.y + 2, max(4, size // 14), max(3, size // 22)),
    )
    # Red eyes (wiki)
    eye = max(4, size // 16)
    for eye_x in (head.x + head.width // 4, head.right - head.width // 4):
        hole = pg.Rect(eye_x - eye // 2, head.y + head.height // 3, eye, eye)
        pg.draw.rect(screen, (40, 10, 10), hole)
        pg.draw.rect(screen, (220, 40, 40), hole.inflate(-eye // 3, -eye // 3))
    return body.union(left_ear).union(right_ear)


def draw_boss_ghost(screen: pg.Surface, cx: int, cy: int, size: int) -> pg.Rect:
    """Bloxd-style spirit ghost: pale translucent voxels, hollow eyes, wavy hem."""
    body_w = max(22, size // 2)
    body_h = max(32, int(size * 0.8))
    body = pg.Rect(cx - body_w // 2, cy - body_h // 2 - size // 18, body_w, body_h)
    sheet = (220, 235, 255)
    mid = (170, 195, 230)
    rim = (110, 140, 180)
    # Soft spirit glow
    glow = pg.Surface((body_w + 24, body_h + 28), pg.SRCALPHA)
    pg.draw.ellipse(glow, (150, 200, 255, 80), glow.get_rect())
    screen.blit(glow, glow.get_rect(center=body.center))
    # Semi-transparent sheet body
    sheet_surf = pg.Surface((body_w, body_h), pg.SRCALPHA)
    sheet_surf.fill((*sheet, 200))
    screen.blit(sheet_surf, body.topleft)
    pg.draw.rect(screen, rim, body, max(1, min(3, body_w // 14)))
    # Head plate slightly brighter
    head = pg.Rect(body.x + body_w // 8, body.y + body_h // 12, body_w * 3 // 4, body_h // 4)
    _voxel_block(screen, head, sheet, rim)
    # Hollow eyes + mouth
    eye = max(5, size // 13)
    for eye_x in (body.x + body_w // 3, body.right - body_w // 3):
        hole = pg.Rect(eye_x - eye // 2, head.centery - eye // 2, eye, eye)
        pg.draw.rect(screen, (25, 35, 55), hole)
        pg.draw.rect(screen, (90, 220, 255), hole.inflate(-eye // 2, -eye // 2))
    mouth = pg.Rect(body.centerx - eye, body.y + body_h * 2 // 5, eye * 2, max(3, eye // 2))
    pg.draw.rect(screen, (30, 40, 60), mouth)
    # Wavy hem flaps
    wave = max(4, body_w // 5)
    for index in range(5):
        wx = body.x + index * wave
        drop = wave // 2 if index % 2 else 0
        flap = pg.Rect(wx, body.bottom - wave // 2, max(2, wave - 1), wave + drop)
        fill = sheet if index % 2 == 0 else mid
        flap_surf = pg.Surface(flap.size, pg.SRCALPHA)
        flap_surf.fill((*fill, 190))
        screen.blit(flap_surf, flap.topleft)
        pg.draw.rect(screen, rim, flap, 1)
    return body


def draw_boss_deer(screen: pg.Surface, cx: int, cy: int, size: int) -> pg.Rect:
    """Bloxd.io Deer: beige body, dark-brown spots, darker legs, slim head + ears."""
    body_w = max(20, int(size * 0.48))
    body_h = max(28, int(size * 0.7))
    body = pg.Rect(cx - body_w // 2, cy - body_h // 3, body_w, body_h)
    beige = (214, 188, 140)
    mid = (180, 148, 100)
    dark = (118, 82, 48)
    spot = (92, 62, 34)
    cream = (236, 220, 185)
    pg.draw.ellipse(screen, (32, 22, 12), body.inflate(size // 7, size // 12).move(0, size // 10))
    _voxel_block(screen, body, beige, mid)
    # Darker lower half
    lower = pg.Rect(body.x, body.y + body_h * 2 // 5, body_w, body_h * 3 // 5)
    _voxel_block(screen, lower, mid, dark)
    # Dark-brown spots around the body (wiki)
    spot_r = max(3, size // 22)
    for ox, oy in (
        (body_w // 5, body_h // 5),
        (body_w * 3 // 5, body_h // 4),
        (body_w // 3, body_h // 2),
        (body_w * 2 // 3, body_h * 3 // 5),
        (body_w // 4, body_h * 3 // 4),
    ):
        pg.draw.rect(screen, spot, (body.x + ox, body.y + oy, spot_r, spot_r))
    # Neck + head
    neck = pg.Rect(body.centerx - body_w // 8, body.y - body_h // 5, body_w // 4, body_h // 4)
    _voxel_block(screen, neck, beige, mid)
    head = pg.Rect(neck.centerx - body_w // 3, neck.y - body_h // 9, body_w * 2 // 3, body_h // 4)
    _voxel_block(screen, head, (200, 168, 118), mid)
    # Long snout
    muzzle = pg.Rect(head.centerx - body_w // 10, head.centery - 1, body_w // 3, body_h // 9)
    _voxel_block(screen, muzzle, cream, mid)
    pg.draw.rect(
        screen,
        dark,
        (muzzle.right - max(3, size // 20), muzzle.centery - 2, max(3, size // 18), max(3, size // 18)),
    )
    # Ears
    ear = max(4, size // 16)
    _voxel_block(screen, pg.Rect(head.x - ear // 2, head.y + ear // 4, ear, ear), mid, dark)
    _voxel_block(screen, pg.Rect(head.right - ear // 2, head.y + ear // 4, ear, ear), mid, dark)
    # Small branched antlers so the boss reads as a deer/stag silhouette
    stem = max(3, size // 22)
    antler = (205, 185, 145)
    for side in (-1, 1):
        base_x = head.centerx + side * head.width // 4
        trunk = pg.Rect(base_x - stem // 2, head.y - size // 6, stem, size // 6)
        _voxel_block(screen, trunk, antler, dark)
        branch = pg.Rect(
            base_x - (size // 9 if side < 0 else 0),
            head.y - size // 6,
            size // 9,
            stem,
        )
        _voxel_block(screen, branch, antler, dark)
    # Dark eyes
    eye = max(2, size // 22)
    for eye_x in (head.x + head.width // 3, head.right - head.width // 3):
        pg.draw.rect(screen, (25, 15, 10), (eye_x - eye // 2, head.y + head.height // 3, eye, eye))
    # Cream belly
    belly = pg.Rect(body.x + body_w // 3, body.y + body_h // 3, body_w // 3, body_h // 2)
    _voxel_block(screen, belly, cream, mid)
    antler_box = pg.Rect(cx - size // 3, cy - size // 2, size * 2 // 3, size // 4)
    return body.union(head).union(antler_box)


def _draw_boss_chrome(
    screen: pg.Surface,
    big_font: pg.font.Font,
    bounds: pg.Rect,
    title: str,
    hp: int,
    max_hp: int,
    *,
    label_color: tuple[int, int, int],
    bar_color: tuple[int, int, int],
) -> None:
    """Boss nameplate and HP bar above a Bloxd-style sprite."""
    label = big_font.render(title, True, label_color)
    screen.blit(label, label.get_rect(center=(bounds.centerx, bounds.y - 22)))
    bar_width = max(40, bounds.width)
    bar = pg.Rect(bounds.centerx - bar_width // 2, bounds.y - 14, bar_width, 8)
    pg.draw.rect(screen, (20, 18, 24), bar)
    fill = max(0, int(bar_width * hp / max(1, max_hp)))
    pg.draw.rect(screen, bar_color, (bar.x, bar.y, fill, bar.height))


def cast_ray(game: DungeonGame, ray_angle: float) -> float:
    """Grid-step a ray through the dungeon and return wall distance."""
    ray_x, ray_y = math.cos(ray_angle), math.sin(ray_angle)
    map_x, map_y = int(game.x), int(game.y)
    delta_x = abs(1 / ray_x) if abs(ray_x) > 1e-8 else 1e8
    delta_y = abs(1 / ray_y) if abs(ray_y) > 1e-8 else 1e8
    step_x = 1 if ray_x >= 0 else -1
    step_y = 1 if ray_y >= 0 else -1
    side_x = (map_x + 1 - game.x) * delta_x if step_x > 0 else (game.x - map_x) * delta_x
    side_y = (map_y + 1 - game.y) * delta_y if step_y > 0 else (game.y - map_y) * delta_y
    side = 0
    distance = 0.0
    for _ in range(64):
        if side_x < side_y:
            side_x += delta_x
            map_x += step_x
            side = 0
            distance = side_x - delta_x
        else:
            side_y += delta_y
            map_y += step_y
            side = 1
            distance = side_y - delta_y
        if game.is_wall(map_x + 0.001, map_y + 0.001):
            if side:
                distance = side_y - delta_y
            else:
                distance = side_x - delta_x
            break
    return max(0.05, min(distance, MAX_DEPTH))


def draw_world(screen: pg.Surface, game: DungeonGame, font: pg.font.Font, big_font: pg.font.Font) -> None:
    horizon = SCREEN_H // 2
    forest = getattr(game, "theme", "dungeon") == "forest"
    if forest:
        # Bright daylight grove: sky + grass instead of crypt gloom.
        screen.fill((150, 205, 245))
        pg.draw.rect(screen, (95, 170, 75), (0, horizon, SCREEN_W, horizon))
        pg.draw.rect(screen, (120, 195, 95), (0, horizon, SCREEN_W, horizon // 3))
    else:
        screen.fill((10, 12, 21))
        pg.draw.rect(screen, (24, 23, 35), (0, horizon, SCREEN_W, horizon))
    depths: list[float] = []
    for ray in range(RAY_COUNT):
        ray_angle = game.angle - FOV / 2 + FOV * ray / RAY_COUNT
        raw_distance = cast_ray(game, ray_angle)
        distance = raw_distance * math.cos(ray_angle - game.angle)
        depths.append(distance)
        wall_height = min(SCREEN_H, int(SCREEN_H / max(distance, 0.1)))
        top = horizon - wall_height // 2
        if forest:
            # Tree-trunk / canopy walls — brighter greens and bark browns.
            shade = max(40, 210 - int(distance * 9))
            if math.sin(ray_angle) < 0:
                shade = int(shade * 0.88)
            bark = int(shade * 0.55)
            wall_color = (bark + 20, shade, int(shade * 0.45))
            seam_color = (max(20, bark - 10), max(30, shade - 35), max(15, int(shade * 0.3)))
        else:
            shade = max(15, 150 - int(distance * 11))
            if math.sin(ray_angle) < 0:
                shade = int(shade * 0.78)
            wall_color = (shade, int(shade * 0.86), int(shade * 0.72))
            seam_color = (max(8, shade - 22), max(8, int(shade * 0.72)), max(8, int(shade * 0.6)))
        rect = pg.Rect(ray * RAY_WIDTH, top, RAY_WIDTH + 1, wall_height)
        pg.draw.rect(screen, wall_color, rect)
        if wall_height > 32:
            pg.draw.line(screen, seam_color, (rect.left, top + wall_height // 2), (rect.right, top + wall_height // 2), 1)
            if forest and wall_height > 48:
                # Canopy fringe on tall tree walls.
                leaf = (max(30, int(shade * 0.55)), min(255, shade + 40), max(25, int(shade * 0.4)))
                pg.draw.line(screen, leaf, (rect.left, top + 4), (rect.right, top + 4), 3)

    if forest:
        for tx, ty in FOREST_TREES:
            dx, dy = tx - game.x, ty - game.y
            distance = math.hypot(dx, dy)
            relative_angle = (math.atan2(dy, dx) - game.angle + math.pi) % (2 * math.pi) - math.pi
            if distance < 0.35 or abs(relative_angle) > FOV / 2 + 0.25:
                continue
            screen_x = int((0.5 + relative_angle / FOV) * SCREEN_W)
            ray_index = min(RAY_COUNT - 1, max(0, screen_x // RAY_WIDTH))
            if distance >= depths[ray_index]:
                continue
            size = min(SCREEN_H, int(SCREEN_H * 0.55 / distance))
            center_y = horizon + int(SCREEN_H * 0.06 / distance)
            trunk = pg.Rect(screen_x - size // 14, center_y - size // 8, max(4, size // 7), size // 2)
            pg.draw.rect(screen, (110, 70, 35), trunk)
            canopy = (screen_x, center_y - size // 3)
            for radius, color in (
                (size // 3, (40, 130, 55)),
                (size // 4, (55, 160, 70)),
                (size // 6, (80, 190, 90)),
            ):
                pg.draw.circle(screen, color, canopy, max(6, radius))

    for peer in game.remote_players:
        dx, dy = peer.x - game.x, peer.y - game.y
        distance = math.hypot(dx, dy)
        relative_angle = (math.atan2(dy, dx) - game.angle + math.pi) % (2 * math.pi) - math.pi
        if distance < 0.2 or abs(relative_angle) > FOV / 2 + 0.25:
            continue
        screen_x = int((0.5 + relative_angle / FOV) * SCREEN_W)
        ray_index = min(RAY_COUNT - 1, max(0, screen_x // RAY_WIDTH))
        # A nearer wall hides the other player.
        if distance >= depths[ray_index]:
            continue
        size = min(SCREEN_H, int(SCREEN_H * 0.42 / distance))
        center_y = horizon + int(SCREEN_H * 0.08 / distance)
        color = REMOTE_COLORS.get(peer.name, (255, 220, 160))
        body = pg.Rect(screen_x - size // 6, center_y - size // 2, size // 3, size)
        pg.draw.rect(screen, color, body, border_radius=max(3, size // 10))
        pg.draw.circle(screen, (30, 24, 20), (body.centerx, body.y + size // 8), max(4, size // 10))
        name = font.render(peer.name, True, color)
        screen.blit(name, name.get_rect(center=(screen_x, body.y - 14)))

    sprites = sorted(
        game.living_enemies,
        key=lambda enemy: math.hypot(enemy.x - game.x, enemy.y - game.y),
        reverse=True,
    )
    for drop in sorted(
        game.loot_drops,
        key=lambda item: math.hypot(item.x - game.x, item.y - game.y),
        reverse=True,
    ):
        dx, dy = drop.x - game.x, drop.y - game.y
        distance = math.hypot(dx, dy)
        relative_angle = (math.atan2(dy, dx) - game.angle + math.pi) % (2 * math.pi) - math.pi
        if distance < 0.1 or abs(relative_angle) > FOV / 2 + 0.2:
            continue
        screen_x = int((0.5 + relative_angle / FOV) * SCREEN_W)
        ray_index = min(RAY_COUNT - 1, max(0, screen_x // RAY_WIDTH))
        if distance >= depths[ray_index]:
            continue
        size = min(58, max(8, int(38 / distance)))
        center_y = horizon + int(SCREEN_H * 0.16 / distance)
        icon = pg.Rect(screen_x - size // 2, center_y - size // 2, size, size)
        pg.draw.circle(screen, (24, 22, 29), icon.center, size // 2 + 5)
        pg.draw.rect(screen, drop.loot.color, icon, border_radius=max(2, size // 5))
        pg.draw.rect(screen, (240, 233, 202), icon, 2, border_radius=max(2, size // 5))
        if size >= 24:
            loot_label = font.render(drop.loot.name, True, (255, 239, 199))
            screen.blit(loot_label, loot_label.get_rect(center=(screen_x, icon.top - 10)))

    for enemy in sprites:
        dx, dy = enemy.x - game.x, enemy.y - game.y
        distance = math.hypot(dx, dy)
        relative_angle = (math.atan2(dy, dx) - game.angle + math.pi) % (2 * math.pi) - math.pi
        if abs(relative_angle) > FOV / 2 + 0.3 or distance < 0.1:
            continue
        screen_x = int((0.5 + relative_angle / FOV) * SCREEN_W)
        # Bear is largest (Bloxd: almost player height). Deer a bit shorter. Ghost tall/floaty.
        scale = (
            0.82 if enemy.kind == "boss3"
            else 0.78 if enemy.kind == "warden"
            else 0.95 if enemy.boss
            else 0.48
        )
        size = min(SCREEN_H, int(SCREEN_H * scale / distance))
        center_y = horizon + int(SCREEN_H * 0.08 / distance)
        sprite_rect = pg.Rect(screen_x - size // 3, center_y - size // 2, size * 2 // 3, size)
        ray_index = min(RAY_COUNT - 1, max(0, screen_x // RAY_WIDTH))
        if distance >= depths[ray_index]:
            continue
        if enemy.kind == "boss3":
            # Boss 3: Bloxd.io deer (beige + spots + antlers).
            bounds = draw_boss_deer(screen, screen_x, center_y, size)
            _draw_boss_chrome(
                screen,
                big_font,
                bounds,
                "DEER",
                enemy.hp,
                enemy.max_hp,
                label_color=(240, 220, 160),
                bar_color=(190, 140, 70),
            )
        elif enemy.kind == "warden":
            # Boss 2: Bloxd-style ghost / spirit sheet.
            bounds = draw_boss_ghost(screen, screen_x, center_y, size)
            _draw_boss_chrome(
                screen,
                big_font,
                bounds,
                "GHOST",
                enemy.hp,
                enemy.max_hp,
                label_color=(190, 220, 255),
                bar_color=(130, 180, 255),
            )
        elif enemy.boss:
            # Boss 1: Bloxd.io big bear (light brown, red eyes).
            bounds = draw_boss_bear(screen, screen_x, center_y, size)
            _draw_boss_chrome(
                screen,
                big_font,
                bounds,
                "BEAR",
                enemy.hp,
                enemy.max_hp,
                label_color=(255, 200, 120),
                bar_color=(180, 70, 35),
            )
        else:
            pg.draw.ellipse(screen, (30, 43, 34), sprite_rect.inflate(size // 4, size // 12))
            pg.draw.rect(screen, (65, 110, 67), sprite_rect, border_radius=max(2, size // 7))
            pg.draw.rect(screen, (105, 145, 83), (sprite_rect.x + size // 9, sprite_rect.y + size // 10, size * 4 // 9, size // 4), border_radius=5)
            eye_y = sprite_rect.y + size // 3
            for eye_x in (sprite_rect.x + size // 5, sprite_rect.right - size // 5):
                pg.draw.circle(screen, (255, 71, 51), (eye_x, eye_y), max(2, size // 20))

    draw_held_item(screen, game)
    draw_hud(screen, game, font)
    if game.message_timer > 0:
        message = font.render(game.message, True, (255, 230, 178))
        box = message.get_rect(center=(SCREEN_W // 2, 70)).inflate(24, 14)
        pg.draw.rect(screen, (11, 12, 22), box, border_radius=8)
        pg.draw.rect(screen, (98, 79, 104), box, 1, border_radius=8)
        screen.blit(message, message.get_rect(center=box.center))
    if game.won or game.health <= 0:
        overlay = pg.Surface((SCREEN_W, SCREEN_H), pg.SRCALPHA)
        overlay.fill((5, 6, 12, 190))
        screen.blit(overlay, (0, 0))
        title = big_font.render("DUNGEON CLEARED" if game.won else "YOU WERE LOST", True, (173, 246, 205) if game.won else (255, 125, 140))
        subtitle_text = (
            "R replay · Esc menu"
            if game.won
            else f"Respawning in {math.ceil(game.respawn_timer)} seconds — movement disabled"
        )
        subtitle = font.render(subtitle_text, True, (235, 231, 220))
        screen.blit(title, title.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 20)))
        screen.blit(subtitle, subtitle.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 28)))


# Original Minecraft-inspired 16×16 sword (diagonal tip → handle). Not Mojang art.
# . empty  O outline  L light blade  M mid blade  D dark blade  H handle  G guard
_MC_SWORD = (
    "................",
    "............LL..",
    "...........LLMM.",
    "..........LLMMD.",
    ".........LLMMD..",
    "........LLMMD...",
    ".......LLMMD....",
    "......LLMMD.....",
    ".....GMMMD......",
    "....GGMD........",
    "...HHGD.........",
    "..HHH...........",
    ".HHHH...........",
    ".HHH............",
    "..H.............",
    "................",
)

_MC_SWORD_PALETTES: dict[str, dict[str, tuple[int, int, int]]] = {
    "Crypt Blade": {
        "O": (40, 40, 48),
        "L": (230, 235, 240),
        "M": (180, 190, 200),
        "D": (120, 130, 145),
        "H": (110, 70, 40),
        "G": (90, 90, 100),
    },
    "Iron Sword": {
        "O": (50, 55, 65),
        "L": (230, 235, 245),
        "M": (175, 185, 200),
        "D": (110, 120, 135),
        "H": (100, 65, 35),
        "G": (95, 100, 110),
    },
    "Diamond Sword": {
        "O": (20, 70, 90),
        "L": (180, 250, 255),
        "M": (80, 220, 230),
        "D": (30, 160, 180),
        "H": (100, 65, 35),
        "G": (40, 140, 160),
    },
    "Gold Sword": {
        "O": (120, 80, 20),
        "L": (255, 245, 160),
        "M": (255, 210, 70),
        "D": (200, 150, 30),
        "H": (100, 65, 35),
        "G": (180, 130, 40),
    },
    "Shadow Greatsword": {
        "O": (40, 20, 60),
        "L": (220, 190, 255),
        "M": (150, 100, 210),
        "D": (90, 50, 140),
        "H": (70, 45, 30),
        "G": (80, 50, 110),
    },
    "Grave Axe": {
        "O": (60, 35, 25),
        "L": (255, 200, 140),
        "M": (210, 120, 80),
        "D": (140, 70, 45),
        "H": (90, 55, 30),
        "G": (100, 70, 45),
    },
    "Void Blade": {
        "O": (40, 10, 70),
        "L": (230, 200, 255),
        "M": (160, 90, 255),
        "D": (90, 40, 160),
        "H": (50, 30, 40),
        "G": (120, 60, 200),
    },
}


def _sword_palette(weapon_name: str) -> dict[str, tuple[int, int, int]]:
    return _MC_SWORD_PALETTES.get(weapon_name, _MC_SWORD_PALETTES["Crypt Blade"])


def build_minecraft_sword_surface(weapon_name: str, pixel: int = 8) -> pg.Surface:
    """Build a chunky pixel sword surface (Minecraft-like silhouette)."""
    size = 16 * pixel
    surf = pg.Surface((size, size), pg.SRCALPHA)
    colors = _sword_palette(weapon_name)
    for row, line in enumerate(_MC_SWORD):
        for col, ch in enumerate(line):
            if ch == ".":
                continue
            color = colors.get(ch, colors["M"])
            pg.draw.rect(surf, color, (col * pixel, row * pixel, pixel, pixel))
    return surf


def blit_minecraft_sword(
    screen: pg.Surface,
    weapon_name: str,
    center: tuple[int, int],
    pixel: int,
    angle_deg: float = -35.0,
) -> None:
    """Draw a rotated Minecraft-style pixel sword centered on a point."""
    sword = build_minecraft_sword_surface(weapon_name, pixel)
    rotated = pg.transform.rotate(sword, angle_deg)
    screen.blit(rotated, rotated.get_rect(center=center))


def draw_held_item(screen: pg.Surface, game: DungeonGame) -> None:
    """Draw a first-person view of whatever is in the selected hotbar slot."""
    # Slight idle bob + attack swing so the held item feels alive.
    bob = math.sin(pg.time.get_ticks() * 0.006) * 6
    swing = 0.0
    if game.attack_flash > 0:
        swing = (0.16 - game.attack_flash) / 0.16
    base_x = SCREEN_W - 160
    base_y = SCREEN_H - 130 + int(bob)

    if game.selected_slot in (0, 2) and (game.selected_slot == 0 or game.weapon_bonus > 0):
        # Minecraft-style pixel sword in the lower-right (swings on attack).
        cx = base_x - int(swing * 110)
        cy = base_y - int(swing * 50)
        angle = -28.0 - swing * 55.0
        blit_minecraft_sword(screen, game.weapon_name, (cx, cy), pixel=10, angle_deg=angle)
    elif game.selected_slot == 1:
        # Health potion bottle in the lower-right hand.
        raise_y = int(swing * 50)
        bottle = pg.Rect(base_x + 95, base_y + 40 - raise_y, 52, 90)
        neck = pg.Rect(bottle.centerx - 10, bottle.y - 18, 20, 22)
        pg.draw.ellipse(screen, (40, 28, 36), bottle.inflate(18, 10).move(0, 70))
        pg.draw.rect(screen, (137, 54, 74), bottle, border_radius=12)
        pg.draw.rect(screen, (214, 112, 121), (bottle.x + 10, bottle.y + 28, 32, 40), border_radius=8)
        pg.draw.rect(screen, (90, 70, 58), neck, border_radius=4)
        pg.draw.rect(screen, (192, 169, 136), (neck.x - 2, neck.y - 6, 24, 10), border_radius=3)
        # Liquid shine
        pg.draw.line(
            screen,
            (255, 180, 190),
            (bottle.x + 14, bottle.y + 36),
            (bottle.x + 14, bottle.y + 70),
            3,
        )
        if game.health_potions <= 0:
            # Dim empty bottle
            empty = pg.Surface(bottle.inflate(8, 8).size, pg.SRCALPHA)
            empty.fill((10, 10, 16, 140))
            screen.blit(empty, bottle.inflate(8, 8).topleft)
    else:
        # Empty hand silhouette for unused slots.
        palm = [
            (base_x + 100, base_y + 120),
            (base_x + 160, base_y + 100),
            (base_x + 180, base_y + 150),
            (base_x + 110, base_y + 170),
        ]
        pg.draw.polygon(screen, (70, 52, 48), palm)
        pg.draw.polygon(screen, (40, 28, 26), palm, 2)


def draw_minimap(screen: pg.Surface, game: DungeonGame, font: pg.font.Font) -> pg.Rect:
    """Top-right tracker: walls, you, zombies, and bosses."""
    dungeon = game.dungeon_map
    rows = len(dungeon)
    cols = len(dungeon[0]) if rows else 1
    top = 42 if game.net_role != "solo" else 14
    frame = pg.Rect(
        SCREEN_W - MINIMAP_SIZE - MINIMAP_MARGIN,
        top,
        MINIMAP_SIZE,
        MINIMAP_SIZE,
    )
    pg.draw.rect(screen, (8, 10, 18), frame, border_radius=8)
    pg.draw.rect(screen, (110, 120, 140), frame, 2, border_radius=8)

    pad = 8
    inner = frame.inflate(-pad * 2, -pad * 2)
    cell = min(inner.width / cols, inner.height / rows)
    map_w = cell * cols
    map_h = cell * rows
    origin_x = inner.x + (inner.width - map_w) / 2
    origin_y = inner.y + (inner.height - map_h) / 2

    def to_screen(wx: float, wy: float) -> tuple[int, int]:
        return (
            int(origin_x + wx * cell),
            int(origin_y + wy * cell),
        )

    # Floor / walls
    for row_i, row in enumerate(dungeon):
        for col_i, tile in enumerate(row):
            rect = pg.Rect(
                int(origin_x + col_i * cell),
                int(origin_y + row_i * cell),
                max(1, int(cell) + 1),
                max(1, int(cell) + 1),
            )
            if tile == "#":
                pg.draw.rect(screen, (48, 52, 68), rect)
            else:
                pg.draw.rect(screen, (22, 26, 36), rect)

    # Living enemies: green zombies, bright boss markers.
    for enemy in game.living_enemies:
        px, py = to_screen(enemy.x, enemy.y)
        if enemy.boss:
            if enemy.kind == "boss3":
                color = (230, 190, 100)
            elif enemy.kind == "warden":
                color = (150, 200, 255)
            else:
                color = (255, 120, 70)
            radius = max(3, int(cell * 0.55))
            pg.draw.circle(screen, color, (px, py), radius)
            pg.draw.circle(screen, (255, 255, 255), (px, py), radius, 1)
        else:
            radius = max(2, int(cell * 0.35))
            pg.draw.circle(screen, (90, 210, 90), (px, py), radius)

    # Co-op allies
    for peer in getattr(game, "remote_players", []):
        if peer.hp <= 0:
            continue
        px, py = to_screen(peer.x, peer.y)
        pg.draw.circle(screen, (255, 200, 80), (px, py), max(2, int(cell * 0.35)))

    # You: cyan wedge pointing where you look.
    you_x, you_y = to_screen(game.x, game.y)
    tip_len = max(6, int(cell * 1.1))
    tip = (
        you_x + int(math.cos(game.angle) * tip_len),
        you_y + int(math.sin(game.angle) * tip_len),
    )
    left = (
        you_x + int(math.cos(game.angle + 2.4) * tip_len * 0.55),
        you_y + int(math.sin(game.angle + 2.4) * tip_len * 0.55),
    )
    right = (
        you_x + int(math.cos(game.angle - 2.4) * tip_len * 0.55),
        you_y + int(math.sin(game.angle - 2.4) * tip_len * 0.55),
    )
    pg.draw.polygon(screen, (90, 230, 255), [tip, left, right])
    pg.draw.circle(screen, (255, 255, 255), (you_x, you_y), 2)

    title = font.render("MAP", True, (210, 220, 235))
    screen.blit(title, (frame.x + 8, frame.y + 4))
    # Legend under the frame: cyan you, green zombie, orange boss.
    legend_y = frame.bottom + 6
    items = (
        ((90, 230, 255), "you"),
        ((90, 210, 90), "zombie"),
        ((255, 120, 70), "boss"),
    )
    x = frame.x
    for color, label in items:
        pg.draw.circle(screen, color, (x + 4, legend_y + 7), 4)
        text = font.render(label, True, (170, 180, 195))
        screen.blit(text, (x + 12, legend_y))
        x += text.get_width() + 22
    return frame


def draw_hud(screen: pg.Surface, game: DungeonGame, font: pg.font.Font) -> None:
    panel_top = 42 if game.net_role != "solo" else 14
    panel = pg.Rect(16, panel_top, 270, 104)
    pg.draw.rect(screen, (10, 12, 21), panel, border_radius=8)
    pg.draw.rect(screen, (78, 78, 94), panel, 1, border_radius=8)
    screen.blit(font.render(f"HEALTH  {game.health}", True, (255, 146, 151)), (28, panel_top + 8))
    screen.blit(font.render(f"ZOMBIES  {sum(not e.boss for e in game.living_enemies)}", True, (180, 218, 163)), (28, panel_top + 32))
    screen.blit(font.render(f"WEAPON  {game.weapon_name}  (+{game.weapon_bonus})", True, (232, 187, 133)), (28, panel_top + 56))
    screen.blit(font.render(f"ARMOR  {game.armor_name}  (-{game.armor_value})", True, (178, 221, 175)), (28, panel_top + 78))
    minimap = draw_minimap(screen, game, font)
    if game.campaign_mode:
        stage_text = f"CAMPAIGN {game.stage_index + 1}/{len(CAMPAIGN_KEYS)}  {game.stage_name}"
    else:
        stage_text = f"ROOM  {game.stage_name}"
    stage_label = font.render(stage_text, True, (224, 204, 162))
    # Keep room name just left of the minimap so the tracker stays clear.
    screen.blit(
        stage_label,
        (minimap.x - stage_label.get_width() - 12, minimap.y + 6),
    )
    boss = next((enemy for enemy in game.living_enemies if enemy.boss), None)
    if boss is not None:
        boss_bar = pg.Rect(SCREEN_W // 2 - 170, 18, 340, 24)
        pg.draw.rect(screen, (13, 12, 20), boss_bar, border_radius=8)
        ratio = boss.hp / boss.max_hp
        fill = pg.Rect(boss_bar.x + 3, boss_bar.y + 3, int((boss_bar.width - 6) * ratio), boss_bar.height - 6)
        pg.draw.rect(screen, (168, 30, 65), fill, border_radius=6)
        label = font.render(f"BOSS {boss.name}  {boss.hp}/{boss.max_hp}", True, (255, 239, 223))
        screen.blit(label, label.get_rect(center=boss_bar.center))
    cross = SCREEN_W // 2, SCREEN_H // 2
    pg.draw.line(screen, (235, 236, 220), (cross[0] - 8, cross[1]), (cross[0] + 8, cross[1]), 2)
    pg.draw.line(screen, (235, 236, 220), (cross[0], cross[1] - 8), (cross[0], cross[1] + 8), 2)
    draw_hotbar(screen, game, font)
    hint = font.render("WASD move  |  Mouse look  |  1-5 select  |  Click / Space use  |  R restart", True, (205, 206, 214))
    screen.blit(hint, hint.get_rect(center=(SCREEN_W // 2, SCREEN_H - 12)))


def draw_hotbar(screen: pg.Surface, game: DungeonGame, font: pg.font.Font) -> None:
    slot_width = 72
    slot_height = 66
    gap = 8
    total_width = HOTBAR_SIZE * slot_width + (HOTBAR_SIZE - 1) * gap
    start_x = (SCREEN_W - total_width) // 2
    top = SCREEN_H - slot_height - 34
    labels = (
        "Blade",
        "Potion",
        game.weapon_name[:9] if game.weapon_bonus else "",
        game.armor_name[:9] if game.armor_value else "",
        "",
    )

    for index in range(HOTBAR_SIZE):
        x = start_x + index * (slot_width + gap)
        slot = pg.Rect(x, top, slot_width, slot_height)
        selected = index == game.selected_slot
        fill = (48, 42, 48) if selected else (17, 19, 29)
        border = (255, 207, 123) if selected else (91, 94, 111)
        pg.draw.rect(screen, fill, slot, border_radius=8)
        pg.draw.rect(screen, border, slot, 3 if selected else 1, border_radius=8)
        screen.blit(font.render(str(index + 1), True, (255, 221, 161) if selected else (184, 187, 200)), (x + 6, top + 4))

        if index == 0:
            blit_minecraft_sword(
                screen, game.weapon_name, (slot.centerx, top + 30), pixel=2, angle_deg=-35.0
            )
            count = "INF"
        elif index == 1:
            bottle = pg.Rect(x + 25, top + 19, 22, 27)
            pg.draw.rect(screen, (137, 54, 74), bottle, border_radius=5)
            pg.draw.rect(screen, (214, 112, 121), (x + 29, top + 30, 14, 12), border_radius=3)
            pg.draw.rect(screen, (192, 169, 136), (x + 31, top + 14, 10, 7), border_radius=2)
            count = str(game.health_potions)
        elif index == 2 and game.weapon_bonus:
            blit_minecraft_sword(
                screen, game.weapon_name, (slot.centerx, top + 30), pixel=2, angle_deg=-35.0
            )
            count = f"+{game.weapon_bonus}"
        elif index == 3 and game.armor_value:
            pg.draw.polygon(
                screen,
                (177, 219, 167),
                [(x + 36, top + 16), (x + 49, top + 22), (x + 46, top + 38), (x + 36, top + 47), (x + 26, top + 38), (x + 23, top + 22)],
            )
            count = f"-{game.armor_value}"
        else:
            count = ""

        label = font.render(labels[index], True, (230, 229, 221))
        screen.blit(label, label.get_rect(center=(slot.centerx, top + 54)))
        if count:
            count_text = font.render(count, True, (255, 227, 176))
            screen.blit(count_text, count_text.get_rect(topright=(slot.right - 5, top + 5)))


def menu_entries() -> list[tuple[str, str]]:
    """Solo maps, then create/join for same-WiFi co-op."""
    entries = [("campaign", "Full Campaign  (Crypt → Depths → Boss 3)")]
    for room in ROOM_MAPS:
        entries.append((room.key, f"{room.name}  —  {room.blurb}"))
    entries.append(("lan-create", "Create LAN room"))
    entries.append(("lan-join", "Join LAN room"))
    return entries


def draw_menu(
    screen: pg.Surface,
    font: pg.font.Font,
    big_font: pg.font.Font,
    selected: int,
) -> None:
    """Map-select / campaign menu."""
    screen.fill((8, 10, 18))
    title = big_font.render("DUNGEON 67", True, (255, 220, 140))
    screen.blit(title, title.get_rect(center=(SCREEN_W // 2, 48)))
    sub = font.render("Solo maps, or create / join a room on the same WiFi.", True, (180, 190, 210))
    screen.blit(sub, sub.get_rect(center=(SCREEN_W // 2, 88)))

    for index, (_key, label) in enumerate(menu_entries()):
        y = 112 + index * 52
        row = pg.Rect(120, y, SCREEN_W - 240, 44)
        active = index == selected
        pg.draw.rect(screen, (50, 70, 50) if active else (22, 26, 38), row, border_radius=8)
        pg.draw.rect(screen, (180, 255, 160) if active else (70, 80, 100), row, 2, border_radius=8)
        color = (240, 255, 230) if active else (200, 205, 215)
        text = font.render(f"{index + 1}.  {label}", True, color)
        screen.blit(text, (row.x + 18, row.y + 12))

    hint = font.render("↑↓ / W S select   ·   Enter play   ·   Esc quit", True, (160, 170, 190))
    screen.blit(hint, hint.get_rect(center=(SCREEN_W // 2, SCREEN_H - 28)))


def draw_lan_bar(screen: pg.Surface, font: pg.font.Font, *, code: str, role: str, count: int) -> None:
    """Top bar with the room code, role, and player count."""
    bar = pg.Rect(0, 0, SCREEN_W, 32)
    pg.draw.rect(screen, (16, 28, 24), bar)
    pg.draw.line(screen, (120, 200, 140), (0, 31), (SCREEN_W, 31), 2)
    label = font.render(f"ROOM {code}    {role}    Players {count}", True, (220, 255, 220))
    screen.blit(label, (16, 8))


def _draw_choice_rows(
    screen: pg.Surface,
    font: pg.font.Font,
    entries: list[tuple[str, str]],
    selected: int,
    top: int,
) -> None:
    """Draw a vertical list of selectable rows."""
    for index, (_key, label) in enumerate(entries):
        y = top + index * 48
        row = pg.Rect(120, y, SCREEN_W - 240, 40)
        active = index == selected
        pg.draw.rect(screen, (50, 70, 50) if active else (22, 26, 38), row, border_radius=8)
        pg.draw.rect(screen, (180, 255, 160) if active else (70, 80, 100), row, 2, border_radius=8)
        color = (240, 255, 230) if active else (200, 205, 215)
        text = font.render(f"{index + 1}.  {label}", True, color)
        screen.blit(text, (row.x + 18, row.y + 10))


def lobby_entries() -> list[tuple[str, str]]:
    """Maps the host can start once the room exists."""
    return menu_entries()[:-2]


def main() -> int:
    """Run the menu, solo crawler, or a same-WiFi co-op room."""
    pg.init()
    pg.display.set_caption("Dungeon 67: The Crypt Below")
    screen = pg.display.set_mode((SCREEN_W, SCREEN_H))
    clock = pg.time.Clock()
    font = pg.font.SysFont("consolas", 17)
    big_font = pg.font.SysFont("consolas", 44, bold=True)
    game = DungeonGame()
    scene = "menu"  # menu | lobby | join | wait | play
    menu_index = 0
    lobby_index = 0
    join_code = ""
    lan_status = ""
    hello_timer = 0.0
    session: LanSession | None = None
    running = True

    def close_session() -> None:
        """Leave the LAN room and return this window to solo."""
        nonlocal session
        if session is not None:
            session.close()
            session = None
        game.net_role = "solo"
        game.remote_players = []
        game.pending_attack = False

    def enter_play() -> None:
        nonlocal scene
        scene = "play"
        pg.mouse.set_visible(False)
        pg.event.set_grab(True)

    def leave_play() -> None:
        nonlocal scene
        close_session()
        scene = "menu"
        pg.event.set_grab(False)
        pg.mouse.set_visible(True)

    def start_solo(index: int) -> None:
        close_session()
        if index == 0:
            game.start_campaign()
        else:
            game.start_room(ROOM_MAPS[index - 1].key)
        enter_play()

    def create_lan() -> None:
        nonlocal session, scene, lan_status, lobby_index
        close_session()
        try:
            session = LanSession(create_room_code(), host=True)
        except (OSError, ValueError) as exc:
            lan_status = str(exc)
            return
        game.net_role = "host"
        game.net_id = session.player_id
        lobby_index = 0
        lan_status = ""
        scene = "lobby"

    def confirm_join() -> None:
        nonlocal session, scene, lan_status, hello_timer
        try:
            session = LanSession(validate_room_code(join_code), host=False)
        except (OSError, ValueError) as exc:
            lan_status = str(exc)
            return
        game.net_role = "client"
        game.net_id = session.player_id
        session.send_hello()
        hello_timer = 0.0
        lan_status = "Waiting for host…"
        scene = "wait"

    def start_hosted(index: int) -> None:
        if session is None:
            return
        if index == 0:
            game.start_campaign()
        else:
            game.start_room(lobby_entries()[index][0])
        game.net_role = "host"
        game.net_id = session.player_id
        enter_play()

    def activate_menu(index: int) -> None:
        nonlocal join_code, lan_status, scene
        key = menu_entries()[index][0]
        if key == "lan-create":
            create_lan()
        elif key == "lan-join":
            close_session()
            join_code = ""
            lan_status = "Type the 6-digit code, then Enter."
            scene = "join"
        else:
            start_solo(index)

    while running:
        dt = min(clock.tick(FPS) / 1000.0, 0.05)
        menu_count = len(menu_entries())
        lobby_count = len(lobby_entries())
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.KEYDOWN:
                if scene == "menu":
                    if event.key == pg.K_ESCAPE:
                        running = False
                    elif event.key in (pg.K_UP, pg.K_w):
                        menu_index = (menu_index - 1) % menu_count
                    elif event.key in (pg.K_DOWN, pg.K_s):
                        menu_index = (menu_index + 1) % menu_count
                    elif event.key in (pg.K_RETURN, pg.K_SPACE):
                        activate_menu(menu_index)
                    elif pg.K_1 <= event.key <= pg.K_9:
                        choice = event.key - pg.K_1
                        if choice < menu_count:
                            menu_index = choice
                            activate_menu(choice)
                elif scene == "lobby":
                    if event.key == pg.K_ESCAPE:
                        close_session()
                        scene = "menu"
                    elif event.key in (pg.K_UP, pg.K_w):
                        lobby_index = (lobby_index - 1) % lobby_count
                    elif event.key in (pg.K_DOWN, pg.K_s):
                        lobby_index = (lobby_index + 1) % lobby_count
                    elif event.key in (pg.K_RETURN, pg.K_SPACE):
                        start_hosted(lobby_index)
                    elif pg.K_1 <= event.key <= pg.K_9:
                        choice = event.key - pg.K_1
                        if choice < lobby_count:
                            lobby_index = choice
                            start_hosted(choice)
                elif scene == "join":
                    if event.key == pg.K_ESCAPE:
                        scene = "menu"
                    elif event.key == pg.K_BACKSPACE:
                        join_code = join_code[:-1]
                    elif event.key in (pg.K_RETURN, pg.K_SPACE) and len(join_code) == 6:
                        confirm_join()
                    elif event.unicode.isdigit() and len(join_code) < 6:
                        join_code += event.unicode
                        if len(join_code) == 6:
                            confirm_join()
                elif scene == "wait":
                    if event.key == pg.K_ESCAPE:
                        close_session()
                        scene = "menu"
                else:
                    if event.key == pg.K_ESCAPE:
                        leave_play()
                    elif event.key == pg.K_r and (game.health > 0 or game.won) and game.net_role != "client":
                        game.reset()
                        if session is not None and session.host:
                            game.net_role = "host"
                            game.net_id = session.player_id
                    elif game.health > 0 and event.key in (pg.K_1, pg.K_2, pg.K_3, pg.K_4, pg.K_5):
                        game.select_slot(event.key - pg.K_1)
                    elif game.health > 0 and event.key == pg.K_SPACE:
                        game.use_selected_item()
            elif scene == "play" and event.type == pg.MOUSEMOTION and game.health > 0:
                game.angle += event.rel[0] * MOUSE_SENSITIVITY
            elif (
                scene == "play"
                and event.type == pg.MOUSEBUTTONDOWN
                and game.health > 0
                and event.button in (1, 3)
            ):
                game.use_selected_item()

        if scene == "menu":
            draw_menu(screen, font, big_font, menu_index)
            if lan_status:
                note = font.render(lan_status, True, (255, 180, 140))
                screen.blit(note, note.get_rect(center=(SCREEN_W // 2, SCREEN_H - 52)))
        elif scene == "lobby" and session is not None:
            session.poll()
            screen.fill((8, 10, 18))
            title = big_font.render(f"ROOM {session.code}", True, (255, 220, 140))
            screen.blit(title, title.get_rect(center=(SCREEN_W // 2, 48)))
            count = 1 + len(session.peers)
            sub = font.render(
                f"HOST  ·  {count} player{'s' if count != 1 else ''}  ·  pick a map to start",
                True,
                (180, 220, 190),
            )
            screen.blit(sub, sub.get_rect(center=(SCREEN_W // 2, 96)))
            _draw_choice_rows(screen, font, lobby_entries(), lobby_index, 130)
            hint = font.render("Enter start   ·   Esc leave room", True, (160, 170, 190))
            screen.blit(hint, hint.get_rect(center=(SCREEN_W // 2, SCREEN_H - 28)))
        elif scene == "join":
            screen.fill((8, 10, 18))
            title = big_font.render("JOIN LAN ROOM", True, (255, 220, 140))
            screen.blit(title, title.get_rect(center=(SCREEN_W // 2, 160)))
            code_label = big_font.render(join_code.ljust(6, "_"), True, (220, 255, 220))
            screen.blit(code_label, code_label.get_rect(center=(SCREEN_W // 2, 260)))
            note = font.render(lan_status or "Type the 6-digit code.", True, (180, 190, 210))
            screen.blit(note, note.get_rect(center=(SCREEN_W // 2, 330)))
            hint = font.render("Esc back", True, (160, 170, 190))
            screen.blit(hint, hint.get_rect(center=(SCREEN_W // 2, SCREEN_H - 28)))
        elif scene == "wait" and session is not None:
            session.poll()
            hello_timer += dt
            if hello_timer >= 0.4:
                session.send_hello()
                hello_timer = 0.0
            if session.rejected:
                lan_status = "That room is full (4 players)."
            elif session.snapshot is not None:
                game.apply_snapshot(session.snapshot)
                enter_play()
            else:
                found = session.lobby_count > 1
                lan_status = (
                    f"Host found ({session.lobby_count}). Waiting for the map…"
                    if found
                    else "Waiting for host…"
                )
            if scene == "wait":
                screen.fill((8, 10, 18))
                title = big_font.render(f"ROOM {session.code}", True, (255, 220, 140))
                screen.blit(title, title.get_rect(center=(SCREEN_W // 2, 200)))
                note = font.render(lan_status, True, (180, 220, 190))
                screen.blit(note, note.get_rect(center=(SCREEN_W // 2, 280)))
                hint = font.render("Esc leave room", True, (160, 170, 190))
                screen.blit(hint, hint.get_rect(center=(SCREEN_W // 2, SCREEN_H - 28)))
        elif scene == "play":
            if session is not None and session.host:
                session.poll()
                for peer in session.take_attacks():
                    game.resolve_strike(
                        peer.x,
                        peer.y,
                        peer.angle,
                        peer.weapon_bonus,
                        striker_id=peer.player_id,
                    )
                game.remote_players = [
                    RemotePlayer(
                        player_id=peer.player_id,
                        name=peer.name,
                        x=peer.x,
                        y=peer.y,
                        angle=peer.angle,
                        hp=peer.hp,
                        weapon_bonus=peer.weapon_bonus,
                    )
                    for peer in session.peers.values()
                ]
                game.update(dt, pg.key.get_pressed())
                if session.snapshot_due():
                    session.send_snapshot(game.build_snapshot(), force=True)
            elif session is not None:
                session.poll()
                if session.snapshot is not None:
                    game.apply_snapshot(session.snapshot)
                game.update(dt, pg.key.get_pressed())
                attacking = game.pending_attack
                game.pending_attack = False
                session.send_pose(
                    x=game.x,
                    y=game.y,
                    angle=game.angle,
                    hp=game.health,
                    attack=attacking,
                    slot=game.selected_slot,
                    weapon_bonus=game.weapon_bonus,
                    force=attacking,
                )
            else:
                game.update(dt, pg.key.get_pressed())
            draw_world(screen, game, font, big_font)
            if session is not None:
                draw_lan_bar(
                    screen,
                    font,
                    code=session.code,
                    role="HOST" if session.host else "JOINED",
                    count=1 + len(session.peers) if session.host else max(session.lobby_count, 1 + len(game.remote_players)),
                )
        pg.display.flip()

    close_session()
    pg.event.set_grab(False)
    pg.mouse.set_visible(True)
    pg.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
