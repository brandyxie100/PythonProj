"""First-person ray-cast dungeon crawler with zombies and the boss 67."""

from __future__ import annotations

import math
import random
import sys
from dataclasses import dataclass

import pygame as pg

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
    RoomMap("crypt", "Crypt of 67", "Boss 1: 67", DUNGEON, (2.5, 2.5)),
    RoomMap("depths", "Warden's Depths", "Boss 2: The Warden", DUNGEON_TWO, (2.5, 1.5)),
    RoomMap(
        "abyss",
        "Abyssal Halls",
        "FIND Boss 3 here (1000 HP)",
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
        if self.attack_timer > 0 or self.won or self.health <= 0:
            return False
        self.attack_timer = ATTACK_COOLDOWN
        self.attack_flash = 0.16
        hit_any = False
        for enemy in self.living_enemies:
            dx, dy = enemy.x - self.x, enemy.y - self.y
            distance = math.hypot(dx, dy)
            facing_error = abs((math.atan2(dy, dx) - self.angle + math.pi) % (2 * math.pi) - math.pi)
            if distance <= (1.75 if enemy.boss else 1.45) and facing_error < (0.8 if enemy.boss else 0.65):
                base_damage = 10 if enemy.boss else 15
                enemy.hp -= base_damage + self.weapon_bonus
                hit_any = True
                if enemy.hp <= 0:
                    enemy.alive = False
                    self.kills += 1
                    if enemy.kind == "warden":
                        self.weapon_name = GOLD_SWORD_LOOT.name
                        self.weapon_bonus = GOLD_SWORD_LOOT.value
                        self.message = "The Warden falls! Gold Sword replaces your Iron Sword."
                    elif enemy.kind == "boss3":
                        self.weapon_name = VOID_BLADE_LOOT.name
                        self.weapon_bonus = VOID_BLADE_LOOT.value
                        self.message = "Boss 3 falls! Void Blade surges into your grip."
                    else:
                        self._drop_loot(enemy)
                        rare = (
                            enemy.kind == "boss67"
                            and self.loot_drops
                            and self.loot_drops[-1].loot.name == DIAMOND_SWORD_LOOT.name
                        )
                        if rare:
                            self.message = (
                                f"{enemy.name} defeated! Rare Diamond Sword dropped!"
                            )
                        else:
                            self.message = f"{enemy.name} defeated!"
                    self.message_timer = 1.8
                else:
                    self.message = f"{enemy.name}: {enemy.hp} HP"
                    self.message_timer = 0.8
                break
        if not hit_any:
            self.message = "Your blade cuts through the dark."
            self.message_timer = 0.45
        return hit_any

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

    def _collect_loot(self) -> None:
        remaining: list[LootDrop] = []
        for drop in self.loot_drops:
            if math.hypot(drop.x - self.x, drop.y - self.y) > LOOT_PICKUP_DISTANCE:
                remaining.append(drop)
                continue
            loot = drop.loot
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
            return
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

        for enemy in self.living_enemies:
            enemy.attack_timer = max(0.0, enemy.attack_timer - dt)
            distance = math.hypot(enemy.x - self.x, enemy.y - self.y)
            if distance < 0.58:
                if enemy.attack_timer <= 0:
                    if enemy.kind == "boss3":
                        incoming_damage = BOSS3_DAMAGE
                        enemy.attack_timer = 0.55
                    elif enemy.kind == "warden":
                        incoming_damage = BOSS_DAMAGE + 10
                        enemy.attack_timer = 0.6
                    elif enemy.boss:
                        incoming_damage = BOSS_DAMAGE
                        enemy.attack_timer = BOSS_ATTACK_INTERVAL
                    elif self.room_key in ("depths", "abyss", "spiral"):
                        incoming_damage = ZOMBIE_DAMAGE + 4
                        enemy.attack_timer = 0.7
                    else:
                        incoming_damage = ZOMBIE_DAMAGE
                        enemy.attack_timer = ZOMBIE_ATTACK_INTERVAL
                    self.health -= max(1, incoming_damage - self.armor_value)
                    self.message = f"{enemy.name} hit you!"
                    self.message_timer = 0.8
                    if self.health <= 0:
                        self._begin_death()
                        return
            elif distance < (7.0 if enemy.kind == "boss3" else 6.0 if enemy.boss else 5.0):
                dx = (self.x - enemy.x) / distance
                dy = (self.y - enemy.y) / distance
                if enemy.kind == "boss3":
                    speed = BOSS3_SPEED
                elif enemy.kind == "warden":
                    speed = BOSS_SPEED + 0.2
                elif enemy.boss:
                    speed = BOSS_SPEED
                elif self.room_key in ("depths", "abyss", "spiral"):
                    speed = ZOMBIE_SPEED + 0.1
                else:
                    speed = ZOMBIE_SPEED

                new_x = enemy.x + dx * speed * dt
                new_y = enemy.y + dy * speed * dt
                if not self.is_wall(new_x, enemy.y):
                    enemy.x = new_x
                if not self.is_wall(enemy.x, new_y):
                    enemy.y = new_y

        self._collect_loot()

        if self.health > 0 and not self.living_enemies:
            self._advance_stage()

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
        self._load_stage(self.stage_index)
        self.message = "Respawned. Your equipment and potions are safe."
        self.message_timer = 2.5


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
        scale = 0.9 if enemy.kind == "boss3" else 0.72 if enemy.kind == "warden" else 0.65 if enemy.boss else 0.48
        size = min(SCREEN_H, int(SCREEN_H * scale / distance))
        center_y = horizon + int(SCREEN_H * 0.08 / distance)
        sprite_rect = pg.Rect(screen_x - size // 3, center_y - size // 2, size * 2 // 3, size)
        ray_index = min(RAY_COUNT - 1, max(0, screen_x // RAY_WIDTH))
        if distance >= depths[ray_index]:
            continue
        if enemy.kind == "boss3":
            # Boss 3: tall bone-white / void crown — distinct from crimson/purple bosses.
            body = sprite_rect.inflate(size // 5, size // 6)
            pg.draw.ellipse(screen, (20, 40, 55), body.inflate(size // 2, size // 8))
            pg.draw.rect(screen, (210, 230, 240), body, border_radius=max(4, size // 10))
            pg.draw.rect(screen, (40, 60, 80), body, 3, border_radius=max(4, size // 10))
            # Crown spikes
            for i, ox in enumerate((-size // 3, 0, size // 3)):
                tip = (body.centerx + ox, body.y - size // 6 - (i % 2) * 8)
                pg.draw.polygon(
                    screen,
                    (120, 220, 255),
                    [tip, (tip[0] - 8, body.y + 4), (tip[0] + 8, body.y + 4)],
                )
            # Hollow eyes
            for eye_x in (body.x + size // 5, body.right - size // 5):
                pg.draw.circle(screen, (10, 20, 30), (eye_x, body.y + size // 4), max(4, size // 14))
                pg.draw.circle(screen, (80, 255, 255), (eye_x, body.y + size // 4), max(2, size // 28))
            label = big_font.render("BOSS 3", True, (160, 240, 255))
            screen.blit(label, label.get_rect(center=(screen_x, body.y - size // 5)))
            bar_width = body.width
            pg.draw.rect(screen, (15, 25, 35), (body.x, body.y - 16, bar_width, 8))
            pg.draw.rect(
                screen,
                (80, 220, 255),
                (body.x, body.y - 16, int(bar_width * enemy.hp / enemy.max_hp), 8),
            )
        elif enemy.kind == "warden":
            # Warden: tall violet cloak
            pg.draw.ellipse(screen, (30, 12, 48), sprite_rect.inflate(size // 3, size // 10))
            pg.draw.rect(screen, (70, 35, 110), sprite_rect, border_radius=max(3, size // 8))
            pg.draw.rect(
                screen,
                (160, 90, 220),
                (sprite_rect.x + size // 8, sprite_rect.y + size // 8, size // 2, size // 5),
                border_radius=6,
            )
            for eye_x in (sprite_rect.x + size // 5, sprite_rect.right - size // 5):
                pg.draw.circle(screen, (255, 120, 255), (eye_x, sprite_rect.y + size // 3), max(2, size // 18))
            label = big_font.render(enemy.name, True, (220, 180, 255))
            screen.blit(label, label.get_rect(center=(screen_x, sprite_rect.y - size // 10)))
            bar_width = size * 2 // 3
            pg.draw.rect(screen, (25, 16, 25), (sprite_rect.x, sprite_rect.y - 13, bar_width, 7))
            pg.draw.rect(
                screen,
                (160, 70, 220),
                (sprite_rect.x, sprite_rect.y - 13, int(bar_width * enemy.hp / enemy.max_hp), 7),
            )
        elif enemy.boss:
            # Boss 67: crimson classic
            body_color = (125, 29, 66)
            pg.draw.ellipse(screen, (48, 10, 32), sprite_rect.inflate(size // 3, size // 10))
            pg.draw.rect(screen, body_color, sprite_rect, border_radius=max(3, size // 8))
            pg.draw.rect(screen, (224, 56, 103), (sprite_rect.x + size // 8, sprite_rect.y + size // 8, size // 2, size // 5), border_radius=6)
            for eye_x in (sprite_rect.x + size // 5, sprite_rect.right - size // 5):
                pg.draw.circle(screen, (255, 218, 98), (eye_x, sprite_rect.y + size // 3), max(2, size // 18))
            label = big_font.render(enemy.name, True, (255, 226, 120))
            screen.blit(label, label.get_rect(center=(screen_x, sprite_rect.y - size // 10)))
            bar_width = size * 2 // 3
            pg.draw.rect(screen, (25, 16, 25), (sprite_rect.x, sprite_rect.y - 13, bar_width, 7))
            pg.draw.rect(screen, (221, 42, 75), (sprite_rect.x, sprite_rect.y - 13, int(bar_width * enemy.hp / enemy.max_hp), 7))
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


def draw_hud(screen: pg.Surface, game: DungeonGame, font: pg.font.Font) -> None:
    panel = pg.Rect(16, 14, 270, 104)
    pg.draw.rect(screen, (10, 12, 21), panel, border_radius=8)
    pg.draw.rect(screen, (78, 78, 94), panel, 1, border_radius=8)
    screen.blit(font.render(f"HEALTH  {game.health}", True, (255, 146, 151)), (28, 22))
    screen.blit(font.render(f"ZOMBIES  {sum(not e.boss for e in game.living_enemies)}", True, (180, 218, 163)), (28, 46))
    screen.blit(font.render(f"WEAPON  {game.weapon_name}  (+{game.weapon_bonus})", True, (232, 187, 133)), (28, 70))
    screen.blit(font.render(f"ARMOR  {game.armor_name}  (-{game.armor_value})", True, (178, 221, 175)), (28, 92))
    if game.campaign_mode:
        stage_text = f"CAMPAIGN {game.stage_index + 1}/{len(CAMPAIGN_KEYS)}  {game.stage_name}"
    else:
        stage_text = f"ROOM  {game.stage_name}"
    stage_label = font.render(stage_text, True, (224, 204, 162))
    screen.blit(stage_label, (SCREEN_W - stage_label.get_width() - 20, 54))
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


def draw_menu(
    screen: pg.Surface,
    font: pg.font.Font,
    big_font: pg.font.Font,
    selected: int,
) -> None:
    """Map-select / campaign menu."""
    screen.fill((8, 10, 18))
    title = big_font.render("DUNGEON 67", True, (255, 220, 140))
    screen.blit(title, title.get_rect(center=(SCREEN_W // 2, 56)))
    sub = font.render("Choose a room map, or run the full campaign (Boss 3 finale).", True, (180, 190, 210))
    screen.blit(sub, sub.get_rect(center=(SCREEN_W // 2, 100)))

    options: list[tuple[str, str]] = [
        ("campaign", "Full Campaign  (Crypt → Depths → Boss 3)"),
    ]
    for room in ROOM_MAPS:
        options.append((room.key, f"{room.name}  —  {room.blurb}"))

    for index, (_key, label) in enumerate(options):
        y = 150 + index * 52
        row = pg.Rect(120, y, SCREEN_W - 240, 44)
        active = index == selected
        pg.draw.rect(screen, (50, 70, 50) if active else (22, 26, 38), row, border_radius=8)
        pg.draw.rect(screen, (180, 255, 160) if active else (70, 80, 100), row, 2, border_radius=8)
        color = (240, 255, 230) if active else (200, 205, 215)
        text = font.render(f"{index + 1}.  {label}", True, color)
        screen.blit(text, (row.x + 18, row.y + 12))

    hint = font.render("↑↓ / W S select   ·   Enter play   ·   Esc quit", True, (160, 170, 190))
    screen.blit(hint, hint.get_rect(center=(SCREEN_W // 2, SCREEN_H - 36)))


def main() -> int:
    pg.init()
    pg.display.set_caption("Dungeon 67: The Crypt Below")
    screen = pg.display.set_mode((SCREEN_W, SCREEN_H))
    clock = pg.time.Clock()
    font = pg.font.SysFont("consolas", 17)
    big_font = pg.font.SysFont("consolas", 44, bold=True)
    game = DungeonGame()
    scene = "menu"  # menu | play
    menu_index = 0
    menu_count = 1 + len(ROOM_MAPS)
    running = True

    while running:
        dt = min(clock.tick(FPS) / 1000.0, 0.05)
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
                        if menu_index == 0:
                            game.start_campaign()
                        else:
                            game.start_room(ROOM_MAPS[menu_index - 1].key)
                        scene = "play"
                        pg.mouse.set_visible(False)
                        pg.event.set_grab(True)
                    elif pg.K_1 <= event.key <= pg.K_9:
                        choice = event.key - pg.K_1
                        if choice < menu_count:
                            menu_index = choice
                            if menu_index == 0:
                                game.start_campaign()
                            else:
                                game.start_room(ROOM_MAPS[menu_index - 1].key)
                            scene = "play"
                            pg.mouse.set_visible(False)
                            pg.event.set_grab(True)
                else:
                    if event.key == pg.K_ESCAPE:
                        scene = "menu"
                        pg.event.set_grab(False)
                        pg.mouse.set_visible(True)
                    elif event.key == pg.K_r and (game.health > 0 or game.won):
                        game.reset()
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
        else:
            game.update(dt, pg.key.get_pressed())
            draw_world(screen, game, font, big_font)
        pg.display.flip()

    pg.event.set_grab(False)
    pg.mouse.set_visible(True)
    pg.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
