"""Procedural WWII aircraft and VFX drawing helpers."""

from __future__ import annotations

import math
import random

import pygame as pg

import config as cfg


def _poly(surface: pg.Surface, color: tuple[int, int, int], points: list[tuple[float, float]]) -> None:
    """Draw a filled polygon with integer points."""
    pg.draw.polygon(surface, color, [(int(x), int(y)) for x, y in points])


def draw_player_plane(
    surface: pg.Surface,
    x: float,
    y: float,
    *,
    prop_angle: float,
    looping: bool = False,
    flash: bool = False,
) -> pg.Rect:
    """Draw a US Navy Wildcat-style fighter (nose up = screen-up)."""
    scale = 1.15 if looping else 1.0
    body = cfg.PLAYER_BLUE if not flash else cfg.UI_WHITE
    dark = cfg.PLAYER_NAVY
    wing_span = 22 * scale
    length = 28 * scale

    # Wings
    _poly(
        surface,
        body,
        [
            (x - wing_span, y + 4 * scale),
            (x - 6 * scale, y - 2 * scale),
            (x + 6 * scale, y - 2 * scale),
            (x + wing_span, y + 4 * scale),
            (x + 10 * scale, y + 8 * scale),
            (x - 10 * scale, y + 8 * scale),
        ],
    )
    # Fuselage
    _poly(
        surface,
        dark,
        [
            (x - 5 * scale, y + 12 * scale),
            (x - 4 * scale, y - length * 0.55),
            (x + 4 * scale, y - length * 0.55),
            (x + 5 * scale, y + 12 * scale),
            (x, y + 16 * scale),
        ],
    )
    # Cockpit
    pg.draw.ellipse(
        surface,
        (40, 160, 200),
        pg.Rect(int(x - 3 * scale), int(y - 6 * scale), int(6 * scale), int(8 * scale)),
    )
    # Tail
    _poly(
        surface,
        body,
        [
            (x - 8 * scale, y + 14 * scale),
            (x, y + 8 * scale),
            (x + 8 * scale, y + 14 * scale),
            (x, y + 18 * scale),
        ],
    )
    # Propeller disc
    prop_r = 7 * scale
    for i in range(3):
        a = prop_angle + i * (math.pi * 2 / 3)
        x2 = x + math.cos(a) * prop_r
        y2 = y - length * 0.55 + math.sin(a) * prop_r * 0.35
        pg.draw.line(
            surface,
            (220, 220, 230),
            (int(x), int(y - length * 0.55)),
            (int(x2), int(y2)),
            2,
        )
    # Star roundel
    pg.draw.circle(surface, cfg.UI_WHITE, (int(x - 12 * scale), int(y + 3 * scale)), 3)
    pg.draw.circle(surface, cfg.UI_RED, (int(x - 12 * scale), int(y + 3 * scale)), 1)

    return pg.Rect(int(x - wing_span), int(y - length * 0.6), int(wing_span * 2), int(length * 1.2))


def draw_enemy_fighter(
    surface: pg.Surface,
    x: float,
    y: float,
    *,
    prop_angle: float,
    color: tuple[int, int, int] = cfg.ENEMY_OLIVE,
) -> pg.Rect:
    """Draw a Zero-style enemy fighter (nose toward player / down)."""
    dark = cfg.ENEMY_DARK
    wing = 18
    # Wings
    _poly(
        surface,
        color,
        [
            (x - wing, y - 2),
            (x - 5, y + 2),
            (x + 5, y + 2),
            (x + wing, y - 2),
            (x + 8, y - 6),
            (x - 8, y - 6),
        ],
    )
    # Fuselage
    _poly(
        surface,
        dark,
        [(x - 4, y - 10), (x - 3, y + 14), (x + 3, y + 14), (x + 4, y - 10), (x, y - 14)],
    )
    pg.draw.circle(surface, (30, 30, 30), (int(x), int(y + 2)), 3)
    # Rising sun disc
    pg.draw.circle(surface, cfg.UI_RED, (int(x + 10), int(y - 2)), 3)
    # Prop
    for i in range(2):
        a = prop_angle + i * math.pi
        pg.draw.line(
            surface,
            (200, 200, 200),
            (int(x), int(y + 14)),
            (int(x + math.cos(a) * 6), int(y + 14 + math.sin(a) * 2)),
            2,
        )
    return pg.Rect(int(x - wing), int(y - 14), wing * 2, 30)


def draw_enemy_bomber(surface: pg.Surface, x: float, y: float, *, prop_angle: float) -> pg.Rect:
    """Draw a twin-engine bomber silhouette."""
    color = (70, 85, 50)
    _poly(
        surface,
        color,
        [
            (x - 32, y),
            (x - 8, y + 6),
            (x + 8, y + 6),
            (x + 32, y),
            (x + 20, y - 8),
            (x - 20, y - 8),
        ],
    )
    _poly(
        surface,
        cfg.ENEMY_DARK,
        [(x - 6, y - 16), (x - 5, y + 18), (x + 5, y + 18), (x + 6, y - 16)],
    )
    for ox in (-18, 18):
        pg.draw.ellipse(surface, (40, 45, 30), pg.Rect(int(x + ox - 5), int(y - 4), 10, 8))
        pg.draw.line(
            surface,
            (180, 180, 180),
            (int(x + ox), int(y + 4)),
            (int(x + ox + math.cos(prop_angle) * 5), int(y + 4 + math.sin(prop_angle))),
            2,
        )
    return pg.Rect(int(x - 32), int(y - 16), 64, 36)


