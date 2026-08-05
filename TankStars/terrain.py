"""Destructible heightmap terrain for Tank Stars."""

from __future__ import annotations

import math
import random

import pygame

import config as c


class Terrain:
    """1D height field that can be cratered by explosions."""

    def __init__(self, stage: int, seed: int | None = None) -> None:
        """Generate rolling hills; later stages get steeper valleys."""
        self.width = c.SCREEN_W
        self.heights = [float(c.SCREEN_H - 120)] * self.width
        rng = random.Random(seed if seed is not None else 1000 + stage)
        roughness = 0.55 + stage * 0.03
        base = c.SCREEN_H - 140 - min(40, stage * 1.5)
        # Sum of sines for classic artillery hills.
        waves = [
            (rng.uniform(0.004, 0.009), rng.uniform(28, 55 + stage), rng.random() * math.tau),
            (rng.uniform(0.012, 0.022), rng.uniform(12, 28), rng.random() * math.tau),
            (rng.uniform(0.03, 0.05), rng.uniform(4, 12) * roughness, rng.random() * math.tau),
        ]
        for x in range(self.width):
            y = base
            for freq, amp, phase in waves:
                y += math.sin(x * freq + phase) * amp
            # Soft walls near edges so tanks stay on-screen.
            edge = min(x, self.width - 1 - x)
            if edge < 50:
                y -= (50 - edge) * 0.9
            self.heights[x] = max(180.0, min(float(c.SCREEN_H - 40), y))

        self._surface = pygame.Surface((c.SCREEN_W, c.SCREEN_H), pygame.SRCALPHA)
        self._dirty = True

    def height_at(self, x: float) -> float:
        """Surface Y at horizontal ``x`` (clamped)."""
        xi = int(max(0, min(self.width - 1, round(x))))
        return self.heights[xi]

    def surface_normal_angle(self, x: float) -> float:
        """Approximate ground slope angle in radians (for tank tilt)."""
        x0 = max(0, min(self.width - 2, int(x)))
        dy = self.heights[x0 + 1] - self.heights[x0]
        return math.atan2(dy, 1.0)

    def carve_crater(self, cx: float, cy: float, radius: float) -> None:
        """Remove a circular bite from the heightmap around ``(cx, cy)``."""
        r = int(radius)
        x0 = max(0, int(cx) - r - 2)
        x1 = min(self.width - 1, int(cx) + r + 2)
        for x in range(x0, x1 + 1):
            dx = x - cx
            # Only carve where the explosion reaches below current surface.
            under = math.sqrt(max(0.0, radius * radius - dx * dx))
            crater_y = cy + under * 0.35  # mostly dig downward
            # Also lower surface if blast is near the top of the dirt.
            if abs(cy - self.heights[x]) < radius * 1.2 or cy >= self.heights[x] - 8:
                target = max(self.heights[x], crater_y)
                # Dig: increase Y (down the screen).
                dig = self.heights[x] + (radius - abs(dx)) * 0.55
                self.heights[x] = min(float(c.SCREEN_H - 30), max(target, dig))
                self.heights[x] = min(self.heights[x], float(c.SCREEN_H - 28))
        self._dirty = True

    def collides(self, x: float, y: float) -> bool:
        """True if point is underground."""
        return y >= self.height_at(x)

    def _rebuild_surface(self) -> None:
        self._surface.fill((0, 0, 0, 0))
        # Fill dirt columns.
        for x in range(self.width):
            top = int(self.heights[x])
            pygame.draw.line(self._surface, c.GROUND_COLOR, (x, top), (x, c.SCREEN_H))
            pygame.draw.line(
                self._surface,
                c.GROUND_DARK,
                (x, top),
                (x, min(c.SCREEN_H, top + c.DIRT_LAYER)),
            )
        # Grass lip
        pts = [(0, c.SCREEN_H)]
        for x in range(0, self.width, 2):
            pts.append((x, int(self.heights[x])))
        pts.append((self.width - 1, int(self.heights[-1])))
        pts.append((c.SCREEN_W, c.SCREEN_H))
        # Outline
        for x in range(1, self.width):
            pygame.draw.line(
                self._surface,
                (90, 170, 70),
                (x - 1, int(self.heights[x - 1])),
                (x, int(self.heights[x])),
                2,
            )
        self._dirty = False

    def draw(self, surf: pygame.Surface) -> None:
        """Blit the cached terrain surface."""
        if self._dirty:
            self._rebuild_surface()
        surf.blit(self._surface, (0, 0))
