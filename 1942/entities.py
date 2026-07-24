"""Combat entities: player, enemies, bosses, bullets, powerups."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Callable

import pygame as pg

import config as cfg
import sprites


# ---------------------------------------------------------------------------
# Shared bullet
# ---------------------------------------------------------------------------
@dataclass
class Bullet:
    """A single projectile in flight."""

    x: float
    y: float
    vx: float
    vy: float
    friendly: bool
    damage: int = 1
    kind: str = "normal"
    alive: bool = True
    radius: float = 3.0

    def update(self, dt: float) -> None:
        """Move and cull off-screen shots."""
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.y < -30 or self.y > cfg.SCREEN_H + 30 or self.x < -30 or self.x > cfg.SCREEN_W + 30:
            self.alive = False

    def draw(self, surface: pg.Surface) -> None:
        """Render projectile."""
        sprites.draw_bullet(surface, self.x, self.y, friendly=self.friendly, kind=self.kind)

    def hitbox(self) -> pg.Rect:
        """Collision rect."""
        r = int(self.radius)
        return pg.Rect(int(self.x - r), int(self.y - r), r * 2, r * 2)


# ---------------------------------------------------------------------------
# Player upgrades (persist across missions in a run)
# ---------------------------------------------------------------------------
@dataclass
class Loadout:
    """Player upgrade state for the current campaign run."""

    fire_level: int = 0  # 0..4 — cooldown / multi-shot
    spread_level: int = 0  # 0..3 — side guns
    speed_level: int = 0  # 0..3
    shield_level: int = 0  # bonus HP layers
    bomb_level: int = 0  # starting bombs + radius

    def fire_cooldown(self) -> float:
        """Seconds between volleys."""
        return max(0.08, cfg.PLAYER_FIRE_COOLDOWN - self.fire_level * 0.02)

    def move_speed(self) -> float:
        """Horizontal/vertical flight speed."""
        return cfg.PLAYER_SPEED * (1.0 + self.speed_level * 0.12)

    def max_hp(self) -> int:
        """Hit points including shield upgrades."""
        return cfg.PLAYER_MAX_HP + self.shield_level

    def start_bombs(self) -> int:
        """Bombs available at mission start."""
        return cfg.PLAYER_BOMB_COUNT_START + self.bomb_level


# ---------------------------------------------------------------------------
# Player
# ---------------------------------------------------------------------------
class Player:
    """US Navy interceptor controlled by the player."""

    def __init__(self, loadout: Loadout) -> None:
        """Spawn above the carrier lane at bottom-center."""
        self.loadout = loadout
        self.x = cfg.SCREEN_W * 0.5
        self.y = cfg.SCREEN_H * 0.78
        self.hp = loadout.max_hp()
        self.bombs = loadout.start_bombs()
        self.alive = True
        self.prop = 0.0
        self.fire_timer = 0.0
        self.loop_timer = 0.0
        self.loop_cd = 0.0
        self.invuln = 0.0
        self.flash = False
        self.score_mult = 1

    def hitbox(self) -> pg.Rect:
        """Tight fuselage hitbox while looping grants i-frames."""
        if self.loop_timer > 0:
            return pg.Rect(-100, -100, 0, 0)
        return pg.Rect(int(self.x - 10), int(self.y - 12), 20, 28)

    def update(self, dt: float, keys: pg.key.ScancodeWrapper, spawn_bullet: Callable) -> None:
        """Handle movement, fire, and loop dodge."""
        if not self.alive:
            return
        self.prop += dt * 28
        self.fire_timer = max(0.0, self.fire_timer - dt)
        self.loop_cd = max(0.0, self.loop_cd - dt)
        self.invuln = max(0.0, self.invuln - dt)
        self.flash = self.invuln > 0 and int(self.invuln * 12) % 2 == 0

        if self.loop_timer > 0:
            self.loop_timer -= dt
            self.y -= 40 * dt
            return

        speed = self.loadout.move_speed()
        dx = dy = 0.0
        if keys[pg.K_LEFT] or keys[pg.K_a]:
            dx -= 1
        if keys[pg.K_RIGHT] or keys[pg.K_d]:
            dx += 1
        if keys[pg.K_UP] or keys[pg.K_w]:
            dy -= 1
        if keys[pg.K_DOWN] or keys[pg.K_s]:
            dy += 1
        if dx or dy:
            length = math.hypot(dx, dy)
            self.x += (dx / length) * speed * dt
            self.y += (dy / length) * speed * dt
        self.x = max(24, min(cfg.SCREEN_W - 24, self.x))
        self.y = max(40, min(cfg.SCREEN_H - 30, self.y))

        if keys[pg.K_SPACE] and self.fire_timer <= 0:
            self._fire(spawn_bullet)
            self.fire_timer = self.loadout.fire_cooldown()

        if (keys[pg.K_LSHIFT] or keys[pg.K_RSHIFT]) and self.loop_cd <= 0:
            self.loop_timer = cfg.PLAYER_LOOP_DURATION
            self.loop_cd = cfg.PLAYER_LOOP_COOLDOWN
            self.invuln = max(self.invuln, cfg.PLAYER_LOOP_DURATION)

    def _fire(self, spawn_bullet: Callable) -> None:
        """Spawn primary + upgrade volleys."""
        dmg = 1 + self.loadout.fire_level // 2
        spawn_bullet(Bullet(self.x, self.y - 18, 0, -cfg.PLAYER_BULLET_SPEED, True, dmg, "heavy" if self.loadout.fire_level >= 3 else "normal"))
        if self.loadout.fire_level >= 1:
            spawn_bullet(Bullet(self.x - 8, self.y - 10, 0, -cfg.PLAYER_BULLET_SPEED, True, 1))
            spawn_bullet(Bullet(self.x + 8, self.y - 10, 0, -cfg.PLAYER_BULLET_SPEED, True, 1))
        if self.loadout.spread_level >= 1:
            spawn_bullet(Bullet(self.x, self.y - 12, -120, -cfg.PLAYER_BULLET_SPEED * 0.95, True, 1, "spread"))
            spawn_bullet(Bullet(self.x, self.y - 12, 120, -cfg.PLAYER_BULLET_SPEED * 0.95, True, 1, "spread"))
        if self.loadout.spread_level >= 2:
            spawn_bullet(Bullet(self.x, self.y - 12, -220, -cfg.PLAYER_BULLET_SPEED * 0.9, True, 1, "spread"))
            spawn_bullet(Bullet(self.x, self.y - 12, 220, -cfg.PLAYER_BULLET_SPEED * 0.9, True, 1, "spread"))
        if self.loadout.spread_level >= 3:
            spawn_bullet(Bullet(self.x - 14, self.y, -40, -cfg.PLAYER_BULLET_SPEED, True, 1, "spread"))
            spawn_bullet(Bullet(self.x + 14, self.y, 40, -cfg.PLAYER_BULLET_SPEED, True, 1, "spread"))

    def try_bomb(self) -> bool:
        """Consume a bomb if available."""
        if self.bombs <= 0 or not self.alive:
            return False
        self.bombs -= 1
        self.invuln = max(self.invuln, 0.6)
        return True

    def damage(self, amount: int = 1) -> None:
        """Apply damage unless invulnerable / looping."""
        if not self.alive or self.invuln > 0 or self.loop_timer > 0:
            return
        self.hp -= amount
        self.invuln = cfg.PLAYER_INVULN_AFTER_HIT
        if self.hp <= 0:
            self.alive = False

    def draw(self, surface: pg.Surface) -> None:
        """Render fighter."""
        if not self.alive:
            return
        if self.flash:
            return
        sprites.draw_player_plane(
            surface,
            self.x,
            self.y,
            prop_angle=self.prop,
            looping=self.loop_timer > 0,
            flash=False,
        )


# ---------------------------------------------------------------------------
# Enemies
# ---------------------------------------------------------------------------
@dataclass
class Enemy:
    """Generic hostile aircraft / surface unit."""

    kind: str
    x: float
    y: float
    hp: int
    score: int
    vx: float = 0.0
    vy: float = 80.0
    alive: bool = True
    prop: float = 0.0
    fire_cd: float = 1.0
    fire_timer: float = field(default_factory=lambda: random.uniform(0.2, 1.0))
    phase: float = field(default_factory=lambda: random.uniform(0, math.pi * 2))
    tilt: float = 0.0
    flash: float = 0.0

    def hitbox(self) -> pg.Rect:
        """Approximate collision bounds by kind."""
        sizes = {
            "fighter": (28, 28),
            "interceptor": (26, 28),
            "bomber": (60, 32),
            "dive": (32, 28),
            "gunboat": (52, 24),
        }
        w, h = sizes.get(self.kind, (28, 28))
        return pg.Rect(int(self.x - w / 2), int(self.y - h / 2), w, h)

    def update(self, dt: float, player: Player, spawn_bullet: Callable) -> None:
        """Move, pattern, and shoot."""
        if not self.alive:
            return
        self.prop += dt * 20
        self.flash = max(0.0, self.flash - dt)
        self.phase += dt
        self.fire_timer -= dt

        if self.kind == "fighter":
            self.x += math.sin(self.phase * 2.0) * 60 * dt + self.vx * dt
            self.y += self.vy * dt
            if self.fire_timer <= 0:
                spawn_bullet(Bullet(self.x, self.y + 12, 0, cfg.ENEMY_BULLET_SPEED, False, 1))
                self.fire_timer = self.fire_cd
        elif self.kind == "interceptor":
            # Aggressive pursuit on X
            aim = 1 if player.x > self.x else -1
            self.x += aim * 90 * dt
            self.y += self.vy * 1.25 * dt
            if self.fire_timer <= 0:
                dx = player.x - self.x
                dy = player.y - self.y
                dist = max(1.0, math.hypot(dx, dy))
                spd = cfg.ENEMY_BULLET_SPEED * 1.15
                spawn_bullet(Bullet(self.x, self.y + 10, dx / dist * spd, dy / dist * spd, False, 1, "aim"))
                self.fire_timer = self.fire_cd * 0.85
        elif self.kind == "bomber":
            self.x += math.sin(self.phase) * 30 * dt
            self.y += self.vy * 0.55 * dt
            if self.fire_timer <= 0:
                for ox in (-12, 0, 12):
                    spawn_bullet(Bullet(self.x + ox, self.y + 14, ox * 2, cfg.ENEMY_BULLET_SPEED * 0.8, False, 1))
                self.fire_timer = self.fire_cd * 1.2
        elif self.kind == "dive":
            if self.y < player.y - 40:
                self.tilt = math.atan2(player.x - self.x, player.y - self.y) * 0.35
                self.x += (player.x - self.x) * 1.2 * dt
                self.y += self.vy * 1.6 * dt
            else:
                self.y += self.vy * 0.7 * dt
                self.tilt *= 0.9
            if self.fire_timer <= 0 and abs(self.x - player.x) < 80:
                spawn_bullet(Bullet(self.x, self.y + 10, 0, cfg.ENEMY_BULLET_SPEED * 1.3, False, 1, "aim"))
                self.fire_timer = self.fire_cd
        elif self.kind == "gunboat":
            self.y += cfg.OCEAN_SCROLL_BASE * dt * 0.35
            self.x += math.sin(self.phase * 0.8) * 40 * dt
            if self.fire_timer <= 0:
                spawn_bullet(Bullet(self.x, self.y - 8, 0, -cfg.ENEMY_BULLET_SPEED * 0.5, False, 1))
                angle = math.atan2(player.y - self.y, player.x - self.x)
                spawn_bullet(
                    Bullet(
                        self.x,
                        self.y - 8,
                        math.cos(angle) * cfg.ENEMY_BULLET_SPEED,
                        math.sin(angle) * cfg.ENEMY_BULLET_SPEED,
                        False,
                        1,
                        "aim",
                    )
                )
                self.fire_timer = self.fire_cd * 1.4

        if self.y > cfg.SCREEN_H + 60 or self.x < -80 or self.x > cfg.SCREEN_W + 80:
            self.alive = False

    def hurt(self, dmg: int) -> None:
        """Apply bullet damage."""
        self.hp -= dmg
        self.flash = 0.08
        if self.hp <= 0:
            self.alive = False

    def draw(self, surface: pg.Surface) -> None:
        """Render by kind."""
        if not self.alive:
            return
        if self.flash > 0:
            # white flash via brief skip of dark fill — draw outline only
            pg.draw.circle(surface, cfg.UI_WHITE, (int(self.x), int(self.y)), 6, 1)
        if self.kind == "fighter":
            sprites.draw_enemy_fighter(surface, self.x, self.y, prop_angle=self.prop)
        elif self.kind == "interceptor":
            sprites.draw_enemy_fighter(
                surface, self.x, self.y, prop_angle=self.prop, color=(110, 100, 40)
            )
        elif self.kind == "bomber":
            sprites.draw_enemy_bomber(surface, self.x, self.y, prop_angle=self.prop)
        elif self.kind == "dive":
            sprites.draw_enemy_dive(surface, self.x, self.y, tilt=self.tilt)
        elif self.kind == "gunboat":
            sprites.draw_gunboat(surface, self.x, self.y)


# ---------------------------------------------------------------------------
# Boss
# ---------------------------------------------------------------------------
class Boss:
    """Mission boss — large multi-phase air fortress."""

    def __init__(self, mission: int, name: str) -> None:
        """Scale HP and aggression with mission index."""
        self.name = name
        self.x = cfg.SCREEN_W * 0.5
        self.y = -80.0
        self.target_y = 110.0
        self.max_hp = 80 + mission * 18
        self.hp = self.max_hp
        self.alive = True
        self.entered = False
        self.phase = 0
        self.timer = 0.0
        self.fire_timer = 1.0
        self.flash = 0.0
        self.vx = 70.0
        self.score = cfg.SCORE_BOSS + mission * 200

    def hitbox(self) -> pg.Rect:
        """Boss collision box."""
        return pg.Rect(int(self.x - 50), int(self.y - 28), 100, 60)

    def update(self, dt: float, player: Player, spawn_bullet: Callable) -> None:
        """Enter, strafe, and escalate fire patterns."""
        if not self.alive:
            return
        self.timer += dt
        self.flash = max(0.0, self.flash - dt)
        self.fire_timer -= dt

        if not self.entered:
            self.y += 60 * dt
            if self.y >= self.target_y:
                self.y = self.target_y
                self.entered = True
            return

        self.x += self.vx * dt
        if self.x < 80 or self.x > cfg.SCREEN_W - 80:
            self.vx *= -1

        # Phase by HP
        ratio = self.hp / self.max_hp
        self.phase = 0 if ratio > 0.66 else 1 if ratio > 0.33 else 2

        if self.fire_timer > 0:
            return

        if self.phase == 0:
            for ang in (-0.4, -0.2, 0, 0.2, 0.4):
                spawn_bullet(
                    Bullet(
                        self.x,
                        self.y + 30,
                        math.sin(ang) * 160,
                        cfg.ENEMY_BULLET_SPEED,
                        False,
                        1,
                    )
                )
            self.fire_timer = 1.1
        elif self.phase == 1:
            for i in range(8):
                a = self.timer * 2 + i * (math.pi * 2 / 8)
                spawn_bullet(
                    Bullet(
                        self.x,
                        self.y,
                        math.cos(a) * cfg.ENEMY_BULLET_SPEED,
                        math.sin(a) * cfg.ENEMY_BULLET_SPEED,
                        False,
                        1,
                        "aim",
                    )
                )
            self.fire_timer = 0.9
        else:
            # Aimed barrages + ring
            dx = player.x - self.x
            dy = player.y - self.y
            dist = max(1.0, math.hypot(dx, dy))
            for spread in (-0.25, 0, 0.25):
                ca = math.cos(spread)
                sa = math.sin(spread)
                vx = (dx / dist) * ca - (dy / dist) * sa
                vy = (dx / dist) * sa + (dy / dist) * ca
                spawn_bullet(
                    Bullet(
                        self.x,
                        self.y + 20,
                        vx * cfg.ENEMY_BULLET_SPEED * 1.2,
                        vy * cfg.ENEMY_BULLET_SPEED * 1.2,
                        False,
                        1,
                        "aim",
                    )
                )
            self.fire_timer = 0.55

    def hurt(self, dmg: int) -> None:
        """Damage boss."""
        self.hp -= dmg
        self.flash = 0.1
        if self.hp <= 0:
            self.alive = False

    def draw(self, surface: pg.Surface) -> None:
        """Render boss and HP bar."""
        if not self.alive and self.hp <= 0:
            return
        sprites.draw_boss_carrier(
            surface,
            self.x,
            self.y,
            hp_ratio=max(0.0, self.hp / self.max_hp),
            flash=self.flash > 0,
        )
        # HP bar
        bar_w = 160
        x0 = cfg.SCREEN_W // 2 - bar_w // 2
        pg.draw.rect(surface, (30, 30, 30), pg.Rect(x0, 36, bar_w, 8))
        pg.draw.rect(
            surface,
            cfg.UI_RED,
            pg.Rect(x0, 36, int(bar_w * max(0.0, self.hp / self.max_hp)), 8),
        )


# ---------------------------------------------------------------------------
# Powerups
# ---------------------------------------------------------------------------
@dataclass
class PowerUp:
    """Floating pickup after kills."""

    x: float
    y: float
    kind: str  # "power" | "bomb" | "shield" | "score"
    alive: bool = True
    vy: float = 50.0
    phase: float = 0.0

    def update(self, dt: float) -> None:
        """Drift downward."""
        self.phase += dt * 4
        self.y += self.vy * dt
        self.x += math.sin(self.phase) * 20 * dt
        if self.y > cfg.SCREEN_H + 20:
            self.alive = False

    def hitbox(self) -> pg.Rect:
        """Pickup rect."""
        return pg.Rect(int(self.x - 10), int(self.y - 10), 20, 20)

    def draw(self, surface: pg.Surface) -> None:
        """Colored token with letter."""
        colors = {
            "power": cfg.UI_GOLD,
            "bomb": (120, 200, 255),
            "shield": (120, 255, 160),
            "score": (255, 160, 80),
        }
        labels = {"power": "P", "bomb": "B", "shield": "S", "score": "$"}
        color = colors.get(self.kind, cfg.UI_WHITE)
        pg.draw.circle(surface, color, (int(self.x), int(self.y)), 9)
        pg.draw.circle(surface, (20, 20, 20), (int(self.x), int(self.y)), 9, 1)
        font = pg.font.SysFont("consolas", 14, bold=True)
        img = font.render(labels.get(self.kind, "?"), True, (20, 20, 20))
        surface.blit(img, img.get_rect(center=(int(self.x), int(self.y))))
