"""Level obstacles, portals, and a cube→ship course."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pygame

import config as c

ObstacleKind = Literal["spike", "block"]
Gamemode = Literal["cube", "ship"]


@dataclass(slots=True)
class Obstacle:
    """A world-space hazard or platform."""

    kind: ObstacleKind
    x: float
    y: float  # top of the object
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
    """World-space gamemode switch (cube ↔ ship)."""

    x: float
    mode: Gamemode
    triggered: bool = False

    def screen_x(self, camera_x: float) -> float:
        """Portal center X in screen space."""
        return self.x - camera_x


def build_level() -> tuple[list[Obstacle], list[Portal], float]:
    """Build the course: cube section, ship flight, finish."""
    objs: list[Obstacle] = []
    portals: list[Portal] = []
    g = c.GROUND_Y
    s = c.CUBE_SIZE

    def spike(wx: float, *, tall: float = 28.0, top: float | None = None) -> None:
        """Ground spike, or ceiling spike when ``top`` is set."""
        if top is None:
            objs.append(Obstacle("spike", wx, g - tall, 28.0, tall))
        else:
            # Point downward from the ceiling band.
            objs.append(Obstacle("spike", wx, top, 28.0, tall))

    def block(wx: float, wy: float, w: float = s, h: float = s) -> None:
        objs.append(Obstacle("block", wx, wy, w, h))

    def portal(wx: float, mode: Gamemode) -> None:
        portals.append(Portal(wx, mode))

    # ---- Cube section (2-block jumps) ----
    x = 520.0
    spike(x)
    x += 240
    spike(x)
    x += 200
    spike(x)
    spike(x + 42)

    # Two-block stair (matches new jump height).
    x += 300
    block(x, g - s)
    block(x + s + 10, g - s * 2)
    spike(x + (s + 10) * 2 + 36)
    x += 380

    # Double-height gap hop onto a 2-block platform.
    spike(x)
    block(x + 100, g - s * 2, w=s * 2)
    spike(x + 220)
    x += 400

    for i in range(5):
        spike(x + i * 75)
    x += 5 * 75 + 220

    # Stack you can clear with a 2-block jump.
    block(x, g - s)
    block(x, g - s * 2)
    spike(x + s + 30)
    x += 340

    # ---- Enter ship ----
    portal(x + 40, "ship")
    x += 200

    # Ship corridor — floating hazards between floor and ceiling.
    for i in range(4):
        block(x + i * 180, g - s * 3.2 - (i % 2) * 40, w=s * 1.4)
    x += 4 * 180 + 40

    # Mid-height spike pillars (as short blocks + spikes).
    for i in range(5):
        yy = c.CEILING_Y + 70 + (i % 3) * 55
        block(x + i * 150, yy, w=26, h=26)
    x += 5 * 150 + 80

    # Wave of ground + ceiling spikes for ship weaving.
    for i in range(6):
        if i % 2 == 0:
            spike(x + i * 110, tall=34)
        else:
            spike(x + i * 110, tall=34, top=c.CEILING_Y)
    x += 6 * 110 + 160

    # Floating platforms to weave through.
    block(x, g - s * 4.5, w=s * 2)
    block(x + 140, g - s * 2.2, w=s * 2)
    block(x + 280, g - s * 3.8, w=s * 2)
    x += 420

    # ---- Back to cube for the finish ----
    portal(x + 20, "cube")
    x += 180
    spike(x)
    spike(x + 50)
    x += 240
    for i in range(4):
        spike(x + i * 70)
    x += 4 * 70 + 200

    block(x, g - s, w=s * 4)
    finish_x = x + s * 4 + 80
    return objs, portals, finish_x


def draw_obstacle(surf: pygame.Surface, obs: Obstacle, camera_x: float) -> None:
    """Render a spike or block in screen space."""
    rect = obs.screen_rect(camera_x)
    if rect.right < -40 or rect.left > c.SCREEN_W + 40:
        return

    if obs.kind == "spike":
        # Spikes near the ceiling point downward.
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
        inset = rect.inflate(-8, -8)
        if inset.w > 4 and inset.h > 4:
            pygame.draw.line(
                surf,
                c.BLOCK_EDGE,
                (inset.left, inset.centery),
                (inset.right, inset.centery),
                1,
            )
            pygame.draw.line(
                surf,
                c.BLOCK_EDGE,
                (inset.centerx, inset.top),
                (inset.centerx, inset.bottom),
                1,
            )


def draw_portal(surf: pygame.Surface, portal: Portal, camera_x: float, pulse: float) -> None:
    """Draw a glowing mode portal ring."""
    sx = int(portal.screen_x(camera_x))
    if sx < -60 or sx > c.SCREEN_W + 60:
        return
    color = c.PORTAL_SHIP if portal.mode == "ship" else c.PORTAL_CUBE
    cy = int((c.CEILING_Y + c.GROUND_Y) / 2)
    radius = 34 + int(3 * abs((pulse * 4) % 2 - 1))
    pygame.draw.circle(surf, color, (sx, cy), radius, width=5)
    pygame.draw.circle(surf, (*color, ), (sx, cy), radius - 10, width=2)
    label = "SHIP" if portal.mode == "ship" else "CUBE"
    font = pygame.font.SysFont("Arial", 14, bold=True)
    text = font.render(label, True, color)
    surf.blit(text, text.get_rect(center=(sx, cy)))
