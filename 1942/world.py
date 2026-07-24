"""Scrolling Midway Atoll ocean backdrop."""

from __future__ import annotations

import math
import random

import pygame as pg

import config as cfg


class OceanWorld:
    """Vertically scrolling Pacific ocean with atoll islands and haze."""

    def __init__(self) -> None:
        """Seed decorative islands and wake lines."""
        self.offset: float = 0.0
        self.speed: float = cfg.OCEAN_SCROLL_BASE
        self.islands: list[dict] = []
        self.waves: list[dict] = []
        self.clouds: list[dict] = []
        self._seed_decor()

    def _seed_decor(self) -> None:
        """Create looping decorative elements."""
        rng = random.Random(1942)
        for i in range(8):
            self.islands.append(
                {
                    "x": rng.randint(40, cfg.SCREEN_W - 40),
                    "y": rng.uniform(0, cfg.SCREEN_H * 2),
                    "r": rng.randint(18, 55),
                    "kind": rng.choice(["sand", "green", "reef"]),
                }
            )
        for i in range(30):
            self.waves.append(
                {
                    "x": rng.randint(0, cfg.SCREEN_W),
                    "y": rng.uniform(0, cfg.SCREEN_H),
                    "w": rng.randint(12, 40),
                }
            )
        for i in range(6):
            self.clouds.append(
                {
                    "x": rng.randint(0, cfg.SCREEN_W),
                    "y": rng.uniform(0, cfg.SCREEN_H),
                    "s": rng.uniform(0.6, 1.4),
                    "a": rng.randint(30, 70),
                }
            )

    def set_speed(self, speed: float) -> None:
        """Adjust scroll rate for mission intensity."""
        self.speed = speed

    def update(self, dt: float) -> None:
        """Advance scroll offsets."""
        self.offset = (self.offset + self.speed * dt) % (cfg.SCREEN_H * 2)
        for wave in self.waves:
            wave["y"] = (wave["y"] + self.speed * dt) % cfg.SCREEN_H
        for island in self.islands:
            island["y"] = (island["y"] + self.speed * dt) % (cfg.SCREEN_H * 2)
        for cloud in self.clouds:
            cloud["y"] = (cloud["y"] + cfg.CLOUD_SCROLL * dt) % cfg.SCREEN_H

    def draw(self, surface: pg.Surface) -> None:
        """Paint ocean gradient, islands, foam, and clouds."""
        # Vertical ocean bands for depth
        for i in range(12):
            t = i / 12
            shade = (
                int(cfg.OCEAN_DEEP[0] + (cfg.OCEAN_MID[0] - cfg.OCEAN_DEEP[0]) * t),
                int(cfg.OCEAN_DEEP[1] + (cfg.OCEAN_MID[1] - cfg.OCEAN_DEEP[1]) * t),
                int(cfg.OCEAN_DEEP[2] + (cfg.OCEAN_MID[2] - cfg.OCEAN_DEEP[2]) * t),
            )
            y0 = int(i * cfg.SCREEN_H / 12)
            y1 = int((i + 1) * cfg.SCREEN_H / 12)
            pg.draw.rect(surface, shade, pg.Rect(0, y0, cfg.SCREEN_W, y1 - y0))

        # Soft horizontal shimmer tied to scroll
        shimmer_y = int((-self.offset * 0.5) % 40)
        for y in range(shimmer_y, cfg.SCREEN_H, 40):
            pg.draw.line(surface, cfg.OCEAN_FOAM, (0, y), (cfg.SCREEN_W, y), 1)

        for wave in self.waves:
            pg.draw.arc(
                surface,
                cfg.OCEAN_FOAM,
                pg.Rect(int(wave["x"]), int(wave["y"]), wave["w"], 8),
                0.2,
                math.pi - 0.2,
                1,
            )

        for island in self.islands:
            iy = island["y"] % (cfg.SCREEN_H + 120) - 60
            if iy < -80 or iy > cfg.SCREEN_H + 80:
                continue
            r = island["r"]
            if island["kind"] == "reef":
                pg.draw.ellipse(
                    surface,
                    (40, 130, 140),
                    pg.Rect(int(island["x"] - r), int(iy - r * 0.4), r * 2, int(r * 0.8)),
                )
            else:
                pg.draw.ellipse(
                    surface,
                    cfg.SAND,
                    pg.Rect(int(island["x"] - r), int(iy - r * 0.45), r * 2, int(r * 0.9)),
                )
                if island["kind"] == "green":
                    pg.draw.ellipse(
                        surface,
                        cfg.ATOLL_GREEN,
                        pg.Rect(
                            int(island["x"] - r * 0.6),
                            int(iy - r * 0.25),
                            int(r * 1.2),
                            int(r * 0.5),
                        ),
                    )

        # Distant haze strip (carrier task force silhouette hint)
        pg.draw.rect(surface, cfg.SKY_HAZE, pg.Rect(0, 0, cfg.SCREEN_W, 28))

        for cloud in self.clouds:
            self._draw_cloud(surface, cloud)

    def _draw_cloud(self, surface: pg.Surface, cloud: dict) -> None:
        """Soft cloud puffs using translucent circles."""
        layer = pg.Surface((90, 40), pg.SRCALPHA)
        a = cloud["a"]
        s = cloud["s"]
        for ox, oy, rad in ((20, 18, 14), (40, 14, 16), (60, 18, 12), (35, 22, 10)):
            pg.draw.circle(layer, (255, 255, 255, a), (int(ox * s), int(oy * s)), int(rad * s))
        surface.blit(layer, (int(cloud["x"] - 40), int(cloud["y"])))
