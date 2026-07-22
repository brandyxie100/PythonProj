"""Versus stage-clearing projectile-duel mode.

Two stick figures stand atop pillars and lob weapons along parabolic arcs.
The player can strafe left/right to dodge, but stepping past the pillar edge
causes a fatal fall. Hits embed weapons and turn the struck body segment red;
a fighter dies when a head is hit or when more than 80% of the body has turned
red. Clear each stage's opponent to advance.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Optional

import pygame

import config as c
from duel_fighter import DuelFighter, EmbeddedWeapon
from projectiles import Projectile, spawn_projectile
from weapon_draw import draw_panel_icon

Point = tuple[float, float]

_PILLAR_TOP_Y: float = 452.0
_PILLAR_WIDTH: int = 104
_PLAYER_X: float = 320.0  # shifted right so the figure clears the weapon panel
_ENEMY_X: float = float(c.SCREEN_W) - 180.0
_PROJECTILE_FLOOR: float = float(c.SCREEN_H) + 30.0
_TOTAL_STAGES: int = 5

# Left-side weapon-selector panel layout.
_PANEL_X: int = 18
_PANEL_Y: int = 196
_PANEL_BTN_W: int = 176
_PANEL_BTN_H: int = 34
_PANEL_GAP: int = 8


@dataclass(frozen=True, slots=True)
class DuelStageSpec:
    """Difficulty and loadout for one duel stage."""

    number: int
    enemy_weapon: str
    fire_interval: float  # seconds between enemy throws
    aim_noise: float  # radians of elevation jitter (lower = more accurate)
    reward: int


def duel_stage(number: int) -> DuelStageSpec:
    """Build one of the escalating duel stages."""
    specs = {
        1: DuelStageSpec(1, "spear", 2.6, 0.20, 25),
        2: DuelStageSpec(2, "bow", 2.2, 0.15, 40),
        3: DuelStageSpec(3, "trident", 1.9, 0.11, 60),
        4: DuelStageSpec(4, "broadsword", 1.6, 0.08, 85),
        5: DuelStageSpec(5, "trident", 1.3, 0.05, 120),
    }
    return specs[number]


def _simulate_miss_distance(
    origin: Point,
    facing: int,
    elevation: float,
    power: float,
    speed_scale: float,
    target: Point,
) -> float:
    """Return the closest a trajectory passes to ``target`` (for AI aiming)."""
    speed = power * speed_scale
    x, y = origin
    vx = facing * math.cos(elevation) * speed
    vy = -math.sin(elevation) * speed
    dt = 1.0 / 120.0
    best = float("inf")
    for _ in range(720):
        vy += c.PROJECTILE_GRAVITY * dt
        x += vx * dt
        y += vy * dt
        best = min(best, math.hypot(x - target[0], y - target[1]))
        if y >= _PROJECTILE_FLOOR or x < -80 or x > c.SCREEN_W + 80:
            break
    return best


def _solve_aim(
    origin: Point,
    facing: int,
    target: Point,
    speed_scale: float,
) -> tuple[float, float]:
    """Search elevation/power pairs for the best firing solution."""
    best_elev = 0.7
    best_power = c.THROW_POWER_MAX
    best_dist = float("inf")
    for ei in range(20):
        elev = c.AIM_MIN_ELEV + (c.AIM_MAX_ELEV - c.AIM_MIN_ELEV) * ei / 19.0
        for pi in range(11):
            power = c.THROW_POWER_MIN + (
                c.THROW_POWER_MAX - c.THROW_POWER_MIN
            ) * pi / 10.0
            dist = _simulate_miss_distance(
                origin, facing, elev, power, speed_scale, target
            )
            if dist < best_dist:
                best_dist = dist
                best_elev = elev
                best_power = power
    return best_elev, best_power


class DuelAI:
    """Aims and fires the enemy fighter with stage-scaled accuracy."""

    def __init__(self, spec: DuelStageSpec) -> None:
        """Store the stage spec and stagger the first shot."""
        self._spec = spec
        self._fire_timer = 1.2

    def update(
        self,
        me: DuelFighter,
        target: DuelFighter,
        dt: float,
    ) -> Optional[Projectile]:
        """Aim toward the target and occasionally fire a projectile."""
        if me.dead or target.dead:
            return None

        stats = c.THROW_WEAPONS[me.weapon_key]
        # Aim toward the torso center so most hits land on the body mass.
        aim_point = target.neck
        aim_elev, power = _solve_aim(
            me.muzzle_point(), me.facing, aim_point, stats.speed_scale
        )
        # Smoothly track the computed elevation so the arm visibly follows aim.
        me.aim_elev += max(-0.05, min(0.05, aim_elev - me.aim_elev))

        self._fire_timer -= dt
        if self._fire_timer > 0.0 or not me.can_throw():
            return None

        self._fire_timer = self._spec.fire_interval
        noisy_elev = aim_elev + random.uniform(-self._spec.aim_noise, self._spec.aim_noise)
        me.aim_elev = max(c.AIM_MIN_ELEV, min(c.AIM_MAX_ELEV, noisy_elev))
        me.throw_cooldown = c.THROW_COOLDOWN
        me.start_throw_animation()
        return spawn_projectile(
            me.weapon_key, me.team, me.muzzle_point(), me.aim_elev, me.facing, power
        )


class VersusScene:
    """Stage-clearing duel: defeat each pillar opponent to advance."""

    def __init__(self) -> None:
        """Set up fonts, the player fighter, and the first stage."""
        self._font = pygame.font.SysFont("Arial", 22, bold=True)
        self._small = pygame.font.SysFont("Arial", 17)
        self._stage_no = 1
        self._score = 0
        self._result: Optional[str] = None
        self._banner_timer = 1.4
        self._space_prev = False
        self._cycle_prev = False
        self._prev_enemy_weapon = ""  # ensures each respawn uses a new weapon

        self._player = DuelFighter(
            team="player",
            x=_PLAYER_X,
            ground_y=_PILLAR_TOP_Y,
            facing=1,
            weapon_key="spear",
        )
        self._projectiles: list[Projectile] = []
        self._enemy: DuelFighter
        self._ai: DuelAI
        self._load_stage(self._stage_no)

    # -- stage lifecycle ----------------------------------------------------
    def _pick_enemy_weapon(self) -> str:
        """Choose a random weapon that differs from the last enemy's weapon."""
        options = [w for w in c.THROW_WEAPON_ORDER if w != self._prev_enemy_weapon]
        weapon = random.choice(options)
        self._prev_enemy_weapon = weapon
        return weapon

    def _load_stage(self, number: int) -> None:
        spec = duel_stage(number)
        # Each newly spawned enemy takes over the same pillar but wields a
        # different weapon from the one the previous enemy used.
        self._enemy = DuelFighter(
            team="enemy",
            x=_ENEMY_X,
            ground_y=_PILLAR_TOP_Y,
            facing=-1,
            weapon_key=self._pick_enemy_weapon(),
        )
        self._ai = DuelAI(spec)
        self._projectiles.clear()
        self._player.reset_health()
        self._banner_timer = 1.4

    # -- input --------------------------------------------------------------
    @staticmethod
    def _weapon_buttons() -> list[tuple[pygame.Rect, str]]:
        """Return clickable rects paired with their weapon key."""
        buttons: list[tuple[pygame.Rect, str]] = []
        for i, key in enumerate(c.THROW_WEAPON_ORDER):
            rect = pygame.Rect(
                _PANEL_X,
                _PANEL_Y + i * (_PANEL_BTN_H + _PANEL_GAP),
                _PANEL_BTN_W,
                _PANEL_BTN_H,
            )
            buttons.append((rect, key))
        return buttons

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle weapon cycling (E) and left-panel weapon selection (click)."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
            self._player.cycle_weapon()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect, key in self._weapon_buttons():
                if rect.collidepoint(event.pos):
                    self._player.weapon_key = key
                    break

    def _handle_player_input(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        move_axis = int(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - int(
            keys[pygame.K_a] or keys[pygame.K_LEFT]
        )
        self._player.apply_move_axis(move_axis, dt)

        aim_dir = int(keys[pygame.K_w] or keys[pygame.K_UP]) - int(
            keys[pygame.K_s] or keys[pygame.K_DOWN]
        )
        self._player.rotate_aim(aim_dir, dt)

        space = bool(keys[pygame.K_SPACE])
        if space and not self._space_prev:
            self._player.start_charge()
        if not space and self._space_prev:
            power = self._player.release_charge()
            if power is not None:
                self._projectiles.append(
                    spawn_projectile(
                        self._player.weapon_key,
                        "player",
                        self._player.muzzle_point(),
                        self._player.aim_elev,
                        self._player.facing,
                        power,
                    )
                )
        self._space_prev = space

    # -- update -------------------------------------------------------------
    def update(self, dt: float) -> Optional[str]:
        """Advance one frame; returns 'win'/'lose' when the run ends."""
        if self._result is not None:
            return self._result

        self._handle_player_input(dt)
        self._player.update(dt)
        self._enemy.update(dt)

        enemy_shot = self._ai.update(self._enemy, self._player, dt)
        if enemy_shot is not None:
            self._projectiles.append(enemy_shot)

        self._advance_projectiles(dt)

        if self._player.dead:
            self._result = "lose"
            return self._result

        if self._enemy.dead:
            self._score += duel_stage(self._stage_no).reward
            if self._stage_no >= _TOTAL_STAGES:
                self._result = "win"
                return self._result
            self._stage_no += 1
            self._load_stage(self._stage_no)

        if self._banner_timer > 0.0:
            self._banner_timer = max(0.0, self._banner_timer - dt)
        return None

    def _advance_projectiles(self, dt: float) -> None:
        for proj in self._projectiles:
            if proj.dead:
                continue
            prev_tip = proj.tip()
            proj.update(dt, _PROJECTILE_FLOOR)
            target = self._enemy if proj.team == "player" else self._player
            if target.dead:
                continue
            # Swept hit test: sample along the tip's travel this frame so fast
            # projectiles cannot tunnel through the thin stick-figure body.
            hit = self._swept_hit(target, prev_tip, proj.tip())
            if hit is None:
                continue
            segment, point = hit
            target.apply_hit(
                segment,
                proj.stats.damage,
                EmbeddedWeapon(proj.weapon_key, point[0], point[1], proj.angle),
            )
            proj.dead = True
        self._projectiles = [p for p in self._projectiles if not p.dead]

    @staticmethod
    def _swept_hit(
        target: DuelFighter,
        start: Point,
        end: Point,
    ) -> Optional[tuple[str, Point]]:
        """Sample points from ``start`` to ``end`` and return the first body hit."""
        span = math.hypot(end[0] - start[0], end[1] - start[1])
        steps = max(1, int(span / 5.0))
        for i in range(steps + 1):
            t = i / steps
            point = (start[0] + (end[0] - start[0]) * t, start[1] + (end[1] - start[1]) * t)
            segment = target.hit_test(point)
            if segment is not None:
                return segment, point
        return None

    # -- rendering ----------------------------------------------------------
    def draw(self, surf: pygame.Surface) -> None:
        """Render background, pillars, fighters, projectiles, and HUD."""
        self._draw_background(surf)
        self._draw_pillar(surf, _PLAYER_X)
        self._draw_pillar(surf, _ENEMY_X)

        self._player.draw(surf)
        self._enemy.draw(surf)
        for proj in self._projectiles:
            proj.draw(surf)

        self._draw_hud(surf)

    def _draw_background(self, surf: pygame.Surface) -> None:
        for y in range(c.SCREEN_H):
            t = y / c.SCREEN_H
            color = tuple(
                int(c.DUEL_BG_TOP[i] + (c.DUEL_BG_BOTTOM[i] - c.DUEL_BG_TOP[i]) * t)
                for i in range(3)
            )
            pygame.draw.line(surf, color, (0, y), (c.SCREEN_W, y))

    def _draw_pillar(self, surf: pygame.Surface, x: float) -> None:
        left = int(x - _PILLAR_WIDTH / 2)
        pygame.draw.rect(
            surf,
            c.DUEL_PILLAR_COLOR,
            pygame.Rect(left, int(_PILLAR_TOP_Y), _PILLAR_WIDTH, c.SCREEN_H),
        )
        pygame.draw.rect(
            surf,
            c.DUEL_PILLAR_TOP,
            pygame.Rect(left - 6, int(_PILLAR_TOP_Y) - 10, _PILLAR_WIDTH + 12, 14),
            border_radius=4,
        )

    def _draw_hud(self, surf: pygame.Surface) -> None:
        stage_txt = self._font.render(
            f"STAGE {self._stage_no}/{_TOTAL_STAGES}", True, (30, 40, 30)
        )
        score_txt = self._font.render(f"COINS: {self._score}", True, (120, 80, 20))
        surf.blit(stage_txt, (20, 18))
        surf.blit(score_txt, (20, 46))

        self._draw_integrity(surf, 20, 78, "YOU", self._player)
        self._draw_integrity(surf, c.SCREEN_W - 240, 78, "ENEMY", self._enemy)

        weapon_txt = self._small.render(
            f"Weapon: {c.THROW_WEAPONS[self._player.weapon_key].name}",
            True,
            (30, 40, 30),
        )
        surf.blit(weapon_txt, (20, 108))

        # Power meter
        meter = pygame.Rect(20, 134, 220, 16)
        pygame.draw.rect(surf, (40, 60, 40), meter, border_radius=4)
        frac = (self._player.power - c.THROW_POWER_MIN) / (
            c.THROW_POWER_MAX - c.THROW_POWER_MIN
        )
        frac = max(0.0, min(1.0, frac))
        pygame.draw.rect(
            surf,
            (240, 180, 40),
            pygame.Rect(20, 134, int(220 * frac), 16),
            border_radius=4,
        )
        power_label = self._small.render("POWER (hold Space)", True, (30, 40, 30))
        surf.blit(power_label, (250, 133))

        self._draw_weapon_panel(surf)

        controls = self._small.render(
            "A/D dodge  |  W/S aim  |  Hold Space: throw  |  E or click panel: weapon"
            "  |  Don't fall off!",
            True,
            (32, 44, 32),
        )
        surf.blit(controls, (20, c.SCREEN_H - 28))

        if self._banner_timer > 0.0:
            banner = self._font.render(f"STAGE {self._stage_no}", True, (20, 30, 20))
            surf.blit(banner, banner.get_rect(center=(c.SCREEN_W // 2, 40)))

    def _draw_weapon_panel(self, surf: pygame.Surface) -> None:
        """Draw the clickable weapon selector on the left of the screen."""
        title = self._small.render("WEAPONS", True, (28, 40, 28))
        surf.blit(title, (_PANEL_X, _PANEL_Y - 22))
        mouse = pygame.mouse.get_pos()
        for rect, key in self._weapon_buttons():
            stats = c.THROW_WEAPONS[key]
            selected = key == self._player.weapon_key
            hovered = rect.collidepoint(mouse)
            if selected:
                fill = (250, 214, 96)
            elif hovered:
                fill = (150, 196, 128)
            else:
                fill = (56, 96, 62)
            pygame.draw.rect(surf, fill, rect, border_radius=7)
            pygame.draw.rect(surf, (30, 46, 32), rect, 2, border_radius=7)

            # Mini multi-part weapon icon instead of a flat color swatch.
            icon_center = (rect.x + 22, rect.centery)
            draw_panel_icon(surf, key, icon_center, size=24.0)

            text_color = (40, 34, 12) if selected else (238, 244, 236)
            name = self._small.render(stats.name, True, text_color)
            surf.blit(name, (rect.x + 42, rect.centery - name.get_height() // 2))

    def _draw_integrity(
        self,
        surf: pygame.Surface,
        x: int,
        y: int,
        label: str,
        fighter: DuelFighter,
    ) -> None:
        """Draw a body-integrity bar (inverse of accumulated redness)."""
        ratio = max(0.0, 1.0 - fighter.body_red_ratio() / c.BODY_RED_DEATH_RATIO)
        bar = pygame.Rect(x, y, 220, 18)
        pygame.draw.rect(surf, (40, 60, 40), bar, border_radius=4)
        pygame.draw.rect(
            surf,
            (70, 200, 90),
            pygame.Rect(x, y, int(220 * ratio), 18),
            border_radius=4,
        )
        text = self._small.render(f"{label} integrity", True, (30, 40, 30))
        surf.blit(text, (x, y - 20))

    @property
    def score(self) -> int:
        """Coins earned so far in this duel run."""
        return self._score
