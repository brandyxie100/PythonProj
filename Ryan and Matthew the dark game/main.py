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


@dataclass
class Enemy:
    x: float
    y: float
    name: str
    hp: int
    max_hp: int
    boss: bool = False
    alive: bool = True
    attack_timer: float = 0.0
    wander_angle: float = 0.0


class DungeonGame:
    def __init__(self) -> None:
        self.rng = random.Random()
        self.reset()

    def reset(self) -> None:
        self.x, self.y = 2.5, 2.5
        self.angle = 0.0
        self.health = 100
        self.kills = 0
        self.attack_timer = 0.0
        self.attack_flash = 0.0
        self.selected_slot = 0
        self.health_potions = 3
        self.won = False
        self.message = "Find the dungeon exit. The boss is waiting below."
        self.message_timer = 4.0
        self.enemies = [
            Enemy(9.5, 2.5, "Crypt Zombie", 30, 30, wander_angle=2.1),
            Enemy(11.5, 7.5, "Crypt Zombie", 30, 30, wander_angle=4.4),
            Enemy(3.5, 11.5, "Crypt Zombie", 30, 30, wander_angle=0.8),
            Enemy(10.5, 11.5, "67", 67, 67, boss=True),
        ]

    @property
    def living_enemies(self) -> list[Enemy]:
        return [enemy for enemy in self.enemies if enemy.alive]

    def is_wall(self, x: float, y: float) -> bool:
        cell_x, cell_y = int(x), int(y)
        if not (0 <= cell_y < len(DUNGEON) and 0 <= cell_x < len(DUNGEON[cell_y])):
            return True
        return DUNGEON[cell_y][cell_x] == "#"

    def move(self, forward: float, sideways: float, dt: float) -> None:
        dx = (math.cos(self.angle) * forward - math.sin(self.angle) * sideways) * PLAYER_SPEED * dt
        dy = (math.sin(self.angle) * forward + math.cos(self.angle) * sideways) * PLAYER_SPEED * dt
        radius = 0.2
        if not self.is_wall(self.x + dx + math.copysign(radius, dx), self.y):
            self.x += dx
        if not self.is_wall(self.x, self.y + dy + math.copysign(radius, dy)):
            self.y += dy

    def attack(self) -> bool:
        if self.attack_timer > 0 or self.won:
            return False
        self.attack_timer = ATTACK_COOLDOWN
        self.attack_flash = 0.16
        hit_any = False
        for enemy in self.living_enemies:
            dx, dy = enemy.x - self.x, enemy.y - self.y
            distance = math.hypot(dx, dy)
            facing_error = abs((math.atan2(dy, dx) - self.angle + math.pi) % (2 * math.pi) - math.pi)
            if distance <= (1.75 if enemy.boss else 1.45) and facing_error < (0.8 if enemy.boss else 0.65):
                enemy.hp -= 10 if enemy.boss else 15
                hit_any = True
                if enemy.hp <= 0:
                    enemy.alive = False
                    self.kills += 1
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

    def select_slot(self, slot: int) -> None:
        if 0 <= slot < HOTBAR_SIZE:
            self.selected_slot = slot

    def use_selected_item(self) -> bool:
        if self.won or self.health <= 0:
            return False
        if self.selected_slot == 0:
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
                    self.health -= 20 if enemy.boss else 8
                    enemy.attack_timer = 0.9 if enemy.boss else 1.1
                    self.message = f"{enemy.name} hit you!"
                    self.message_timer = 0.8
                    if self.health <= 0:
                        self.health = 0
                        self.message = "You fell in the dungeon. Press R to try again."
                        self.message_timer = 999
            elif distance < (5.0 if enemy.boss else 4.0):
                dx = (self.x - enemy.x) / distance
                dy = (self.y - enemy.y) / distance
                speed = 0.6 if enemy.boss else 0.42
                new_x = enemy.x + dx * speed * dt
                new_y = enemy.y + dy * speed * dt
                if not self.is_wall(new_x, enemy.y):
                    enemy.x = new_x
                if not self.is_wall(enemy.x, new_y):
                    enemy.y = new_y

        if self.health > 0 and math.hypot(self.x - 7.5, self.y - 13.5) < 0.65:
            if self.living_enemies:
                self.message = "The exit is sealed. Defeat every zombie and boss 67!"
                self.message_timer = 1.0
            else:
                self.won = True
                self.message = "Dungeon cleared! Press R to explore again."


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
        shade = max(15, 150 - int(distance * 11))
        if math.sin(ray_angle) < 0:
            shade = int(shade * 0.78)
        wall_color = (shade, int(shade * 0.86), int(shade * 0.72))
        rect = pg.Rect(ray * RAY_WIDTH, top, RAY_WIDTH + 1, wall_height)
        pg.draw.rect(screen, wall_color, rect)
        if wall_height > 32:
            seam_color = (max(8, shade - 22), max(8, int(shade * 0.72)), max(8, int(shade * 0.6)))
            pg.draw.line(screen, seam_color, (rect.left, top + wall_height // 2), (rect.right, top + wall_height // 2), 1)

    sprites = sorted(
        game.living_enemies,
        key=lambda enemy: math.hypot(enemy.x - game.x, enemy.y - game.y),
        reverse=True,
    )
    for enemy in sprites:
        dx, dy = enemy.x - game.x, enemy.y - game.y
        distance = math.hypot(dx, dy)
        relative_angle = (math.atan2(dy, dx) - game.angle + math.pi) % (2 * math.pi) - math.pi
        if abs(relative_angle) > FOV / 2 + 0.3 or distance < 0.1:
            continue
        screen_x = int((0.5 + relative_angle / FOV) * SCREEN_W)
        size = min(SCREEN_H, int(SCREEN_H * (0.65 if enemy.boss else 0.48) / distance))
        center_y = horizon + int(SCREEN_H * 0.08 / distance)
        sprite_rect = pg.Rect(screen_x - size // 3, center_y - size // 2, size * 2 // 3, size)
        ray_index = min(RAY_COUNT - 1, max(0, screen_x // RAY_WIDTH))
        if distance >= depths[ray_index]:
            continue
        if enemy.boss:
            body_color = (125, 29, 66)
            pg.draw.ellipse(screen, (48, 10, 32), sprite_rect.inflate(size // 3, size // 10))
            pg.draw.rect(screen, body_color, sprite_rect, border_radius=max(3, size // 8))
            pg.draw.rect(screen, (224, 56, 103), (sprite_rect.x + size // 8, sprite_rect.y + size // 8, size // 2, size // 5), border_radius=6)
            for eye_x in (sprite_rect.x + size // 5, sprite_rect.right - size // 5):
                pg.draw.circle(screen, (255, 218, 98), (eye_x, sprite_rect.y + size // 3), max(2, size // 18))
            label = big_font.render("67", True, (255, 226, 120))
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

    if game.attack_flash > 0:
        blade = pg.Rect(SCREEN_W // 2 + 30, SCREEN_H // 2 - 60, 12, 112)
        pg.draw.polygon(screen, (208, 222, 230), [blade.midtop, blade.topright, blade.midbottom, blade.bottomleft])
        pg.draw.line(screen, (255, 240, 178), blade.midtop, blade.midbottom, 2)

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
        subtitle = font.render("Press R to play again", True, (235, 231, 220))
        screen.blit(title, title.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 20)))
        screen.blit(subtitle, subtitle.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 28)))


def draw_hud(screen: pg.Surface, game: DungeonGame, font: pg.font.Font) -> None:
    panel = pg.Rect(16, 14, 220, 58)
    pg.draw.rect(screen, (10, 12, 21), panel, border_radius=8)
    pg.draw.rect(screen, (78, 78, 94), panel, 1, border_radius=8)
    screen.blit(font.render(f"HEALTH  {game.health}", True, (255, 146, 151)), (28, 22))
    screen.blit(font.render(f"ZOMBIES  {sum(not e.boss for e in game.living_enemies)}", True, (180, 218, 163)), (28, 46))
    boss = next((enemy for enemy in game.living_enemies if enemy.boss), None)
    if boss is not None:
        boss_bar = pg.Rect(SCREEN_W // 2 - 170, 18, 340, 24)
        pg.draw.rect(screen, (13, 12, 20), boss_bar, border_radius=8)
        ratio = boss.hp / boss.max_hp
        fill = pg.Rect(boss_bar.x + 3, boss_bar.y + 3, int((boss_bar.width - 6) * ratio), boss_bar.height - 6)
        pg.draw.rect(screen, (168, 30, 65), fill, border_radius=6)
        label = font.render(f"BOSS 67  {boss.hp}/67", True, (255, 239, 223))
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
    labels = ("Blade", "Potion", "", "", "")

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
            blade_points = [(x + 26, top + 16), (x + 39, top + 18), (x + 30, top + 44), (x + 24, top + 40)]
            pg.draw.polygon(screen, (218, 228, 232), blade_points)
            pg.draw.line(screen, (160, 111, 77), (x + 23, top + 40), (x + 37, top + 46), 4)
            pg.draw.line(screen, (246, 220, 166), (x + 23, top + 43), (x + 35, top + 39), 2)
            count = "INF"
        elif index == 1:
            bottle = pg.Rect(x + 25, top + 19, 22, 27)
            pg.draw.rect(screen, (137, 54, 74), bottle, border_radius=5)
            pg.draw.rect(screen, (214, 112, 121), (x + 29, top + 30, 14, 12), border_radius=3)
            pg.draw.rect(screen, (192, 169, 136), (x + 31, top + 14, 10, 7), border_radius=2)
            count = str(game.health_potions)
        else:
            count = ""

        label = font.render(labels[index], True, (230, 229, 221))
        screen.blit(label, label.get_rect(center=(slot.centerx, top + 54)))
        if count:
            count_text = font.render(count, True, (255, 227, 176))
            screen.blit(count_text, count_text.get_rect(topright=(slot.right - 5, top + 5)))


def main() -> int:
    pg.init()
    pg.display.set_caption("Dungeon 67: The Crypt Below")
    screen = pg.display.set_mode((SCREEN_W, SCREEN_H))
    clock = pg.time.Clock()
    font = pg.font.SysFont("consolas", 17)
    big_font = pg.font.SysFont("consolas", 44, bold=True)
    game = DungeonGame()
    pg.mouse.set_visible(False)
    pg.event.set_grab(True)
    running = True
    while running:
        dt = min(clock.tick(FPS) / 1000.0, 0.05)
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    running = False
                elif event.key == pg.K_r:
                    game.reset()
                elif event.key in (pg.K_1, pg.K_2, pg.K_3, pg.K_4, pg.K_5):
                    game.select_slot(event.key - pg.K_1)
                elif event.key == pg.K_SPACE:
                    game.use_selected_item()
            elif event.type == pg.MOUSEMOTION:
                game.angle += event.rel[0] * MOUSE_SENSITIVITY
            elif event.type == pg.MOUSEBUTTONDOWN and event.button in (1, 3):
                game.use_selected_item()

        game.update(dt, pg.key.get_pressed())
        draw_world(screen, game, font, big_font)
        pg.display.flip()

    pg.event.set_grab(False)
    pg.mouse.set_visible(True)
    pg.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
