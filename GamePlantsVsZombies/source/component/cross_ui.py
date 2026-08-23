"""Generate original Cross-Breeds–inspired UI art (no third-party IP)."""

from __future__ import annotations

import math
from pathlib import Path

import pygame as pg


def _helix(
    surf: pg.Surface,
    cx: int,
    cy: int,
    w: int,
    h: int,
    color_a: tuple[int, int, int],
    color_b: tuple[int, int, int],
) -> None:
    steps = 28
    for i in range(steps):
        t = i / max(1, steps - 1)
        y = int(cy - h / 2 + t * h)
        phase = t * math.pi * 3
        x1 = int(cx + math.sin(phase) * w)
        x2 = int(cx - math.sin(phase) * w)
        pg.draw.circle(surf, color_a, (x1, y), 4)
        pg.draw.circle(surf, color_b, (x2, y), 4)
        if i % 2 == 0:
            pg.draw.line(surf, (255, 230, 120), (x1, y), (x2, y), 2)


def build_cross_button() -> pg.Surface:
    """Green-gold lab button with a DNA helix."""
    surf = pg.Surface((300, 92), pg.SRCALPHA)
    pg.draw.rect(surf, (18, 70, 36), (0, 0, 300, 92), border_radius=16)
    pg.draw.rect(surf, (255, 210, 70), (0, 0, 300, 92), 3, border_radius=16)
    pg.draw.rect(surf, (28, 110, 52), (8, 8, 284, 76), border_radius=12)
    _helix(surf, 42, 46, 14, 58, (80, 255, 160), (255, 90, 140))
    font = pg.font.SysFont(None, 36, bold=True)
    title = font.render("CROSS-BREEDS", True, (255, 230, 90))
    surf.blit(title, (70, 18))
    small = pg.font.SysFont(None, 20)
    hint = small.render("Fuse  ·  Evolve  ·  Hybridize", True, (220, 255, 210))
    surf.blit(hint, (72, 54))
    return surf


def build_cross_banner() -> pg.Surface:
    """Wide lawn banner for Cross mode."""
    surf = pg.Surface((520, 36), pg.SRCALPHA)
    pg.draw.rect(surf, (12, 40, 22, 200), (0, 0, 520, 36), border_radius=8)
    pg.draw.rect(surf, (255, 200, 60), (0, 0, 520, 36), 2, border_radius=8)
    _helix(surf, 22, 18, 8, 26, (90, 255, 170), (255, 110, 150))
    font = pg.font.SysFont(None, 22)
    txt = font.render(
        "Drop on any plant to fuse traits or evolve  (power > 2x)",
        True,
        (255, 240, 180),
    )
    surf.blit(txt, (44, 8))
    return surf


def build_dna_badge() -> pg.Surface:
    """Small star/DNA pip for evolved plants."""
    surf = pg.Surface((28, 22), pg.SRCALPHA)
    pg.draw.ellipse(surf, (30, 90, 40, 220), (0, 0, 28, 22))
    pg.draw.ellipse(surf, (255, 210, 70), (0, 0, 28, 22), 1)
    _helix(surf, 14, 11, 7, 16, (120, 255, 180), (255, 140, 80))
    return surf


def build_fusion_glow() -> pg.Surface:
    """Soft gold burst behind fuse toasts."""
    surf = pg.Surface((64, 64), pg.SRCALPHA)
    cx, cy = 32, 32
    for r, a in ((30, 40), (22, 80), (14, 140), (8, 200)):
        s = pg.Surface((64, 64), pg.SRCALPHA)
        pg.draw.circle(s, (255, 210, 70, a), (cx, cy), r)
        surf.blit(s, (0, 0))
    return surf


def generate_and_save(out_dir: Path) -> dict[str, Path]:
    """Write PNGs under resources/graphics/Screen/."""
    if not pg.get_init():
        pg.init()
    if pg.font.get_init() is False:
        pg.font.init()
    out_dir.mkdir(parents=True, exist_ok=True)
    mapping = {
        "CrossButton.png": build_cross_button(),
        "CrossBanner.png": build_cross_banner(),
        "DnaBadge.png": build_dna_badge(),
        "FusionGlow.png": build_fusion_glow(),
    }
    paths = {}
    for name, surf in mapping.items():
        path = out_dir / name
        pg.image.save(surf, str(path))
        paths[name] = path
    return paths


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    dest = root / "resources" / "graphics" / "Screen"
    generate_and_save(dest)
    print("wrote", dest)
