"""Parabolic thrown-weapon projectiles for the versus duel mode."""

from __future__ import annotations

import math
from dataclasses import dataclass

import pygame

import config as c

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
        """Render the projectile as an oriented weapon with a tip marker."""
        tail = self.tail()
        tip = self.tip()
        pygame.draw.line(
            surf,
            self.stats.color,
            (int(tail[0]), int(tail[1])),
            (int(tip[0]), int(tip[1])),
            self.stats.thickness,
        )
        _draw_head(surf, self.weapon_key, tail, tip, self.stats.color)


def _draw_head(
    surf: pygame.Surface,
    weapon_key: str,
    tail: Point,
    tip: Point,
    color: tuple[int, int, int],
) -> None:
    """Draw a weapon-specific head/blade near the projectile tip."""
    tx, ty = tip
    angle = math.atan2(tip[1] - tail[1], tip[0] - tail[0])
    if weapon_key == "bow":
        # Arrowhead: two short barbs.
        for sign in (-1, 1):
            bx = tx - math.cos(angle) * 10 + math.cos(angle + sign * 1.9) * 9
            by = ty - math.sin(angle) * 10 + math.sin(angle + sign * 1.9) * 9
            pygame.draw.line(surf, color, (int(tx), int(ty)), (int(bx), int(by)), 2)
    elif weapon_key == "trident":
        # Trident: three prongs at the tip.
        for sign in (-1, 0, 1):
            px = tx + math.cos(angle + sign * 0.35) * 12
            py = ty + math.sin(angle + sign * 0.35) * 12
            pygame.draw.line(surf, color, (int(tx), int(ty)), (int(px), int(py)), 3)
    elif weapon_key == "axe":
        # Axe: a blade set crossways just behind the tip.
        bx = tx - math.cos(angle) * 9
        by = ty - math.sin(angle) * 9
        perp = angle + math.pi / 2
        pygame.draw.line(
            surf,
            color,
            (int(bx - math.cos(perp) * 9), int(by - math.sin(perp) * 9)),
            (int(bx + math.cos(perp) * 9), int(by + math.sin(perp) * 9)),
            5,
        )
    elif weapon_key == "broadsword":
        # Broadsword: a crossguard behind the tip.
        gx = tx - math.cos(angle) * 12
        gy = ty - math.sin(angle) * 12
        perp = angle + math.pi / 2
        pygame.draw.line(
            surf,
            color,
            (int(gx - math.cos(perp) * 8), int(gy - math.sin(perp) * 8)),
            (int(gx + math.cos(perp) * 8), int(gy + math.sin(perp) * 8)),
            3,
        )
    else:  # spear
        pygame.draw.circle(surf, color, (int(tx), int(ty)), 3)


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
