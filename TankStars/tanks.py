"""Player and enemy tanks for Tank Stars."""

from __future__ import annotations

import math
from dataclasses import dataclass

import pygame

import config as c
from terrain import Terrain


@dataclass(slots=True)
class Shell:
    """A single ballistic projectile."""

    x: float
    y: float
    vx: float
    vy: float
    team: str  # player | enemy
    damage: float = 34.0
    radius: float = 5.0
    alive: bool = True
    exploded: bool = False
    trail: list[tuple[float, float]] | None = None

    def __post_init__(self) -> None:
        if self.trail is None:
            self.trail = []

    def update(self, dt: float, wind: float, terrain: Terrain) -> bool:
        """Integrate flight; return True if this frame caused an impact."""
        if not self.alive:
            return False
        self.vy += c.GRAVITY * dt
        self.vx += wind * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.trail.append((self.x, self.y))
        if len(self.trail) > 18:
            self.trail.pop(0)
        # Out of bounds
        if self.x < -40 or self.x > c.SCREEN_W + 40 or self.y > c.SCREEN_H + 40:
            self.alive = False
            return True
        if terrain.collides(self.x, self.y):
            self.alive = False
            return True
        return False

    def draw(self, surf: pygame.Surface) -> None:
        if not self.alive and not self.trail:
            return
        for i, (tx, ty) in enumerate(self.trail):
            alpha = int(40 + 200 * (i + 1) / max(1, len(self.trail)))
            r = max(1, int(self.radius * (0.3 + 0.7 * (i + 1) / max(1, len(self.trail)))))
            dot = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(dot, (255, 220, 80, alpha), (r, r), r)
            surf.blit(dot, (int(tx) - r, int(ty) - r))
        if self.alive:
            pygame.draw.circle(
                surf, (40, 40, 45), (int(self.x), int(self.y)), int(self.radius)
            )
            pygame.draw.circle(
                surf, (255, 200, 60), (int(self.x), int(self.y)), int(self.radius) - 1
            )


class Tank:
    """Side-view tank that aims a barrel and fires shells."""

    def __init__(
        self,
        *,
        team: str,
        x: float,
        facing: int,
        body: tuple[int, int, int],
        trim: tuple[int, int, int],
        hp: int | None = None,
    ) -> None:
        self.team = team
        self.x = x
        self.facing = 1 if facing >= 0 else -1
        self.body = body
        self.trim = trim
        self.hp = float(hp if hp is not None else c.TANK_MAX_HP)
        self.max_hp = float(hp if hp is not None else c.TANK_MAX_HP)
        self.aim = 0.55  # elevation above horizontal
        self.power = 50.0
        self.charging = False
        self.alive = True
        self.y = 0.0
        self.tilt = 0.0

    def sync_to_ground(self, terrain: Terrain) -> None:
        """Snap the hull onto the terrain surface."""
        self.y = terrain.height_at(self.x) - 2
        self.tilt = terrain.surface_normal_angle(self.x)

    def move(self, direction: int, dt: float, terrain: Terrain, lo: float, hi: float) -> None:
        """Strafe along the hills within ``[lo, hi]``."""
        if not self.alive:
            return
        self.x += direction * c.MOVE_SPEED * dt
        self.x = max(lo, min(hi, self.x))
        self.sync_to_ground(terrain)

    def adjust_aim(self, delta: float) -> None:
        self.aim = max(0.05, min(math.pi * 0.48, self.aim + delta))

    def adjust_power(self, delta: float) -> None:
        self.power = max(c.POWER_MIN, min(c.POWER_MAX, self.power + delta))

    def muzzle(self) -> tuple[float, float]:
        """World position of the barrel tip."""
        ang = self.aim if self.facing > 0 else math.pi - self.aim
        ang += self.tilt * 0.35
        cx = self.x
        cy = self.y - c.TANK_H * 0.55
        return (
            cx + math.cos(ang) * c.BARREL_LEN,
            cy - math.sin(ang) * c.BARREL_LEN,
        )

    def fire(self) -> Shell:
        """Launch a shell with current aim/power."""
        mx, my = self.muzzle()
        ang = self.aim if self.facing > 0 else math.pi - self.aim
        ang += self.tilt * 0.35
        speed = self.power * c.SHOT_SPEED_SCALE
        return Shell(
            mx,
            my,
            math.cos(ang) * speed,
            -math.sin(ang) * speed,
            team=self.team,
            damage=28.0 + self.power * 0.22,
        )

    def take_damage(self, amount: float) -> None:
        if not self.alive:
            return
        self.hp = max(0.0, self.hp - amount)
        if self.hp <= 0:
            self.alive = False

    def draw(self, surf: pygame.Surface) -> None:
        if not self.alive:
            return
        # Hull
        hull = pygame.Surface((c.TANK_W + 8, c.TANK_H + 16), pygame.SRCALPHA)
        hx, hy = (c.TANK_W + 8) // 2, c.TANK_H + 4
        pygame.draw.ellipse(
            hull, self.trim, pygame.Rect(4, hy - 8, c.TANK_W, 14)
        )  # tracks
        pygame.draw.rect(
            hull,
            self.body,
            pygame.Rect(8, hy - c.TANK_H, c.TANK_W - 8, c.TANK_H - 4),
            border_radius=4,
        )
        pygame.draw.rect(
            hull,
            self.trim,
            pygame.Rect(8, hy - c.TANK_H, c.TANK_W - 8, c.TANK_H - 4),
            width=2,
            border_radius=4,
        )
        # Turret
        pygame.draw.circle(hull, self.body, (hx, hy - c.TANK_H + 6), 10)
        pygame.draw.circle(hull, self.trim, (hx, hy - c.TANK_H + 6), 10, 2)

        rotated = pygame.transform.rotate(hull, -math.degrees(self.tilt))
        rect = rotated.get_rect(midbottom=(int(self.x), int(self.y)))
        surf.blit(rotated, rect)

        # Barrel
        mx, my = self.muzzle()
        base_x = self.x
        base_y = self.y - c.TANK_H * 0.55
        pygame.draw.line(
            surf, self.trim, (int(base_x), int(base_y)), (int(mx), int(my)), 7
        )
        pygame.draw.line(
            surf, (230, 230, 235), (int(base_x), int(base_y)), (int(mx), int(my)), 3
        )
        pygame.draw.circle(surf, (255, 220, 80), (int(mx), int(my)), 3)

    def hitbox(self) -> pygame.Rect:
        return pygame.Rect(
            int(self.x - c.TANK_W * 0.45),
            int(self.y - c.TANK_H - 4),
            int(c.TANK_W * 0.9),
            int(c.TANK_H + 8),
        )
