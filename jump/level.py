"""Level obstacles, portals, and a multi-gamemode course."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pygame

import config as c

ObstacleKind = Literal["spike", "block"]
Gamemode = Literal["cube", "ship", "ball", "ufo"]


@dataclass(slots=True)
class Obstacle:
    """A world-space hazard or platform."""

    kind: ObstacleKind
    x: float
    y: float
    w: float
    h: float

    def screen_rect(self, camera_x: float) -> pygame.Rect:
        """Return the axis-aligned rect in screen space."""
        return pygame.Rect(
            int(self.x - camera_x),
            int(self.y),
            int(self.w),
            int(self.h),
        )


@dataclass(slots=True)
class Portal:
    """World-space gamemode switch."""

    x: float
    mode: Gamemode
    triggered: bool = False

    def screen_x(self, camera_x: float) -> float:
        """Portal center X in screen space."""
        return self.x - camera_x


def build_level() -> tuple[list[Obstacle], list[Portal], float]:
    """Build cube → ship → ball → ufo → cube finish."""
    objs: list[Obstacle] = []
    portals: list[Portal] = []
    g = c.GROUND_Y
    s = c.CUBE_SIZE

    def spike(wx: float, *, tall: float = 28.0, top: float | None = None) -> None:
        if top is None:
            objs.append(Obstacle("spike", wx, g - tall, 28.0, tall))
        else:
            objs.append(Obstacle("spike", wx, top, 28.0, tall))

    def block(wx: float, wy: float, w: float = s, h: float = s) -> None:
        objs.append(Obstacle("block", wx, wy, w, h))

    def portal(wx: float, mode: Gamemode) -> None:
        portals.append(Portal(wx, mode))

    # ---- Cube (green) ----
    x = 520.0
    spike(x)
    x += 240
    spike(x)
    x += 200
    spike(x)
    spike(x + 42)
    x += 300
    block(x, g - s)
    block(x + s + 10, g - s * 2)
    spike(x + (s + 10) * 2 + 36)
    x += 380
    spike(x)
    block(x + 100, g - s * 2, w=s * 2)
    spike(x + 220)
    x += 380
    for i in range(4):
        spike(x + i * 75)
    x += 4 * 75 + 200

    # ---- Purple SHIP portal ----
    portal(x + 40, "ship")
    x += 200
    for i in range(4):
        block(x + i * 170, g - s * 3.0 - (i % 2) * 50, w=s * 1.3)
    x += 4 * 170 + 60
    for i in range(5):
        if i % 2 == 0:
            spike(x + i * 115, tall=34)
        else:
            spike(x + i * 115, tall=34, top=c.CEILING_Y)
    x += 5 * 115 + 160
    block(x, g - s * 4.2, w=s * 2)
    block(x + 150, g - s * 2.4, w=s * 2)
    x += 360

    # ---- Orange BALL portal ----
    portal(x + 20, "ball")
    x += 200
    spike(x)
    spike(x + 90)
    x += 280
    block(x, g - s * 2.5, w=s * 3)
    spike(x + s * 3 + 40)
    x += 320
    for i in range(4):
        spike(x + i * 100)
        if i % 2:
            spike(x + i * 100 + 40, tall=30, top=c.CEILING_Y)
    x += 4 * 100 + 180

    # ---- Yellow UFO portal ----
    portal(x + 20, "ufo")
    x += 200
    for i in range(5):
        block(x + i * 140, g - s * (2.0 + (i % 3) * 0.8), w=s)
    x += 5 * 140 + 100
    for i in range(6):
        spike(x + i * 85)
    x += 6 * 85 + 180

    # ---- Green CUBE portal → finish ----
    portal(x + 20, "cube")
    x += 180
    spike(x)
    spike(x + 48)
    x += 260
    for i in range(3):
        spike(x + i * 70)
    x += 3 * 70 + 200
    block(x, g - s, w=s * 4)
    finish_x = x + s * 4 + 80
    return objs, portals, finish_x


def draw_obstacle(surf: pygame.Surface, obs: Obstacle, camera_x: float) -> None:
    """Render a spike or block in screen space."""
    rect = obs.screen_rect(camera_x)
    if rect.right < -40 or rect.left > c.SCREEN_W + 40:
        return

    if obs.kind == "spike":
        points_up = rect.bottom >= c.GROUND_Y - 2
        if points_up:
            tip = (rect.centerx, rect.top)
            left = (rect.left, rect.bottom)
            right = (rect.right, rect.bottom)
        else:
            tip = (rect.centerx, rect.bottom)
            left = (rect.left, rect.top)
            right = (rect.right, rect.top)
        pygame.draw.polygon(surf, c.SPIKE, [tip, left, right])
        pygame.draw.polygon(surf, (255, 160, 180), [tip, left, right], width=2)
    else:
        pygame.draw.rect(surf, c.BLOCK, rect, border_radius=3)
        pygame.draw.rect(surf, c.BLOCK_EDGE, rect, width=2, border_radius=3)


def draw_portal(surf: pygame.Surface, portal: Portal, camera_x: float, pulse: float) -> None:
    """Draw a tall neon oval portal matching the reference chart."""
    sx = int(portal.screen_x(camera_x))
    if sx < -80 or sx > c.SCREEN_W + 80:
        return

    color = c.PORTAL_COLORS[portal.mode]
    cy = int((c.CEILING_Y + c.GROUND_Y) / 2)
    # Tall oval ring
    rw = 28 + int(2 * abs((pulse * 3) % 2 - 1))
    rh = 78
    oval = pygame.Rect(sx - rw, cy - rh, rw * 2, rh * 2)

    # Soft glow
    glow = pygame.Surface((rw * 2 + 20, rh * 2 + 20), pygame.SRCALPHA)
    pygame.draw.ellipse(glow, (*color, 55), glow.get_rect().inflate(-4, -4), width=10)
    surf.blit(glow, (oval.x - 10, oval.y - 10))

    # Outer neon ring
    pygame.draw.ellipse(surf, color, oval, width=6)
    # Inner dark chamber with grid
    inner = oval.inflate(-16, -20)
    pygame.draw.ellipse(surf, (12, 14, 22), inner)
    # White lattice
    for i in range(1, 4):
        y = inner.top + int(inner.h * i / 4)
        pygame.draw.line(surf, (220, 225, 240), (inner.left + 6, y), (inner.right - 6, y), 1)
    for i in range(1, 3):
        x = inner.left + int(inner.w * i / 3)
        pygame.draw.line(surf, (220, 225, 240), (x, inner.top + 8), (x, inner.bottom - 8), 1)
    pygame.draw.ellipse(surf, color, inner, width=2)

    # Corner orbs
    for px, py in (
        (sx, oval.top),
        (sx, oval.bottom),
        (oval.left, cy),
        (oval.right, cy),
    ):
        pygame.draw.circle(surf, color, (px, py), 5)
        pygame.draw.circle(surf, (255, 255, 255), (px, py), 2)

    font = pygame.font.SysFont("Arial", 13, bold=True)
    label = portal.mode.upper()
    text = font.render(label, True, color)
    surf.blit(text, text.get_rect(center=(sx, cy)))
