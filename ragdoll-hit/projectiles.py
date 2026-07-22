"""Parabolic thrown-weapon projectiles for the versus duel mode."""

from __future__ import annotations

import math
from dataclasses import dataclass

import pygame

import config as c
from weapon_draw import draw_projectile_weapon

Point = tuple[float, float]


@dataclass(slots=True)
class Projectile:
    """A single weapon in flight following a parabolic trajectory."""

    weapon_key: str
    team: str
    x: float
    y: float
    vx: float
    vy: float
    angle: float = 0.0
    dead: bool = False

    @property
    def stats(self) -> c.ThrowWeaponStats:
        """Return the stats block for this projectile's weapon."""
        return c.THROW_WEAPONS[self.weapon_key]

    @property
    def position(self) -> Point:
        """Current center position."""
        return self.x, self.y

    def tip(self) -> Point:
        """Front tip of the weapon (used for hit detection)."""
        half = self.stats.length * 0.5
        return (
            self.x + math.cos(self.angle) * half,
            self.y + math.sin(self.angle) * half,
        )

    def tail(self) -> Point:
        """Rear end of the weapon (opposite the tip)."""
        half = self.stats.length * 0.5
        return (
            self.x - math.cos(self.angle) * half,
            self.y - math.sin(self.angle) * half,
        )

    def update(self, dt: float, ground_y: float) -> None:
        """Integrate gravity-driven parabolic motion for one step."""
        self.vy += c.PROJECTILE_GRAVITY * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        # Weapon rotates to follow its velocity vector, like a real throw.
        if self.vx != 0.0 or self.vy != 0.0:
            self.angle = math.atan2(self.vy, self.vx)
        if self.y >= ground_y or self.x < -80 or self.x > c.SCREEN_W + 80:
            self.dead = True

    def draw(self, surf: pygame.Surface) -> None:
        """Render the projectile as a multi-part oriented weapon."""
        draw_projectile_weapon(surf, self.weapon_key, self.tail(), self.tip())


def spawn_projectile(
    weapon_key: str,
    team: str,
    origin: Point,
    elevation: float,
    facing: int,
    power: float,
) -> Projectile:
    """Create a projectile launched from ``origin`` at a given elevation/power."""
    stats = c.THROW_WEAPONS[weapon_key]
    speed = power * stats.speed_scale
    vx = facing * math.cos(elevation) * speed
    vy = -math.sin(elevation) * speed
    return Projectile(
        weapon_key=weapon_key,
        team=team,
        x=origin[0],
        y=origin[1],
        vx=vx,
        vy=vy,
        angle=math.atan2(vy, vx),
    )
