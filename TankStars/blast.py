"""Bomb blast particle animations for Tank Stars."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

import pygame

import config as c


@dataclass(slots=True)
class _Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    radius: float
    color: tuple[int, int, int]
    kind: str  # spark | smoke | debris | flash


@dataclass(slots=True)
class Blast:
    """One multi-layer explosion at a hit point."""

    x: float
    y: float
    age: float = 0.0
    duration: float = c.BLAST_DURATION
    power: float = 1.0  # scales radius / particle energy
    particles: list[_Particle] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Spawn rings of sparks, smoke, and dirt debris."""
        if self.particles:
            return
        p = max(0.5, self.power)
        # Core flash sparks
        for _ in range(int(c.BLAST_SPARK_COUNT * p)):
            ang = random.uniform(0, math.tau)
            spd = random.uniform(120, 420) * p
            life = random.uniform(0.25, 0.65)
            self.particles.append(
                _Particle(
                    self.x,
                    self.y,
                    math.cos(ang) * spd,
                    math.sin(ang) * spd - random.uniform(40, 160),
                    life,
                    life,
                    random.uniform(2.0, 5.0),
                    random.choice(
                        (
                            (255, 240, 120),
                            (255, 160, 40),
                            (255, 80, 30),
                            (255, 255, 200),
                        )
                    ),
                    "spark",
                )
            )
        # Rising smoke puffs
        for _ in range(int(c.BLAST_SMOKE_COUNT * p)):
            ang = random.uniform(-math.pi, 0)
            spd = random.uniform(30, 120) * p
            life = random.uniform(0.5, 1.1)
            shade = random.randint(70, 130)
            self.particles.append(
                _Particle(
                    self.x + random.uniform(-8, 8),
                    self.y + random.uniform(-6, 6),
                    math.cos(ang) * spd * 0.4,
                    -abs(math.sin(ang) * spd) - 20,
                    life,
                    life,
                    random.uniform(8.0, 18.0),
                    (shade, shade, shade),
                    "smoke",
                )
            )
        # Dirt / debris chunks
        for _ in range(int(c.BLAST_DEBRIS_COUNT * p)):
            ang = random.uniform(-math.pi * 0.9, -math.pi * 0.1)
            spd = random.uniform(80, 280) * p
            life = random.uniform(0.4, 0.9)
            self.particles.append(
                _Particle(
                    self.x,
                    self.y,
                    math.cos(ang) * spd,
                    math.sin(ang) * spd,
                    life,
                    life,
                    random.uniform(2.5, 6.0),
                    random.choice(
                        (
                            (90, 70, 40),
                            (120, 95, 55),
                            (70, 110, 50),
                            (55, 45, 30),
                        )
                    ),
                    "debris",
                )
            )
        # Brief white flash speck
        self.particles.append(
            _Particle(self.x, self.y, 0, 0, 0.12, 0.12, 22 * p, (255, 255, 240), "flash")
        )

    @property
    def alive(self) -> bool:
        """True while the blast is still animating."""
        return self.age < self.duration or any(p.life > 0 for p in self.particles)

    def update(self, dt: float) -> None:
        """Advance shockwave age and integrate particles."""
        self.age += dt
        alive: list[_Particle] = []
        for p in self.particles:
            p.life -= dt
            if p.life <= 0:
                continue
            if p.kind != "flash":
                damp = 0.5 if p.kind == "smoke" else 1.2
                p.vx *= max(0.0, 1.0 - damp * dt)
                p.vy *= max(0.0, 1.0 - damp * dt)
                if p.kind in ("spark", "debris"):
                    p.vy += c.GRAVITY * 0.65 * dt
                elif p.kind == "smoke":
                    p.vy -= 25.0 * dt  # buoyancy
                p.x += p.vx * dt
                p.y += p.vy * dt
            alive.append(p)
        self.particles = alive

    def draw(self, surf: pygame.Surface) -> None:
        """Draw expanding shock rings plus all particles."""
        t = min(1.0, self.age / self.duration)
        # Multi-layer shockwave rings
        layer = pygame.Surface((c.SCREEN_W, c.SCREEN_H), pygame.SRCALPHA)
        for i in range(c.BLAST_RING_COUNT):
            delay = i * 0.07
            local = max(0.0, min(1.0, (self.age - delay) / (self.duration * 0.7)))
            if local <= 0.0:
                continue
            radius = int((18 + i * 10) * self.power + local * (70 + i * 28) * self.power)
            alpha = int(220 * (1.0 - local) * (1.0 - i * 0.12))
            if alpha <= 0:
                continue
            color = (255, 180 - i * 30, 40, alpha)
            pygame.draw.circle(layer, color, (int(self.x), int(self.y)), radius, 3)
            # Inner fill pulse on first ring
            if i == 0 and local < 0.35:
                fill_a = int(160 * (1.0 - local / 0.35))
                pygame.draw.circle(
                    layer,
                    (255, 220, 80, fill_a),
                    (int(self.x), int(self.y)),
                    max(4, radius // 2),
                )

        for p in self.particles:
            frac = max(0.0, p.life / p.max_life)
            if p.kind == "flash":
                alpha = int(255 * frac)
                pygame.draw.circle(
                    layer,
                    (*p.color, alpha),
                    (int(p.x), int(p.y)),
                    int(p.radius * (1.2 - frac * 0.4)),
                )
            elif p.kind == "smoke":
                alpha = int(140 * frac)
                r = int(p.radius * (1.4 - frac * 0.4))
                pygame.draw.circle(layer, (*p.color, alpha), (int(p.x), int(p.y)), r)
            elif p.kind == "spark":
                alpha = int(255 * frac)
                # Streak along velocity
                spd = math.hypot(p.vx, p.vy) or 1.0
                ux, uy = p.vx / spd, p.vy / spd
                length = 4 + 10 * frac
                a = (p.x - ux * length, p.y - uy * length)
                b = (p.x + ux * length * 0.4, p.y + uy * length * 0.4)
                pygame.draw.line(
                    layer,
                    (*p.color, alpha),
                    (int(a[0]), int(a[1])),
                    (int(b[0]), int(b[1])),
                    max(1, int(p.radius)),
                )
            else:  # debris
                alpha = int(230 * frac)
                pygame.draw.circle(
                    layer, (*p.color, alpha), (int(p.x), int(p.y)), max(1, int(p.radius))
                )

        surf.blit(layer, (0, 0))
        # Soft screen vignette flash at the very start
        if t < 0.15:
            flash = pygame.Surface((c.SCREEN_W, c.SCREEN_H), pygame.SRCALPHA)
            flash.fill((255, 200, 100, int(50 * (1.0 - t / 0.15))))
            surf.blit(flash, (0, 0))


class BlastSystem:
    """Owns all active bomb blasts."""

    def __init__(self) -> None:
        self.blasts: list[Blast] = []

    def spawn(self, x: float, y: float, *, power: float = 1.0) -> None:
        """Start a new multi-layer explosion."""
        self.blasts.append(Blast(x=x, y=y, power=power))

    def update(self, dt: float) -> None:
        for b in self.blasts:
            b.update(dt)
        self.blasts = [b for b in self.blasts if b.alive]

    def draw(self, surf: pygame.Surface) -> None:
        for b in self.blasts:
            b.draw(surf)

    def clear(self) -> None:
        self.blasts.clear()
