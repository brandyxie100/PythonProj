"""Auto-battler wave fights between slime army and dungeon foes."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

import pygame

import config as c
from config import StageSpec
from fx import FXSystem
from slime import Slime, slime_sprite


@dataclass
class Battle:
    """Realtime auto-fight for one dungeon floor."""

    stage: StageSpec
    army: list[Slime]
    fx: FXSystem
    player_hp: float = 0.0
    enemy_hp: float = 0.0
    enemy_max: float = 0.0
    player_max: float = 0.0
    timer: float = 0.0
    done: bool = False
    won: bool = False
    reward: int = 0
    _atk_cd: float = 0.0
    _enemy_cd: float = 0.0
    _shake: float = 0.0
    _enemy_phase: float = 0.0
    _spawn_puffs: list[tuple[float, float, float]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.player_max = float(sum(s.hp for s in self.army) or 1)
        self.player_hp = self.player_max
        self.enemy_max = float(self.stage.enemy_hp)
        self.enemy_hp = self.enemy_max
        self.reward = self.stage.reward
        self._atk_cd = 0.35
        self._enemy_cd = 0.55

    @property
    def player_dps(self) -> float:
        return float(sum(s.dps for s in self.army))

    def update(self, dt: float) -> None:
        if self.done:
            return
        self.timer += dt
        self._enemy_phase += dt * 3.0
        self._shake = max(0.0, self._shake - dt)
        self._atk_cd -= dt
        self._enemy_cd -= dt

        if self._atk_cd <= 0 and self.army:
            self._atk_cd = 0.45
            dmg = self.player_dps * 0.45
            self.enemy_hp = max(0.0, self.enemy_hp - dmg)
            # Animate a random slime attacking
            s = random.choice(self.army)
            s.attack_t = 0.25
            self.fx.hit_flash(700 + random.uniform(-20, 20), 300)
            self._shake = 0.12
            if self.enemy_hp <= 0:
                self.done = True
                self.won = True
                return

        if self._enemy_cd <= 0:
            self._enemy_cd = 0.7
            dmg = self.stage.enemy_dps * 0.5
            self.player_hp = max(0.0, self.player_hp - dmg)
            if self.army:
                random.choice(self.army).hurt = 0.2
            self.fx.hit_flash(260, 320)
            self._shake = 0.1
            if self.player_hp <= 0:
                self.done = True
                self.won = False

        # Decay spawn puffs
        self._spawn_puffs = [
            (x, y, t - dt) for x, y, t in self._spawn_puffs if t - dt > 0
        ]

    def draw(self, surf: pygame.Surface) -> None:
        ox = int((random.random() - 0.5) * 10 * self._shake)
        oy = int((random.random() - 0.5) * 10 * self._shake)

        # Arena
        arena = pygame.Rect(80 + ox, 140 + oy, c.SCREEN_W - 160, 360)
        pygame.draw.rect(surf, (40, 25, 80), arena, border_radius=20)
        pygame.draw.rect(surf, (255, 100, 200), arena, width=3, border_radius=20)

        title = pygame.font.SysFont("Arial", 26, bold=True).render(
            f"Fight!  {self.stage.name}", True, c.UI
        )
        surf.blit(title, title.get_rect(center=(c.SCREEN_W // 2 + ox, 160 + oy)))

        # Player army row
        n = max(1, len(self.army))
        for i, slime in enumerate(self.army):
            x = 160 + i * min(70, 500 // n) + ox
            y = 360 + oy
            slime.draw(surf, x, y, scale=0.85)

        # Enemy blob
        ex, ey = 720 + ox, 300 + oy + math.sin(self._enemy_phase) * 8
        enemy = slime_sprite(min(c.MAX_TIER, 3 + self.stage.number // 12), 110)
        # Tint enemy darker/redder
        tinted = enemy.copy()
        tinted.fill((180, 40, 60, 70), special_flags=pygame.BLEND_RGBA_ADD)
        surf.blit(tinted, tinted.get_rect(center=(ex, ey)))
        efont = pygame.font.SysFont("Arial", 18, bold=True)
        elabel = efont.render("MONSTER", True, (255, 120, 140))
        surf.blit(elabel, elabel.get_rect(center=(ex, ey + 70)))

        # HP bars
        self._bar(surf, 120 + ox, 480 + oy, 300, self.player_hp, self.player_max, (80, 255, 140), "Army")
        self._bar(surf, 540 + ox, 480 + oy, 300, self.enemy_hp, self.enemy_max, (255, 90, 110), "Enemy")

    def _bar(
        self,
        surf: pygame.Surface,
        x: int,
        y: int,
        w: int,
        hp: float,
        mx: float,
        color: tuple[int, int, int],
        label: str,
    ) -> None:
        font = pygame.font.SysFont("Arial", 16, bold=True)
        surf.blit(font.render(label, True, c.UI), (x, y - 18))
        pygame.draw.rect(surf, (30, 20, 50), pygame.Rect(x, y, w, 16), border_radius=6)
        ratio = max(0.0, min(1.0, hp / max(1.0, mx)))
        pygame.draw.rect(
            surf, color, pygame.Rect(x, y, int(w * ratio), 16), border_radius=6
        )
        hp_txt = font.render(f"{int(hp)}/{int(mx)}", True, c.UI)
        surf.blit(hp_txt, (x + w + 8, y - 2))
