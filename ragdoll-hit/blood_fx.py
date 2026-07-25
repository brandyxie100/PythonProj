"""Blood particle bursts for wound hits and kill moments."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
import pygame

import config as c

Point = tuple[float, float]

# Palette mixes deep crimson with brighter arterial reds.
_BLOOD_COLORS: tuple[tuple[int, int, int], ...] = (
    (150, 12, 18),
    (190, 20, 28),
    (220, 32, 36),
    (255, 48, 42),
    (110, 8, 14),
)


@dataclass(slots=True)
class BloodParticle:
    """A single droplet or mist speck in a blood burst."""

    x: float
    y: float
    vx: float
    vy: float
    radius: float
    life: float
    max_life: float
    color: tuple[int, int, int]
    drag: float = 1.4  # air resistance (higher = slows sooner)
    stretch: float = 1.0  # >1 draws an elongated streak along velocity


@dataclass(slots=True)
class BloodBurstSystem:
    """Owns, advances, and draws all active blood particles."""

    particles: list[BloodParticle] = field(default_factory=list)

    def spawn_hit(self, origin: Point, *, outward: float = 0.0) -> None:
        """Small splash when a stick figure takes damage."""
        self._spawn(
            origin,
            count=c.BLOOD_HIT_COUNT,
            speed_min=c.BLOOD_HIT_SPEED_MIN,
            speed_max=c.BLOOD_HIT_SPEED_MAX,
            life_min=c.BLOOD_HIT_LIFE_MIN,
            life_max=c.BLOOD_HIT_LIFE_MAX,
            radius_min=c.BLOOD_HIT_RADIUS_MIN,
            radius_max=c.BLOOD_HIT_RADIUS_MAX,
            outward=outward,
            stretch_chance=0.2,
            mist=False,
        )

    def spawn_death(self, origin: Point, *, outward: float = 0.0) -> None:
        """Large multi-layer geyser when a stick figure is killed."""
        # Core spray of heavy droplets.
        self._spawn(
            origin,
            count=c.BLOOD_DEATH_COUNT,
            speed_min=c.BLOOD_DEATH_SPEED_MIN,
            speed_max=c.BLOOD_DEATH_SPEED_MAX,
            life_min=c.BLOOD_DEATH_LIFE_MIN,
            life_max=c.BLOOD_DEATH_LIFE_MAX,
            radius_min=c.BLOOD_DEATH_RADIUS_MIN,
            radius_max=c.BLOOD_DEATH_RADIUS_MAX,
            outward=outward,
            stretch_chance=0.55,
            mist=False,
        )
        # Fine mist that hangs and drifts.
        self._spawn(
            origin,
            count=c.BLOOD_DEATH_MIST_COUNT,
            speed_min=40.0,
            speed_max=160.0,
            life_min=0.7,
            life_max=1.6,
            radius_min=1.0,
            radius_max=2.4,
            outward=outward,
            stretch_chance=0.0,
            mist=True,
        )

    def _spawn(
        self,
        origin: Point,
        *,
        count: int,
        speed_min: float,
        speed_max: float,
        life_min: float,
        life_max: float,
        radius_min: float,
        radius_max: float,
        outward: float,
        stretch_chance: float,
        mist: bool,
    ) -> None:
        """Emit ``count`` particles from ``origin`` in a biased radial fan."""
        ox, oy = origin
        for _ in range(count):
            # Prefer upward / outward spray so bursts read against the green sky.
            angle = random.uniform(-math.pi * 0.95, -math.pi * 0.05)
            if outward != 0.0 and random.random() < 0.55:
                # Bias half the spray toward the impact side.
                side = 0.0 if outward > 0.0 else math.pi
                angle = side + random.uniform(-math.pi * 0.55, math.pi * 0.55)
            speed = random.uniform(speed_min, speed_max)
            if mist:
                speed *= random.uniform(0.55, 1.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            # Death bursts get a stronger initial upward kick.
            if not mist and speed_max >= c.BLOOD_DEATH_SPEED_MIN:
                vy -= random.uniform(40.0, 160.0)
            life = random.uniform(life_min, life_max)
            radius = random.uniform(radius_min, radius_max)
            stretch = 1.0
            if stretch_chance > 0.0 and random.random() < stretch_chance:
                stretch = random.uniform(1.6, 2.8)
            self.particles.append(
                BloodParticle(
                    x=ox + random.uniform(-3.0, 3.0),
                    y=oy + random.uniform(-3.0, 3.0),
                    vx=vx,
                    vy=vy,
                    radius=radius,
                    life=life,
                    max_life=life,
                    color=random.choice(_BLOOD_COLORS),
                    drag=0.6 if mist else 1.4,
                    stretch=stretch,
                )
            )

    def update(self, dt: float) -> None:
        """Integrate particles under gravity and cull expired ones."""
        alive: list[BloodParticle] = []
        for p in self.particles:
            p.life -= dt
            if p.life <= 0.0:
                continue
            # Simple drag so sprays fan out then settle.
            damp = max(0.0, 1.0 - p.drag * dt)
            p.vx *= damp
            p.vy *= damp
            p.vy += c.BLOOD_GRAVITY * dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            alive.append(p)
        self.particles = alive

    def draw(self, surf: pygame.Surface) -> None:
        """Draw fading droplets; elongated ones streak along their velocity."""
        if not self.particles:
            return
        # Off-screen alpha layer so per-droplet fade actually composites.
        layer = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        for p in self.particles:
            t = max(0.0, min(1.0, p.life / p.max_life))
            # Quick pop-in then fade — death mist fades more slowly at first.
            alpha = int(255 * (t**0.65))
            if alpha <= 0:
                continue
            color = (*p.color, alpha)
            r = max(1, int(p.radius * (0.55 + 0.45 * t)))
            if p.stretch > 1.05 and (abs(p.vx) + abs(p.vy)) > 20.0:
                speed = math.hypot(p.vx, p.vy) or 1.0
                ux, uy = p.vx / speed, p.vy / speed
                half = r * p.stretch
                a = (p.x - ux * half, p.y - uy * half)
                b = (p.x + ux * half, p.y + uy * half)
                pygame.draw.line(
                    layer,
                    color,
                    (int(a[0]), int(a[1])),
                    (int(b[0]), int(b[1])),
                    max(1, r),
                )
            else:
                pygame.draw.circle(layer, color, (int(p.x), int(p.y)), r)
        surf.blit(layer, (0, 0))

    def clear(self) -> None:
        """Drop every particle (stage reload)."""
        self.particles.clear()
