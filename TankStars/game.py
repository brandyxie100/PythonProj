"""Core Tank Stars gameplay — 20-stage artillery campaign."""

from __future__ import annotations

import math
import random
from typing import Optional

import pygame

import config as c
from blast import BlastSystem
from stages import StageSpec, stage_spec
from tanks import Shell, Tank
from terrain import Terrain


class Game:
    """Turn-based Tank Stars match across 20 stages."""

    def __init__(self) -> None:
        self._title = pygame.font.SysFont("Arial", 48, bold=True)
        self._font = pygame.font.SysFont("Arial", 24, bold=True)
        self._small = pygame.font.SysFont("Arial", 17)
        self._tiny = pygame.font.SysFont("Arial", 14)

        self.stage_no = 1
        self.spec: StageSpec = stage_spec(1)
        self.terrain = Terrain(1)
        self.blasts = BlastSystem()
        self.player = Tank(
            team="player",
            x=120,
            facing=1,
            body=c.PLAYER_BODY,
            trim=c.PLAYER_TRIM,
        )
        self.enemies: list[Tank] = []
        self.shells: list[Shell] = []
        self.wind = 0.0
        self.turn: str = "player"  # player | enemy | wait
        self.enemy_ix = 0
        self.state = "title"  # title | playing | stage_clear | win | lose
        self.message = ""
        self.message_timer = 0.0
        self.ai_timer = 0.0
        self.ai_ready = False
        self.space_prev = False
        self.request_quit = False
        self._last_shooter = "player"
        self._load_stage(1, show_title=True)

    def _load_stage(self, number: int, *, show_title: bool = False) -> None:
        self.stage_no = number
        self.spec = stage_spec(number)
        self.terrain = Terrain(number)
        self.blasts.clear()
        self.shells.clear()
        self.player = Tank(
            team="player",
            x=130 + random.randint(-20, 20),
            facing=1,
            body=c.PLAYER_BODY,
            trim=c.PLAYER_TRIM,
        )
        self.player.sync_to_ground(self.terrain)
        self.enemies = []
        if self.spec.enemy_count == 1:
            xs = [c.SCREEN_W - 150]
        else:
            xs = [c.SCREEN_W - 280, c.SCREEN_W - 120]
        for ex in xs:
            foe = Tank(
                team="enemy",
                x=ex + random.randint(-15, 15),
                facing=-1,
                body=c.ENEMY_BODY,
                trim=c.ENEMY_TRIM,
                hp=self.spec.enemy_hp,
            )
            foe.sync_to_ground(self.terrain)
            self.enemies.append(foe)
        self._roll_wind()
        self.turn = "player"
        self.enemy_ix = 0
        self.ai_timer = 0.0
        self.ai_ready = False
        self.state = "title" if show_title else "playing"
        self.message = ""
        self.message_timer = 0.0

    def _roll_wind(self) -> None:
        self.wind = random.uniform(-1, 1) * c.TURN_WIND_MAX * self.spec.wind_scale

    def _living_enemies(self) -> list[Tank]:
        return [e for e in self.enemies if e.alive]

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.state == "playing":
                self.state = "title"
            else:
                self.request_quit = True
            return

        if self.state == "title":
            if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_RETURN,
                pygame.K_SPACE,
            ):
                self.state = "playing"
            return

        if self.state in ("stage_clear", "win"):
            if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_RETURN,
                pygame.K_SPACE,
            ):
                if self.state == "win":
                    self._load_stage(1, show_title=True)
                else:
                    nxt = self.stage_no + 1
                    if nxt > c.MAX_STAGES:
                        self.state = "win"
                    else:
                        self._load_stage(nxt)
            return

        if self.state == "lose":
            if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_RETURN,
                pygame.K_SPACE,
            ):
                self._load_stage(self.stage_no)
            return

    def update(self, dt: float) -> None:
        self.blasts.update(dt)
        if self.message_timer > 0:
            self.message_timer = max(0.0, self.message_timer - dt)

        if self.state != "playing":
            return

        # Keep tanks stuck to deforming ground.
        self.player.sync_to_ground(self.terrain)
        for e in self.enemies:
            if e.alive:
                e.sync_to_ground(self.terrain)

        if self.turn == "wait":
            self._update_shells(dt)
            if not any(s.alive for s in self.shells) and not self.blasts.blasts:
                self.shells = [s for s in self.shells if s.alive]
                self._after_shot()
            return

        if self.turn == "player" and self.player.alive:
            self._handle_player_controls(dt)
        elif self.turn == "enemy":
            self._update_ai(dt)

        self._update_shells(dt)

    def _handle_player_controls(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.player.move(-1, dt, self.terrain, 60, c.SCREEN_W * 0.42)
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.player.move(1, dt, self.terrain, 60, c.SCREEN_W * 0.42)
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.player.adjust_aim(c.AIM_SPEED * dt)
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.player.adjust_aim(-c.AIM_SPEED * dt)

        space = keys[pygame.K_SPACE]
        if space:
            if not self.player.charging:
                self.player.charging = True
                self.player.power = c.POWER_MIN
            else:
                self.player.adjust_power(c.POWER_SPEED * dt)
        elif self.space_prev and self.player.charging:
            self.player.charging = False
            self._fire(self.player)
        self.space_prev = bool(space)

    def _fire(self, tank: Tank) -> None:
        shell = tank.fire()
        self.shells.append(shell)
        self._last_shooter = tank.team
        self.turn = "wait"

    def _update_shells(self, dt: float) -> None:
        for shell in self.shells:
            if not shell.alive:
                continue
            hit = shell.update(dt, self.wind, self.terrain)
            if not hit:
                # Tank collision
                targets = []
                if shell.team == "player":
                    targets = self._living_enemies()
                elif self.player.alive:
                    targets = [self.player]
                for tank in targets:
                    if tank.hitbox().collidepoint(shell.x, shell.y):
                        shell.alive = False
                        hit = True
                        tank.take_damage(shell.damage)
                        break
            if hit or not shell.alive:
                self._explode(shell)

    def _explode(self, shell: Shell) -> None:
        if shell.exploded:
            return
        shell.exploded = True
        shell.alive = False
        if shell.x < -20 or shell.x > c.SCREEN_W + 20:
            return
        power = self.spec.blast_bonus * (0.85 + shell.damage / 80.0)
        self.blasts.spawn(shell.x, shell.y, power=power)
        radius = c.CRATER_RADIUS * (0.75 + 0.35 * power)
        self.terrain.carve_crater(shell.x, shell.y, radius)
        # Splash damage
        for tank in [self.player, *self.enemies]:
            if not tank.alive:
                continue
            dist = math.hypot(tank.x - shell.x, tank.y - c.TANK_H * 0.5 - shell.y)
            if dist < radius * 1.35:
                falloff = 1.0 - dist / (radius * 1.35)
                tank.take_damage(shell.damage * 0.55 * falloff)

    def _after_shot(self) -> None:
        if not self.player.alive:
            self.state = "lose"
            self.message = "Your tank was destroyed!"
            return
        if not self._living_enemies():
            if self.stage_no >= c.MAX_STAGES:
                self.state = "win"
                self.message = "All 20 stages cleared!"
            else:
                self.state = "stage_clear"
                self.message = f"Stage {self.stage_no} clear — {self.spec.name}"
            return

        self._roll_wind()
        self.shells.clear()
        if self._last_shooter == "player":
            self.turn = "enemy"
            self.enemy_ix = 0
            self.ai_timer = 0.6
            self.ai_ready = False
        else:
            self.enemy_ix += 1
            living = self._living_enemies()
            if self.enemy_ix >= len(living):
                self.turn = "player"
                self.enemy_ix = 0
            else:
                self.turn = "enemy"
                self.ai_timer = 0.5
                self.ai_ready = False

    def _update_ai(self, dt: float) -> None:
        living = self._living_enemies()
        if not living:
            self.turn = "player"
            return
        if self.enemy_ix >= len(living):
            self.enemy_ix = 0
        foe = living[self.enemy_ix]
        self.ai_timer -= dt
        if self.ai_timer > 0:
            return

        if not self.ai_ready:
            # Aim toward player with skill-scaled noise.
            tx, ty = self.player.x, self.player.y - 20
            mx, my = foe.muzzle()
            dx = tx - mx
            dy = my - ty
            # Rough ballistic elevation guess.
            dist = max(40.0, abs(dx))
            elev = math.atan2(dy + dist * 0.22, dist)
            elev += random.uniform(-1, 1) * c.AI_AIM_NOISE * (1.2 - self.spec.ai_skill)
            foe.aim = max(0.12, min(1.35, elev))
            # Power from distance
            power = 35 + dist / 14.0
            power += random.uniform(-1, 1) * c.AI_POWER_NOISE * (1.1 - self.spec.ai_skill)
            # Wind compensation
            power += abs(self.wind) * 0.08
            foe.power = max(c.POWER_MIN, min(c.POWER_MAX, power))
            # Occasional shuffle
            foe.move(
                random.choice([-1, 0, 0, 1]),
                0.25,
                self.terrain,
                c.SCREEN_W * 0.55,
                c.SCREEN_W - 70,
            )
            self.ai_ready = True
            self.ai_timer = 0.35
            return

        self._fire(foe)

    # -- drawing -----------------------------------------------------------
    def draw(self, surf: pygame.Surface) -> None:
        self._draw_sky(surf)
        self.terrain.draw(surf)
        for shell in self.shells:
            shell.draw(surf)
        self.player.draw(surf)
        for e in self.enemies:
            e.draw(surf)
        self.blasts.draw(surf)
        self._draw_hud(surf)

        if self.state == "title":
            self._banner(
                surf,
                "TANK STARS",
                "20 stages of artillery mayhem — Enter to fight",
            )
        elif self.state == "stage_clear":
            self._banner(surf, "STAGE CLEAR", "Enter for next stage")
        elif self.state == "win":
            self._banner(surf, "VICTORY!", "You cleared all 20 stages — Enter to replay")
        elif self.state == "lose":
            self._banner(surf, "DEFEAT", "Enter to retry this stage")

    def _draw_sky(self, surf: pygame.Surface) -> None:
        for y in range(c.SCREEN_H):
            t = y / c.SCREEN_H
            color = tuple(
                int(c.SKY_TOP[i] + (c.SKY_BOTTOM[i] - c.SKY_TOP[i]) * t) for i in range(3)
            )
            pygame.draw.line(surf, color, (0, y), (c.SCREEN_W, y))
        # Soft clouds
        for i, cx in enumerate((180, 420, 700, 920)):
            cy = 70 + (i % 3) * 18
            pygame.draw.ellipse(surf, (255, 255, 255), pygame.Rect(cx, cy, 90, 28))
            pygame.draw.ellipse(surf, (255, 255, 255), pygame.Rect(cx + 30, cy - 10, 70, 30))

    def _draw_hud(self, surf: pygame.Surface) -> None:
        panel = pygame.Surface((c.SCREEN_W, 72), pygame.SRCALPHA)
        panel.fill((20, 30, 40, 170))
        surf.blit(panel, (0, 0))

        stage = self._font.render(
            f"Stage {self.stage_no}/{c.MAX_STAGES}: {self.spec.name}",
            True,
            c.UI,
        )
        surf.blit(stage, (16, 10))

        # Wind meter
        wind_label = self._small.render("WIND", True, c.UI)
        surf.blit(wind_label, (c.SCREEN_W // 2 - 90, 12))
        wx0 = c.SCREEN_W // 2
        pygame.draw.line(surf, (200, 200, 210), (wx0 - 60, 40), (wx0 + 60, 40), 3)
        tip = int(wx0 + self.wind * 1.1)
        pygame.draw.polygon(
            surf,
            (255, 200, 60) if self.wind >= 0 else (120, 200, 255),
            [(tip, 40), (tip - 8, 32), (tip - 8, 48)]
            if self.wind >= 0
            else [(tip, 40), (tip + 8, 32), (tip + 8, 48)],
        )

        # Player HP
        self._hp_bar(surf, 16, 44, self.player, "YOU")
        # Enemy HP stack
        ey = 44
        for i, e in enumerate(self.enemies):
            if not e.alive:
                continue
            self._hp_bar(surf, c.SCREEN_W - 216, ey, e, f"E{i + 1}")
            ey += 22

        if self.turn == "player" and self.state == "playing":
            # Power / aim
            aim_deg = int(math.degrees(self.player.aim))
            info = self._small.render(
                f"Aim {aim_deg}°   Power {int(self.player.power)}%   "
                f"{'CHARGING' if self.player.charging else 'Hold SPACE'}",
                True,
                c.POWER_YELLOW if self.player.charging else c.UI,
            )
            surf.blit(info, (16, c.SCREEN_H - 28))
            # Power bar
            bar = pygame.Rect(260, c.SCREEN_H - 26, 200, 12)
            pygame.draw.rect(surf, (40, 50, 60), bar, border_radius=4)
            fill = int(bar.w * (self.player.power / c.POWER_MAX))
            pygame.draw.rect(
                surf,
                c.POWER_YELLOW,
                pygame.Rect(bar.x, bar.y, fill, bar.h),
                border_radius=4,
            )

        turn = "YOUR TURN" if self.turn == "player" else (
            "SHELL IN FLIGHT" if self.turn == "wait" else "ENEMY TURN"
        )
        turn_c = c.HP_GREEN if self.turn == "player" else (
            c.POWER_YELLOW if self.turn == "wait" else c.HP_RED
        )
        ttxt = self._small.render(turn, True, turn_c)
        surf.blit(ttxt, (c.SCREEN_W - ttxt.get_width() - 16, 12))

        hint = self._tiny.render(
            "A/D move  W/S aim  Hold SPACE power  Esc menu",
            True,
            (30, 50, 70),
        )
        surf.blit(hint, (c.SCREEN_W - hint.get_width() - 12, c.SCREEN_H - 22))

    def _hp_bar(self, surf: pygame.Surface, x: int, y: int, tank: Tank, label: str) -> None:
        lab = self._tiny.render(label, True, c.UI)
        surf.blit(lab, (x, y - 2))
        bar = pygame.Rect(x + 28, y, 160, 10)
        pygame.draw.rect(surf, (50, 50, 60), bar, border_radius=3)
        ratio = tank.hp / max(1.0, tank.max_hp)
        color = c.HP_GREEN if ratio > 0.35 else c.HP_RED
        pygame.draw.rect(
            surf, color, pygame.Rect(bar.x, bar.y, int(bar.w * ratio), bar.h), border_radius=3
        )

    def _banner(self, surf: pygame.Surface, title: str, subtitle: str) -> None:
        overlay = pygame.Surface((c.SCREEN_W, c.SCREEN_H), pygame.SRCALPHA)
        overlay.fill((10, 20, 30, 150))
        surf.blit(overlay, (0, 0))
        t = self._title.render(title, True, c.UI)
        s = self._font.render(subtitle, True, (200, 210, 220))
        surf.blit(t, t.get_rect(center=(c.SCREEN_W // 2, c.SCREEN_H // 2 - 30)))
        surf.blit(s, s.get_rect(center=(c.SCREEN_W // 2, c.SCREEN_H // 2 + 30)))