def draw_enemy_dive(surface: pg.Surface, x: float, y: float, *, tilt: float) -> pg.Rect:
    """Draw a dive bomber with fixed gear / dive brakes feel."""
    color = (100, 90, 40)
    ca, sa = math.cos(tilt), math.sin(tilt)
    pts = [(-16, -2), (16, -2), (10, 6), (-10, 6)]
    world = [(x + px * ca - py * sa, y + px * sa + py * ca) for px, py in pts]
    _poly(surface, color, world)
    fus = [(0, -12), (-3, 14), (3, 14)]
    world_f = [(x + px * ca - py * sa, y + px * sa + py * ca) for px, py in fus]
    _poly(surface, cfg.ENEMY_DARK, world_f)
    return pg.Rect(int(x - 18), int(y - 14), 36, 30)


def draw_gunboat(surface: pg.Surface, x: float, y: float) -> pg.Rect:
    """Draw a small coastal patrol craft (scrolls with ocean)."""
    hull = [(x - 28, y), (x + 28, y), (x + 20, y + 10), (x - 20, y + 10)]
    _poly(surface, (55, 65, 70), hull)
    pg.draw.rect(surface, (80, 85, 90), pg.Rect(int(x - 8), int(y - 8), 16, 10))
    pg.draw.rect(surface, (40, 40, 45), pg.Rect(int(x - 2), int(y - 14), 4, 8))
    return pg.Rect(int(x - 28), int(y - 14), 56, 26)


def draw_boss_carrier(
    surface: pg.Surface,
    x: float,
    y: float,
    *,
    hp_ratio: float,
    flash: bool = False,
) -> pg.Rect:
    """Draw a large flying fortress / airborne carrier boss."""
    color = cfg.UI_WHITE if flash else cfg.BOSS_STEEL
    dark = (50, 55, 60)
    w, h = 110, 70
    _poly(
        surface,
        color,
        [
            (x - w // 2, y),
            (x - w // 2 + 10, y - h // 2),
            (x + w // 2 - 10, y - h // 2),
            (x + w // 2, y),
            (x + w // 2 - 15, y + h // 2),
            (x - w // 2 + 15, y + h // 2),
        ],
    )
    pg.draw.rect(surface, dark, pg.Rect(int(x - 40), int(y - 8), 80, 12))
    # Engine pods
    for ox in (-40, -15, 15, 40):
        pg.draw.ellipse(surface, dark, pg.Rect(int(x + ox - 8), int(y + 8), 16, 12))
    # Damage streaks
    if hp_ratio < 0.5:
        for _ in range(3):
            sx = x + random.uniform(-40, 40)
            sy = y + random.uniform(-20, 20)
            pg.draw.circle(surface, (30, 30, 30), (int(sx), int(sy)), 4)
    return pg.Rect(int(x - w // 2), int(y - h // 2), w, h)


def draw_bullet(
    surface: pg.Surface,
    x: float,
    y: float,
    *,
    friendly: bool,
    kind: str = "normal",
) -> None:
    """Draw a projectile."""
    if friendly:
        if kind == "spread":
            pg.draw.circle(surface, cfg.UI_GOLD, (int(x), int(y)), 3)
        elif kind == "heavy":
            pg.draw.rect(surface, (255, 240, 120), pg.Rect(int(x - 2), int(y - 6), 4, 12))
        else:
            pg.draw.rect(surface, (255, 255, 200), pg.Rect(int(x - 1), int(y - 5), 2, 10))
    else:
        if kind == "aim":
            pg.draw.circle(surface, (255, 80, 60), (int(x), int(y)), 3)
        else:
            pg.draw.circle(surface, (255, 200, 80), (int(x), int(y)), 2)


def spawn_explosion_particles(
    x: float,
    y: float,
    count: int = 14,
) -> list[dict]:
    """Create particle dicts for an explosion burst."""
    particles: list[dict] = []
    for _ in range(count):
        ang = random.uniform(0, math.pi * 2)
        spd = random.uniform(40, 180)
        particles.append(
            {
                "x": x,
                "y": y,
                "vx": math.cos(ang) * spd,
                "vy": math.sin(ang) * spd,
                "life": random.uniform(0.25, 0.7),
                "max_life": 0.7,
                "r": random.randint(2, 5),
                "color": random.choice([cfg.EXPLOSION_ORANGE, cfg.EXPLOSION_YELLOW, cfg.UI_WHITE]),
            }
        )
    return particles
