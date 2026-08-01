"""Stereo Madness — classic cube → ship → cube course."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pygame

import config as c

ObstacleKind = Literal["spike", "block"]
Gamemode = Literal["cube", "ship", "ball", "ufo"]
OrbKind = Literal["yellow", "pink", "blue"]

LEVEL_NAME: str = "Stereo Madness"


@dataclass(slots=True)
class Obstacle:
    """A world-space hazard or platform."""

    kind: ObstacleKind
    x: float
    y: float
    w: float
    h: float

    def screen_rect(self, camera_x: float) -> pygame.Rect:
        """Return the drawn rect in screen space."""
        return pygame.Rect(
            int(self.x - camera_x),
            int(self.y),
            int(self.w),
            int(self.h),
        )

    def hit_rect(self, camera_x: float) -> pygame.Rect:
        """Return a tighter collision rect than the drawn sprite."""
        rect = self.screen_rect(camera_x)
        if self.kind == "spike":
            inset = int(c.SPIKE_HIT_INSET)
            # Shrink toward the tip so grazing the wide base feels fair.
            points_up = rect.bottom >= c.GROUND_Y - 2
            if points_up:
                return pygame.Rect(
                    rect.left + inset,
                    rect.top + inset // 2,
                    max(4, rect.w - inset * 2),
                    max(4, rect.h - inset),
                )
            return pygame.Rect(
                rect.left + inset,
                rect.top,
                max(4, rect.w - inset * 2),
                max(4, rect.h - inset),
            )
        inset = int(c.BLOCK_HIT_INSET)
        return rect.inflate(-inset * 2, -inset * 2)


@dataclass(slots=True)
class Portal:
    """World-space gamemode switch."""

    x: float
    mode: Gamemode
    triggered: bool = False

    def screen_x(self, camera_x: float) -> float:
        """Portal center X in screen space."""
        return self.x - camera_x


@dataclass(slots=True)
class Orb:
    """Clickable jump orb (yellow / pink / blue)."""

    kind: OrbKind
    x: float  # world center X
    y: float  # world center Y
    used: bool = False

    def screen_center(self, camera_x: float) -> tuple[float, float]:
        """Return orb center in screen space."""
        return self.x - camera_x, self.y

    def hit_rect(self, camera_x: float) -> pygame.Rect:
        """Collision circle approximated as a square."""
        cx, cy = self.screen_center(camera_x)
        r = c.ORB_RADIUS
        return pygame.Rect(int(cx - r), int(cy - r), int(r * 2), int(r * 2))


def build_level() -> tuple[list[Obstacle], list[Portal], list[Orb], float]:
    """Build Stereo Madness with orbs: cube → ship → cube."""
    objs: list[Obstacle] = []
    portals: list[Portal] = []
    orbs: list[Orb] = []
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

    def orb(wx: float, wy: float, kind: OrbKind = "yellow") -> None:
        orbs.append(Orb(kind, wx, wy))

    def pad(amount: float) -> None:
        nonlocal x
        x += amount

    # =====================================================================
    # PART 1 — Cube intro
    # =====================================================================
    x = 480.0

    spike(x)
    pad(210)
    spike(x)
    pad(210)
    spike(x)
    pad(200)

    spike(x)
    spike(x + 38)
    pad(230)

    spike(x)
    pad(190)
    spike(x)
    spike(x + 38)
    pad(240)

    spike(x)
    spike(x + 38)
    spike(x + 76)
    pad(260)

    block(x, g - s)
    spike(x + s + 28)
    pad(220)

    block(x, g - s)
    block(x + s + 8, g - s * 2)
    pad(200)
    spike(x)
    pad(200)

    spike(x)
    block(x + 70, g - s * 2, w=s * 2.5)
    spike(x + 70 + s * 2.5 + 24)
    pad(280)

    for gap in (175, 175, 165, 185, 175):
        spike(x)
        pad(gap)
    pad(40)

    # Yellow orb chain over a wide gap
    spike(x)
    pad(90)
    orb(x + 20, g - s * 2.4, "yellow")
    pad(130)
    orb(x + 20, g - s * 2.8, "yellow")
    pad(140)
    spike(x)
    pad(200)

    block(x, g - s * 2)
    block(x + s + 8, g - s)
    pad(220)
    spike(x)
    spike(x + 40)
    pad(200)
    orb(x + 10, g - s * 2.2, "pink")
    pad(180)

    # =====================================================================
    # PART 2 — Purple SHIP
    # =====================================================================
    portal(x + 30, "ship")
    pad(220)

    for i in range(3):
        yy = g - s * (2.6 + (i % 2) * 1.1)
        block(x, yy, w=s * 1.5)
        pad(160)

    for i in range(8):
        if i % 2 == 0:
            spike(x, tall=32)
        else:
            spike(x, tall=32, top=c.CEILING_Y)
        pad(105)
    pad(40)

    # Ship yellow orbs for recovery kicks
    orb(x + 10, (c.CEILING_Y + g) / 2, "yellow")
    pad(160)

    for i in range(4):
        yy = c.CEILING_Y + 85 + (i % 2) * 70
        block(x, yy, w=22, h=22)
        pad(130)
    pad(40)

    spike(x, tall=30)
    pad(95)
    spike(x, tall=30, top=c.CEILING_Y)
    pad(95)
    spike(x, tall=30)
    pad(95)
    spike(x, tall=30, top=c.CEILING_Y)
    pad(140)

    block(x, g - s * 3.5, w=s * 2)
    pad(150)
    block(x, g - s * 2.2, w=s * 2)
    pad(180)

    # =====================================================================
    # PART 3 — Green CUBE finish
    # =====================================================================
    portal(x + 20, "cube")
    pad(200)

    spike(x)
    pad(170)
    spike(x)
    spike(x + 38)
    pad(220)

    block(x, g - s)
    block(x + s + 6, g - s * 2)
    block(x + (s + 6) * 2, g - s * 3)
    pad(240)
    spike(x)
    pad(160)
    orb(x + 15, g - s * 3.2, "yellow")
    pad(160)

    spike(x)
    block(x + 85, g - s * 2, w=s * 2)
    pad(200)
    spike(x)
    block(x + 85, g - s * 2.5, w=s * 2)
    pad(160)
    orb(x + 20, g - s * 3.0, "pink")
    pad(180)

    for i, gap in enumerate((150, 145, 140, 155, 140, 150)):
        spike(x)
        if i == 2:
            orb(x + gap * 0.45, g - s * 2.5, "yellow")
        pad(gap)

    spike(x)
    spike(x + 38)
    pad(120)
    orb(x + 30, g - s * 2.6, "blue")
    pad(200)

    block(x, g - s, w=s * 5)
    finish_x = x + s * 5 + 100
    return objs, portals, orbs, finish_x


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
    rw = 28 + int(2 * abs((pulse * 3) % 2 - 1))
    rh = 78
    oval = pygame.Rect(sx - rw, cy - rh, rw * 2, rh * 2)

    glow = pygame.Surface((rw * 2 + 20, rh * 2 + 20), pygame.SRCALPHA)
    pygame.draw.ellipse(glow, (*color, 55), glow.get_rect().inflate(-4, -4), width=10)
    surf.blit(glow, (oval.x - 10, oval.y - 10))

    pygame.draw.ellipse(surf, color, oval, width=6)
    inner = oval.inflate(-16, -20)
    pygame.draw.ellipse(surf, (12, 14, 22), inner)
    for i in range(1, 4):
        y = inner.top + int(inner.h * i / 4)
        pygame.draw.line(
            surf, (220, 225, 240), (inner.left + 6, y), (inner.right - 6, y), 1
        )
    for i in range(1, 3):
        px = inner.left + int(inner.w * i / 3)
        pygame.draw.line(
            surf, (220, 225, 240), (px, inner.top + 8), (px, inner.bottom - 8), 1
        )
    pygame.draw.ellipse(surf, color, inner, width=2)

    for px, py in (
        (sx, oval.top),
        (sx, oval.bottom),
        (oval.left, cy),
        (oval.right, cy),
    ):
        pygame.draw.circle(surf, color, (px, py), 5)
        pygame.draw.circle(surf, (255, 255, 255), (px, py), 2)

    font = pygame.font.SysFont("Arial", 13, bold=True)
    text = font.render(portal.mode.upper(), True, color)
    surf.blit(text, text.get_rect(center=(sx, cy)))


def draw_orb(surf: pygame.Surface, orb: Orb, camera_x: float, pulse: float) -> None:
    """Draw a glowing jump orb (faded once used)."""
    cx, cy = orb.screen_center(camera_x)
    if cx < -40 or cx > c.SCREEN_W + 40:
        return
    colors = {
        "yellow": c.ORB_YELLOW,
        "pink": c.ORB_PINK,
        "blue": c.ORB_BLUE,
    }
    color = colors[orb.kind]
    r = int(c.ORB_RADIUS + 2 * abs((pulse * 5) % 2 - 1))
    alpha = 70 if orb.used else 220
    layer = pygame.Surface((r * 2 + 8, r * 2 + 8), pygame.SRCALPHA)
    center = (r + 4, r + 4)
    pygame.draw.circle(layer, (*color, alpha // 3), center, r + 3)
    pygame.draw.circle(layer, (*color, alpha), center, r, width=4)
    pygame.draw.circle(layer, (255, 255, 255, alpha), center, max(3, r // 3))
    pygame.draw.circle(layer, (*color, alpha), center, max(5, r // 2), width=2)
    surf.blit(layer, (int(cx) - r - 4, int(cy) - r - 4))
