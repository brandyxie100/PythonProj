"""Tanks, bullets, power-ups, and explosions."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable

import pygame as pg

import config as cfg
from tiles import StageMap

DIR_UP, DIR_RIGHT, DIR_DOWN, DIR_LEFT = 0, 1, 2, 3
DIR_VEC = {
    DIR_UP: (0, -1),
    DIR_RIGHT: (1, 0),
    DIR_DOWN: (0, 1),
    DIR_LEFT: (-1, 0),
}


def _draw_tank_body(
    surface: pg.Surface,
    x: float,
    y: float,
    direction: int,
    color: tuple[int, int, int],
    dark: tuple[int, int, int],
    *,
    level: int = 0,
    flash: bool = False,
) -> None:
    """Draw a 16×16 logical pixel-art tank, scaled to screen."""
    s = cfg.SCALE
    px, py = int(x * s), int(y * s)
    size = cfg.TANK_SIZE * s
    body = cfg.UI_WHITE if flash else color
    track = dark

    # Tracks
    if direction in (DIR_UP, DIR_DOWN):
        pg.draw.rect(surface, track, pg.Rect(px, py, 3 * s, size))
        pg.draw.rect(surface, track, pg.Rect(px + size - 3 * s, py, 3 * s, size))
        pg.draw.rect(surface, body, pg.Rect(px + 3 * s, py + 2 * s, size - 6 * s, size - 4 * s))
    else:
        pg.draw.rect(surface, track, pg.Rect(px, py, size, 3 * s))
        pg.draw.rect(surface, track, pg.Rect(px, py + size - 3 * s, size, 3 * s))
        pg.draw.rect(surface, body, pg.Rect(px + 2 * s, py + 3 * s, size - 4 * s, size - 6 * s))

    # Turret + barrel
    cx, cy = px + size // 2, py + size // 2
    pg.draw.rect(surface, dark, pg.Rect(cx - 3 * s, cy - 3 * s, 6 * s, 6 * s))
    barrel = 7 * s + level * s
    dx, dy = DIR_VEC[direction]
    if dx:
        pg.draw.rect(
            surface,
            body,
            pg.Rect(cx + (2 * s if dx > 0 else -barrel), cy - s, barrel, 2 * s),
        )
    else:
        pg.draw.rect(
            surface,
            body,
            pg.Rect(cx - s, cy + (2 * s if dy > 0 else -barrel), 2 * s, barrel),
        )
    # Star chevrons for upgraded player
    if level >= 1:
        pg.draw.rect(surface, cfg.UI_YELLOW, pg.Rect(cx - 1 * s, cy - 1 * s, 2 * s, 2 * s))


@dataclass
class Bullet:
    """Single tank shell."""

    x: float
    y: float
    direction: int
    friendly: bool
    power: int = 1  # 1 normal, 2 faster, 3 destroys steel
    alive: bool = True
    owner_id: int = 0

    def update(self, dt: float, stage: StageMap) -> None:
        """Move and collide with tiles."""
        if not self.alive:
            return
        dx, dy = DIR_VEC[self.direction]
        spd = cfg.BULLET_SPEED * (1.25 if self.power >= 2 else 1.0)
        self.x += dx * spd * dt
        self.y += dy * spd * dt
        # Bullet center sample
        cx, cy = self.x, self.y
        if cx < 0 or cy < 0 or cx >= cfg.MAP_W * cfg.TILE or cy >= cfg.MAP_H * cfg.TILE:
            self.alive = False
            return
        tx, ty = int(cx) // cfg.TILE, int(cy) // cfg.TILE
        if stage.blocks_bullet(tx, ty):
            # One shell clears one tank-sized brick/steel unit.
            stage.damage_wall_at(cx, cy, self.power)
            self.alive = False

    def hitbox(self) -> pg.Rect:
        r = 2
        return pg.Rect(int(self.x - r), int(self.y - r), r * 2, r * 2)

    def draw(self, surface: pg.Surface) -> None:
        s = cfg.SCALE
        pg.draw.rect(
            surface,
            cfg.UI_WHITE,
            pg.Rect(int(self.x * s) - s, int(self.y * s) - s, 2 * s, 2 * s),
        )


class Tank:
    """Base tank with movement, firing, and HP."""

    _next_id = 1

    def __init__(
        self,
        x: float,
        y: float,
        *,
        friendly: bool,
        kind: str = "player",
    ) -> None:
        self.id = Tank._next_id
        Tank._next_id += 1
        self.x = x
        self.y = y
        self.direction = DIR_UP if friendly else DIR_DOWN
        self.friendly = friendly
        self.kind = kind
        self.alive = True
        self.level = 0  # star upgrades 0..3
        self.hp = 1
        self.fire_cd = 0.0
        self.invuln = cfg.SPAWN_INVULN if friendly else 1.0
        self.shield = 0.0
        self.flash = False
        self.slide_vx = 0.0
        self.slide_vy = 0.0
        self.ai_timer = random.uniform(0.4, 1.2)
        self.ai_dir_time = 0.0
        self.bonus = False  # drops power-up when destroyed
        self._configure_kind()

    def _configure_kind(self) -> None:
        if self.kind == "player":
            self.speed = cfg.PLAYER_SPEED
            self.hp = 1
            self.color = cfg.PLAYER_YELLOW
            self.dark = cfg.PLAYER_DK
        elif self.kind == "fast":
            self.speed = cfg.ENEMY_SPEED_FAST
            self.hp = 1
            self.color = cfg.ENEMY_GRAY
            self.dark = cfg.ENEMY_DK
        elif self.kind == "power":
            self.speed = cfg.ENEMY_SPEED_POWER
            self.hp = 1
            self.level = 1
            self.color = (180, 140, 80)
            self.dark = cfg.ENEMY_DK
        elif self.kind == "armor":
            self.speed = cfg.ENEMY_SPEED_ARMOR
            self.hp = 4
            self.color = cfg.ENEMY_GREEN
            self.dark = (20, 80, 20)
        else:  # basic
            self.speed = cfg.ENEMY_SPEED_BASIC
            self.hp = 1
            self.color = cfg.ENEMY_GRAY
            self.dark = cfg.ENEMY_DK

    def hitbox(self) -> pg.Rect:
        return pg.Rect(int(self.x), int(self.y), cfg.TANK_SIZE, cfg.TANK_SIZE)

    def barrel_pos(self) -> tuple[float, float]:
        dx, dy = DIR_VEC[self.direction]
        cx = self.x + cfg.TANK_SIZE / 2
        cy = self.y + cfg.TANK_SIZE / 2
        return cx + dx * 8, cy + dy * 8

    def try_move(self, dx: float, dy: float, stage: StageMap, tanks: list[Tank]) -> None:
        """Move with tile + tank collision; slight grid assist when turning."""
        if dx == 0 and dy == 0:
            return
        # Snap to grid axis when changing direction (classic feel)
        if dx != 0:
            self.y = round(self.y / (cfg.TILE / 2)) * (cfg.TILE / 2)
            self.direction = DIR_RIGHT if dx > 0 else DIR_LEFT
        if dy != 0:
            self.x = round(self.x / (cfg.TILE / 2)) * (cfg.TILE / 2)
            self.direction = DIR_DOWN if dy > 0 else DIR_UP

        nx = self.x + dx
        ny = self.y + dy
        nx = max(0, min(cfg.MAP_W * cfg.TILE - cfg.TANK_SIZE, nx))
        ny = max(0, min(cfg.MAP_H * cfg.TILE - cfg.TANK_SIZE, ny))
        if stage.rect_blocked(nx, ny):
            return
        # Tank-tank collision
        test = pg.Rect(int(nx), int(ny), cfg.TANK_SIZE, cfg.TANK_SIZE)
        for other in tanks:
            if other is self or not other.alive:
                continue
            if test.colliderect(other.hitbox()):
                return
        self.x, self.y = nx, ny

    def update_player(
        self,
        dt: float,
        keys: pg.key.ScancodeWrapper,
        stage: StageMap,
        tanks: list[Tank],
        spawn_bullet: Callable,
    ) -> None:
        if not self.alive:
            return
        self._tick_timers(dt)
        spd = self.speed * (1.35 if stage.on_ice(self.x, self.y) else 1.0)
        dx = dy = 0.0
        if keys[pg.K_LEFT] or keys[pg.K_a]:
            dx = -spd * dt
        elif keys[pg.K_RIGHT] or keys[pg.K_d]:
            dx = spd * dt
        elif keys[pg.K_UP] or keys[pg.K_w]:
            dy = -spd * dt
        elif keys[pg.K_DOWN] or keys[pg.K_s]:
            dy = spd * dt
        # Ice sliding: keep last velocity
        if stage.on_ice(self.x, self.y):
            if dx or dy:
                self.slide_vx, self.slide_vy = dx, dy
            else:
                dx, dy = self.slide_vx * 0.98, self.slide_vy * 0.98
                self.slide_vx, self.slide_vy = dx, dy
        else:
            self.slide_vx = self.slide_vy = 0.0
        self.try_move(dx, dy, stage, tanks)
        if keys[pg.K_SPACE] and self.fire_cd <= 0:
            self._fire(spawn_bullet)
            self.fire_cd = max(0.16, cfg.PLAYER_FIRE_CD - self.level * 0.06)

    def update_enemy(
        self,
        dt: float,
        stage: StageMap,
        tanks: list[Tank],
        player: Tank | None,
        spawn_bullet: Callable,
        frozen: bool,
    ) -> None:
        if not self.alive or frozen:
            self._tick_timers(dt)
            return
        self._tick_timers(dt)
        self.ai_timer -= dt
        self.ai_dir_time -= dt
        if self.ai_dir_time <= 0:
            self.ai_dir_time = random.uniform(0.6, 1.8)
            # Prefer moving toward player / base
            choices = [DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT]
            if player and player.alive and random.random() < 0.55:
                if abs(player.x - self.x) > abs(player.y - self.y):
                    self.direction = DIR_RIGHT if player.x > self.x else DIR_LEFT
                else:
                    self.direction = DIR_DOWN if player.y > self.y else DIR_UP
            else:
                self.direction = random.choice(choices)
        dx, dy = DIR_VEC[self.direction]
        step = self.speed * dt
        before = (self.x, self.y)
        self.try_move(dx * step, dy * step, stage, tanks)
        if (self.x, self.y) == before:
            self.ai_dir_time = 0  # bump — turn
        if self.fire_cd <= 0 and random.random() < 0.025:
            self._fire(spawn_bullet)
            self.fire_cd = cfg.ENEMY_FIRE_CD * random.uniform(0.7, 1.3)

    def _tick_timers(self, dt: float) -> None:
        self.fire_cd = max(0.0, self.fire_cd - dt)
        self.invuln = max(0.0, self.invuln - dt)
        self.shield = max(0.0, self.shield - dt)
        self.flash = (self.invuln > 0 or self.shield > 0) and int((self.invuln + self.shield) * 15) % 2 == 0

    def _fire(self, spawn_bullet: Callable) -> None:
        bx, by = self.barrel_pos()
        power = 1
        if self.friendly:
            power = 1 + (1 if self.level >= 1 else 0) + (1 if self.level >= 3 else 0)
        elif self.kind == "power" or self.level >= 1:
            power = 2
        spawn_bullet(
            Bullet(bx, by, self.direction, self.friendly, power=power, owner_id=self.id)
        )

    def hurt(self) -> bool:
        """Apply one hit. Returns True if destroyed."""
        if not self.alive or self.invuln > 0 or self.shield > 0:
            return False
        self.hp -= 1
        # Armor tank color stages
        if self.kind == "armor" and self.hp > 0:
            shades = [cfg.ENEMY_GREEN, (160, 160, 40), (180, 100, 40), cfg.ENEMY_RED]
            self.color = shades[max(0, 4 - self.hp)]
            return False
        if self.hp <= 0:
            self.alive = False
            return True
        return False

    def apply_star(self) -> None:
        self.level = min(3, self.level + 1)

    def draw(self, surface: pg.Surface) -> None:
        if not self.alive:
            return
        if self.flash and int(self.invuln * 20) % 2 == 0 and self.shield <= 0:
            return
        # Classic flashing bonus tank
        color = self.color
        if self.bonus and not self.friendly and int(pg.time.get_ticks() / 120) % 2 == 0:
            color = cfg.UI_WHITE
        _draw_tank_body(
            surface,
            self.x,
            self.y,
            self.direction,
            color,
            self.dark,
            level=self.level if self.friendly else (1 if self.kind == "power" else 0),
            flash=self.shield > 0,
        )
        if self.shield > 0:
            s = cfg.SCALE
            pg.draw.rect(
                surface,
                cfg.UI_WHITE,
                pg.Rect(
                    int(self.x * s) - s,
                    int(self.y * s) - s,
                    cfg.TANK_SIZE * s + 2 * s,
                    cfg.TANK_SIZE * s + 2 * s,
                ),
                max(1, s // 2),
            )


@dataclass
class PowerUp:
    """Classic Battle City bonus item."""

    x: float
    y: float
    kind: str  # helmet clock shovel star grenade tank
    alive: bool = True
    blink: float = 0.0

    KINDS = ("helmet", "clock", "shovel", "star", "grenade", "tank")

    def update(self, dt: float) -> None:
        self.blink += dt

    def hitbox(self) -> pg.Rect:
        return pg.Rect(int(self.x), int(self.y), cfg.TANK_SIZE, cfg.TANK_SIZE)

    def draw(self, surface: pg.Surface) -> None:
        if int(self.blink * 8) % 2 == 0:
            return
        s = cfg.SCALE
        px, py = int(self.x * s), int(self.y * s)
        size = cfg.TANK_SIZE * s
        pg.draw.rect(surface, cfg.UI_ORANGE, pg.Rect(px, py, size, size))
        pg.draw.rect(surface, cfg.UI_YELLOW, pg.Rect(px + s, py + s, size - 2 * s, size - 2 * s))
        font = pg.font.SysFont("consolas", 12 * s // 3, bold=True)
        label = {
            "helmet": "H",
            "clock": "C",
            "shovel": "L",
            "star": "*",
            "grenade": "G",
            "tank": "T",
        }[self.kind]
        img = font.render(label, True, cfg.BLACK)
        surface.blit(img, img.get_rect(center=(px + size // 2, py + size // 2)))


@dataclass
class Explosion:
    """Short pixel burst."""

    x: float
    y: float
    life: float = 0.35
    big: bool = False

    def update(self, dt: float) -> None:
        self.life -= dt

    @property
    def alive(self) -> bool:
        return self.life > 0

    def draw(self, surface: pg.Surface) -> None:
        s = cfg.SCALE
        r = int((8 if self.big else 5) * s * (self.life / 0.35))
        pg.draw.circle(surface, cfg.EXPLOSION, (int(self.x * s), int(self.y * s)), max(1, r))
        pg.draw.circle(surface, cfg.UI_YELLOW, (int(self.x * s), int(self.y * s)), max(1, r // 2))
