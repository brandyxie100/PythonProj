"""Particle and tween helpers for Blumgi Merge animations."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

import pygame

import config as c


@dataclass(slots=True)
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    radius: float
    color: tuple[int, int, int]
    kind: str = "spark"  # spark | star | coin | puff


@dataclass(slots=True)
class FloatingText:
    text: str
    x: float
    y: float
    life: float = 0.9
    max_life: float = 0.9
    color: tuple[int, int, int] = c.GOLD


@dataclass(slots=True)
class FXSystem:
    """Coins, merge stars, hit sparks, floating labels."""

    particles: list[Particle] = field(default_factory=list)
    texts: list[FloatingText] = field(default_factory=list)
    _font: pygame.font.Font | None = None

    def _ensure_font(self) -> pygame.font.Font:
        if self._font is None:
            self._font = pygame.font.SysFont("Arial", 20, bold=True)
        return self._font

    def burst(
        self,
        x: float,
        y: float,
        color: tuple[int, int, int],
        *,
        count: int = 18,
        kind: str = "spark",
    ) -> None:
        for _ in range(count):
            ang = random.uniform(0, math.tau)
            spd = random.uniform(60, 260)
            life = random.uniform(0.3, 0.7)
            self.particles.append(
                Particle(
                    x,
                    y,
                    math.cos(ang) * spd,
                    math.sin(ang) * spd - 40,
                    life,
                    life,
                    random.uniform(2.5, 6.0),
                    color,
                    kind,
                )
            )

    def merge_burst(self, x: float, y: float, color: tuple[int, int, int]) -> None:
        self.burst(x, y, color, count=22, kind="star")
        self.burst(x, y, (255, 255, 255), count=10, kind="spark")

    def coin_burst(self, x: float, y: float, amount: int) -> None:
        self.burst(x, y, c.GOLD, count=14, kind="coin")
        self.texts.append(FloatingText(f"+{amount}", x, y - 10, color=c.GOLD))

    def hit_flash(self, x: float, y: float) -> None:
        self.burst(x, y, (255, 80, 120), count=12, kind="puff")

    def update(self, dt: float) -> None:
        alive: list[Particle] = []
        for p in self.particles:
            p.life -= dt
            if p.life <= 0:
                continue
            p.vy += 420 * dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.vx *= 0.98
            alive.append(p)
        self.particles = alive
        texts: list[FloatingText] = []
        for t in self.texts:
            t.life -= dt
            if t.life <= 0:
                continue
            t.y -= 40 * dt
            texts.append(t)
        self.texts = texts

    def draw(self, surf: pygame.Surface) -> None:
        layer = pygame.Surface((c.SCREEN_W, c.SCREEN_H), pygame.SRCALPHA)
        for p in self.particles:
            a = int(255 * (p.life / p.max_life))
            r = max(1, int(p.radius * (0.5 + 0.5 * p.life / p.max_life)))
            if p.kind == "star":
                pts = []
                for i in range(5):
                    ang = -math.pi / 2 + i * 2 * math.pi / 5
                    pts.append((p.x + math.cos(ang) * r * 1.6, p.y + math.sin(ang) * r * 1.6))
                if len(pts) >= 3:
                    pygame.draw.polygon(layer, (*p.color, a), [(int(x), int(y)) for x, y in pts])
            else:
                pygame.draw.circle(layer, (*p.color, a), (int(p.x), int(p.y)), r)
        surf.blit(layer, (0, 0))
        font = self._ensure_font()
        for t in self.texts:
            a = int(255 * (t.life / t.max_life))
            img = font.render(t.text, True, t.color)
            img.set_alpha(a)
            surf.blit(img, img.get_rect(center=(int(t.x), int(t.y))))
