"""Vivid animated slime units and sprite loading."""

from __future__ import annotations

import math
from pathlib import Path

import pygame

import config as c

_ASSETS = Path(__file__).resolve().parent / "assets"
_CACHE: dict[tuple[int, int], pygame.Surface] = {}
_BASE_SHEETS: list[pygame.Surface] = []


def _load_base_sheets() -> None:
    """Load CC0 OpenGameArt slime sheets once (recolored per tier)."""
    global _BASE_SHEETS
    if _BASE_SHEETS:
        return
    folder = _ASSETS / "slime_oga" / "png" / "48x64" / "thin_outline"
    order = (
        "slime_green.png",
        "slime_lightblue.png",
        "slime_violet.png",
        "slime_yellow.png",
        "slime_blue.png",
        "slime_brown.png",
        "slime_red.png",
        "slime_black.png",
    )
    for name in order:
        path = folder / name
        if path.exists():
            img = pygame.image.load(str(path))
            try:
                img = img.convert_alpha()
            except pygame.error:
                tmp = pygame.Surface(img.get_size(), pygame.SRCALPHA)
                tmp.blit(img, (0, 0))
                img = tmp
            _BASE_SHEETS.append(img)
    if not _BASE_SHEETS:
        s = pygame.Surface((48, 64), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (120, 255, 120), (4, 20, 40, 36))
        _BASE_SHEETS.append(s)


def _recolor(src: pygame.Surface, color: tuple[int, int, int]) -> pygame.Surface:
    """Fast tint using a multiply overlay while keeping alpha."""
    out = src.copy()
    tint = pygame.Surface(out.get_size(), pygame.SRCALPHA)
    tint.fill((*color, 255))
    # Multiply color into RGB, keep original alpha
    colored = out.copy()
    colored.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    # Softly restore highlights
    highlight = out.copy()
    highlight.fill((255, 255, 255, 60), special_flags=pygame.BLEND_RGBA_ADD)
    colored.blit(highlight, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
    # Re-apply original alpha mask
    colored.blit(out, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    return colored


def slime_sprite(tier: int, size: int = 72) -> pygame.Surface:
    """Return a cached vivid slime surface for ``tier`` (1..MAX)."""
    tier = max(1, min(c.MAX_TIER, tier))
    key = (tier, size)
    if key in _CACHE:
        return _CACHE[key]
    _load_base_sheets()
    base = _BASE_SHEETS[(tier - 1) % len(_BASE_SHEETS)]
    tinted = _recolor(base, c.TIER_COLORS[tier - 1])
    canvas = pygame.Surface((64, 72), pygame.SRCALPHA)
    canvas.blit(tinted, (8, 4))
    _draw_weapon(canvas, tier)
    # Extra vivid body glow ellipse behind sprite
    glow = pygame.Surface((64, 72), pygame.SRCALPHA)
    pygame.draw.ellipse(glow, (*c.TIER_COLORS[tier - 1], 70), (6, 22, 52, 44))
    glow.blit(canvas, (0, 0))
    scaled = pygame.transform.smoothscale(glow, (size, int(size * 1.15)))
    _CACHE[key] = scaled
    return scaled


def _draw_weapon(surf: pygame.Surface, tier: int) -> None:
    """Simple weapon silhouette that upgrades with tier."""
    color = (255, 255, 255)
    if tier <= 2:
        return
    if tier <= 4:
        pygame.draw.line(surf, color, (44, 40), (58, 22), 3)
        pygame.draw.circle(surf, c.TIER_COLORS[tier - 1], (58, 22), 4)
    elif tier <= 6:
        pygame.draw.polygon(surf, color, [(42, 38), (60, 18), (56, 42)])
    elif tier <= 8:
        pygame.draw.rect(surf, color, (46, 18, 6, 28), border_radius=2)
        pygame.draw.polygon(surf, (255, 80, 80), [(44, 18), (54, 8), (54, 18)])
    else:
        pygame.draw.polygon(
            surf,
            (255, 220, 60),
            [(18, 22), (24, 10), (32, 20), (40, 8), (46, 22)],
        )


class Slime:
    """A board unit with idle bounce / squash animation state."""

    __slots__ = ("tier", "phase", "merge_flash", "hurt", "attack_t")

    def __init__(self, tier: int = 1) -> None:
        self.tier = max(1, min(c.MAX_TIER, tier))
        self.phase = 0.0
        self.merge_flash = 0.0
        self.hurt = 0.0
        self.attack_t = 0.0

    @property
    def color(self) -> tuple[int, int, int]:
        return c.TIER_COLORS[self.tier - 1]

    @property
    def name(self) -> str:
        return c.TIER_NAMES[self.tier - 1]

    @property
    def dps(self) -> int:
        return c.TIER_DPS[self.tier - 1]

    @property
    def hp(self) -> int:
        return c.TIER_HP[self.tier - 1]

    def update(self, dt: float) -> None:
        self.phase += dt * 4.5
        self.merge_flash = max(0.0, self.merge_flash - dt)
        self.hurt = max(0.0, self.hurt - dt)
        self.attack_t = max(0.0, self.attack_t - dt)

    def draw(self, surf: pygame.Surface, cx: float, cy: float, *, scale: float = 1.0) -> None:
        """Draw with bounce squash and flash overlays."""
        bounce = math.sin(self.phase) * 4.0
        squash = 1.0 + math.sin(self.phase * 2) * 0.06
        if self.merge_flash > 0:
            squash += self.merge_flash * 0.5
        if self.attack_t > 0:
            bounce -= 8 * (self.attack_t / 0.25)
        size = int(c.CELL * 0.72 * scale * squash)
        sprite = slime_sprite(self.tier, max(24, size))
        if self.hurt > 0:
            flash = sprite.copy()
            flash.fill((255, 60, 80, 90), special_flags=pygame.BLEND_RGBA_ADD)
            sprite = flash
        if self.merge_flash > 0:
            glow = sprite.copy()
            glow.fill((255, 255, 180, 100), special_flags=pygame.BLEND_RGBA_ADD)
            sprite = glow
        rect = sprite.get_rect(center=(int(cx), int(cy + bounce)))
        surf.blit(sprite, rect)
        font = pygame.font.SysFont("Arial", 14, bold=True)
        label = font.render(str(self.tier), True, (20, 10, 40))
        surf.blit(label, label.get_rect(center=(int(cx), int(cy + size * 0.42))))
