"""Generate original classic-palette block textures (not Mojang assets)."""

from __future__ import annotations

import random
from pathlib import Path

from PIL import Image, ImageDraw

from blocks import TEXTURE_DIR

SIZE = 16


def _noise_fill(
    draw: ImageDraw.ImageDraw,
    base: tuple[int, int, int],
    variance: int = 18,
    seed: int = 0,
) -> None:
    """Fill 16x16 with speckled classic-style pixels."""
    rng = random.Random(seed)
    for y in range(SIZE):
        for x in range(SIZE):
            d = rng.randint(-variance, variance)
            color = tuple(max(0, min(255, c + d)) for c in base)
            draw.point((x, y), fill=color)


def _save(name: str, img: Image.Image) -> None:
    TEXTURE_DIR.mkdir(parents=True, exist_ok=True)
    path = TEXTURE_DIR / name
    img.save(path)


def _make_solid(name: str, rgb: tuple[int, int, int], variance: int, seed: int) -> None:
    img = Image.new("RGB", (SIZE, SIZE))
    draw = ImageDraw.Draw(img)
    _noise_fill(draw, rgb, variance, seed)
    _save(name, img)


def ensure_textures() -> None:
    """Create textures/ PNGs if missing. Safe to call every launch."""
    TEXTURE_DIR.mkdir(parents=True, exist_ok=True)

    specs: list[tuple[str, tuple[int, int, int], int, int]] = [
        ("dirt.png", (134, 96, 67), 22, 11),
        ("stone.png", (128, 128, 128), 20, 22),
        ("sand.png", (218, 210, 158), 16, 33),
        ("leaves.png", (60, 140, 50), 28, 44),
        ("water.png", (55, 100, 200), 24, 55),
        ("bedrock.png", (40, 40, 40), 14, 66),
        ("planks.png", (170, 135, 80), 18, 77),
        ("wood.png", (110, 80, 45), 16, 88),
        ("wood_top.png", (160, 130, 80), 12, 89),
        ("grass_top.png", (90, 170, 55), 22, 100),
        ]

    for name, rgb, var, seed in specs:
        path = TEXTURE_DIR / name
        if path.exists():
            continue
        _make_solid(name, rgb, var, seed)

    # Grass side: dirt body + green top strip (classic look)
    grass_side = TEXTURE_DIR / "grass.png"
    if not grass_side.exists():
        img = Image.new("RGB", (SIZE, SIZE))
        draw = ImageDraw.Draw(img)
        _noise_fill(draw, (134, 96, 67), 22, 101)
        for y in range(3):
            for x in range(SIZE):
                d = random.Random(200 + x + y * 16).randint(-18, 18)
                g = tuple(max(0, min(255, c + d)) for c in (90, 170, 55))
                draw.point((x, y), fill=g)
        _save("grass.png", img)
