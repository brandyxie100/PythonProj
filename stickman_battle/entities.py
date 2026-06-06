"""Stickman Battle — game entities.

Contains all in-game objects:
  Platform, Tire, SpringBall, Arrow, RifleBullet, MuzzleFlash, ShellCasing,
  BlastParticle, Grenade, HitEffect, AK47Pickup, Stickman (base),
  Player, Enemy.

Stickmen are drawn procedurally using line-segment anatomy and simple
sinusoidal limb-animation driven by a walk phase, so no sprite assets are
needed.
"""

from __future__ import annotations

import math
import random
from typing import Optional

import pygame

import config as c


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ip(x: float, y: float) -> tuple[int, int]:
    """Convert float coords to int pixel tuple."""
    return (int(x), int(y))


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


# ---------------------------------------------------------------------------
# HitEffect — brief orange flash at impact
# ---------------------------------------------------------------------------

class HitEffect(pygame.sprite.Sprite):
    """Short-lived translucent burst drawn at the weapon tip on a hit."""

    LIFE: int = 14  # frames

    def __init__(self, x: int, y: int) -> None:
        """Args:
            x: screen x of impact centre.
            y: screen y of impact centre.
        """
        super().__init__()
        self._total = self.LIFE
        size = 28
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 100, 0, 200), (size // 2, size // 2), size // 2)
        self.rect = self.image.get_rect(center=(x, y))
        self._life = self.LIFE

    def update(self, *_args) -> None:  # type: ignore[override]
        self._life -= 1
        alpha = int(220 * self._life / self._total)
        self.image.set_alpha(max(0, alpha))
        if self._life <= 0:
            self.kill()


# ---------------------------------------------------------------------------
# Platform — static ledge with cyan-edge style
# ---------------------------------------------------------------------------

class Platform(pygame.sprite.Sprite):
    """Static collidable ledge rendered with the dark-blue / cyan aesthetic."""

    def __init__(self, x: int, y: int, w: int, h: int = 18) -> None:
        """Args:
            x: left edge x.
            y: top edge y.
            w: platform width.
            h: platform height.
        """
        super().__init__()
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        # Dark fill
        pygame.draw.rect(self.image, c.PLAT_DARK, (0, 0, w, h))
        # Bright cyan top edge (characteristic look from reference)
        pygame.draw.line(self.image, c.PLAT_EDGE, (0, 0), (w - 1, 0), 3)
        pygame.draw.line(self.image, c.PLAT_GLOW, (0, 1), (w - 1, 1), 1)
        self.rect = self.image.get_rect(topleft=(x, y))


# ---------------------------------------------------------------------------
# Tire — bouncy red circle
# ---------------------------------------------------------------------------

class Tire(pygame.sprite.Sprite):
    """Red circular obstacle that bounces and rolls when hit."""

    R: int = c.TIRE_RADIUS

    def __init__(self, cx: int, cy: int) -> None:
        """Args:
            cx: initial centre x.
            cy: initial centre y.
        """
        super().__init__()
        d = self.R * 2
        self._base = pygame.Surface((d, d), pygame.SRCALPHA)
        pygame.draw.circle(self._base, c.TIRE_COL, (self.R, self.R), self.R)
        pygame.draw.circle(self._base, c.TIRE_IN,  (self.R, self.R), self.R - 6)
        pygame.draw.circle(self._base, c.TIRE_COL, (self.R, self.R), 6)
        # Tread lines for visual spin
        for angle_deg in range(0, 180, 30):
            rad = math.radians(angle_deg)
            px = self.R + math.cos(rad) * (self.R - 3)
            py = self.R + math.sin(rad) * (self.R - 3)
            qx = self.R - math.cos(rad) * (self.R - 3)
            qy = self.R - math.sin(rad) * (self.R - 3)
            pygame.draw.line(self._base, c.TIRE_COL, _ip(px, py), _ip(qx, qy), 2)

        self.image = self._base.copy()
        self.rect = self.image.get_rect(center=(cx, cy))
        self._cx = float(cx)
        self._cy = float(cy)
        self._vx = 0.0
        self._vy = 0.0
        self._angle = 0.0  # rotation in degrees for spin animation

    # ------------------------------------------------------------------
    # Physics
    # ------------------------------------------------------------------

    def apply_impulse(self, ix: float, iy: float) -> None:
        """Add velocity to the tire (called when a stickman hits it).

        Args:
            ix: horizontal impulse.
            iy: vertical impulse.
        """
        self._vx += ix
        self._vy += iy

    def update(self, platforms: list[Platform]) -> None:  # type: ignore[override]
        """Step tire physics: gravity, movement, platform and wall collision.

        Args:
            platforms: list of Platform sprites for landing-collision.
        """
        # Gravity
        self._vy = min(self._vy + c.GRAVITY, c.MAX_FALL)
        self._cx += self._vx
        self._cy += self._vy

        R = self.R

        # Platform top-collision (tire sits on top of platform)
        for plat in platforms:
            pr = plat.rect
            if (self._cx + R > pr.left and self._cx - R < pr.right):
                # Landing on top
                if (self._cy + R >= pr.top and
                        self._cy + R <= pr.top + abs(self._vy) + 4 and
                        self._vy >= 0):
                    self._cy = pr.top - R
                    self._vy = -abs(self._vy) * c.TIRE_BOUNCE
                    if abs(self._vy) < 1.2:
                        self._vy = 0.0
                    self._vx *= 0.88

        # Left / right wall bounce
        if self._cx - R < 0:
            self._cx = float(R)
            self._vx = abs(self._vx) * 0.75
        if self._cx + R > c.SCREEN_W:
            self._cx = float(c.SCREEN_W - R)
            self._vx = -abs(self._vx) * 0.75

        # Floor
        floor_y = c.SCREEN_H - 20
        if self._cy + R >= floor_y:
            self._cy = float(floor_y - R)
            self._vy = -abs(self._vy) * c.TIRE_BOUNCE
            if abs(self._vy) < 1.2:
                self._vy = 0.0
            self._vx *= 0.88

        # Rolling friction
        self._vx *= 0.97

        # Spin visual based on horizontal movement
        self._angle += self._vx * 1.8
        self.image = pygame.transform.rotate(self._base, -self._angle)
        old_center = _ip(self._cx, self._cy)
        self.rect = self.image.get_rect(center=old_center)


# ---------------------------------------------------------------------------
# SpringBall — fixed round booster that launches stickmen upward
# ---------------------------------------------------------------------------

class SpringBall(pygame.sprite.Sprite):
    """Stationary round spring pad that boosts jump height on contact."""

    R: int = c.SPRING_BALL_RADIUS

    def __init__(self, cx: int, cy: int) -> None:
        """Args:
            cx: centre x (fixed).
            cy: centre y (fixed).
        """
        super().__init__()
        d = self.R * 2
        self.image = pygame.Surface((d, d), pygame.SRCALPHA)
        # Outer ball
        pygame.draw.circle(self.image, c.SPRING_COL, (self.R, self.R), self.R)
        pygame.draw.circle(self.image, c.SPRING_DARK, (self.R, self.R), self.R, 3)
        # Coil stripes (spring look)
        for i in range(-2, 3):
            y_off = self.R + i * 5
            pygame.draw.arc(
                self.image, c.SPRING_COIL,
                (4, y_off - 8, d - 8, 16),
                math.radians(200), math.radians(340), 2,
            )
        # Highlight
        pygame.draw.circle(self.image, (255, 255, 200), (self.R - 5, self.R - 5), 4)

        self.rect = self.image.get_rect(center=(cx, cy))
        self._cx = float(cx)
        self._cy = float(cy)
        self._pulse = 0.0

    def update(self) -> None:  # type: ignore[override]
        """Animate a subtle squash-stretch pulse."""
        self._pulse += 0.14

    def draw(self, surf: pygame.Surface) -> None:
        """Draw with a gentle bounce animation.

        Args:
            surf: target surface.
        """
        squash = 1.0 + math.sin(self._pulse) * 0.06
        w = int(self.R * 2 * (1.0 + (1.0 - squash) * 0.5))
        h = int(self.R * 2 * squash)
        scaled = pygame.transform.scale(self.image, (max(w, 1), max(h, 1)))
        rect = scaled.get_rect(center=(int(self._cx), int(self._cy)))
        surf.blit(scaled, rect)

    def try_boost(self, stickman: Stickman) -> bool:
        """Launch the stickman upward if they land on or step on the ball.

        Args:
            stickman: character to boost.

        Returns:
            True if a boost was applied this frame.
        """
        if not stickman.alive:
            return False

        dx = stickman.x - self._cx
        dy = stickman.y - self._cy
        dist = math.hypot(dx, dy)
        touch_dist = self.R + c.STICK_W / 2 + 6

        # Must be near the ball and falling / standing on it
        if dist > touch_dist:
            return False
        if stickman.vy < -2.0:
            return False   # moving up fast — ignore

        # Feet should be at or below ball centre (landing from above)
        if stickman.y > self._cy + self.R + 8:
            return False

        stickman.vy = c.SPRING_BOOST_VEL
        stickman.on_ground = False
        stickman._jumps_left = c.MAX_CONSECUTIVE_JUMPS
        return True


# ---------------------------------------------------------------------------
# Arrow — projectile fired from the bow
# ---------------------------------------------------------------------------

class Arrow:
    """Flying arrow projectile with light gravity arc."""

    HIT_R: int = 8

    def __init__(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        damage: float,
        knockback: float,
        source_x: float,
    ) -> None:
        """Args:
            x: spawn x.
            y: spawn y.
            vx: horizontal speed.
            vy: vertical speed.
            damage: HP damage on hit.
            knockback: push strength.
            source_x: shooter x (for knockback direction).
        """
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.damage = damage
        self.knockback = knockback
        self.source_x = source_x
        self.alive = True
        self._angle = math.atan2(vy, vx)

    def update(self) -> None:
        """Step flight physics; kill when off-screen."""
        self.vy = min(self.vy + c.ARROW_GRAVITY, c.MAX_FALL)
        self.x += self.vx
        self.y += self.vy
        self._angle = math.atan2(self.vy, self.vx)
        if (self.x < -20 or self.x > c.SCREEN_W + 20 or
                self.y < -40 or self.y > c.SCREEN_H + 40):
            self.alive = False

    def draw(self, surf: pygame.Surface) -> None:
        """Draw arrow shaft and head.

        Args:
            surf: target surface.
        """
        if not self.alive:
            return
        length = 18
        ux = math.cos(self._angle)
        uy = math.sin(self._angle)
        tail_x = self.x - ux * length
        tail_y = self.y - uy * length
        pygame.draw.line(surf, (210, 180, 120), _ip(tail_x, tail_y), _ip(self.x, self.y), 2)
        tip_x = self.x + ux * 6
        tip_y = self.y + uy * 6
        pygame.draw.polygon(
            surf, (200, 200, 210),
            [_ip(self.x, self.y), _ip(tip_x - uy * 4, tip_y + ux * 4),
             _ip(tip_x + uy * 4, tip_y - ux * 4)],
        )

    def try_hit(self, target: Stickman) -> bool:
        """Damage target if arrow tip overlaps their body.

        Args:
            target: stickman to test.

        Returns:
            True if a hit was registered (arrow is consumed).
        """
        if not self.alive or not target.alive:
            return False
        cx = target.x
        cy = target.y - target.TOTAL_H / 2
        if math.hypot(self.x - cx, self.y - cy) > self.HIT_R + 24:
            return False
        # Keep bow attacks non-lethal by design: arrows injure but never finish.
        non_lethal_damage = min(self.damage, max(0.0, target.health - 1.0))
        if non_lethal_damage > 0.0:
            target.take_damage(non_lethal_damage, source_x=self.source_x)
        target.vx += (1 if target.x >= self.source_x else -1) * self.knockback
        target.vy -= 1.5
        self.alive = False
        return True


# ---------------------------------------------------------------------------
# RifleBullet — fast AK-47 round (damage matches arrows)
# ---------------------------------------------------------------------------

class RifleBullet:
    """Straight-travelling rifle bullet with minimal drop."""

    HIT_R: int = 6

    def __init__(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        damage: float,
        knockback: float,
        source_x: float,
    ) -> None:
        """Args:
            x: spawn x.
            y: spawn y.
            vx: horizontal speed.
            vy: vertical speed.
            damage: HP damage (same as arrow).
            knockback: push strength.
            source_x: shooter x for knockback direction.
        """
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.damage = damage
        self.knockback = knockback
        self.source_x = source_x
        self.alive = True

    def update(self) -> None:
        """Step bullet flight."""
        self.vy = min(self.vy + c.AK47_BULLET_GRAVITY, c.MAX_FALL)
        self.x += self.vx
        self.y += self.vy
        if (self.x < -20 or self.x > c.SCREEN_W + 20 or
                self.y < -40 or self.y > c.SCREEN_H + 40):
            self.alive = False

    def draw(self, surf: pygame.Surface) -> None:
        """Draw bright tracer streak.

        Args:
            surf: target surface.
        """
        if not self.alive:
            return
        ux = 1.0 if self.vx >= 0 else -1.0
        tail_x = self.x - ux * 14
        pygame.draw.line(surf, (255, 240, 150), _ip(tail_x, self.y), _ip(self.x, self.y), 3)
        pygame.draw.circle(surf, (255, 255, 220), _ip(self.x, self.y), 2)

    def try_hit(self, target: Stickman) -> bool:
        """Damage target on body overlap.

        Args:
            target: stickman to test.

        Returns:
            True if hit registered (bullet consumed).
        """
        if not self.alive or not target.alive:
            return False
        cx = target.x
        cy = target.y - target.TOTAL_H / 2
        if math.hypot(self.x - cx, self.y - cy) > self.HIT_R + 24:
            return False
        target.take_damage(self.damage, source_x=self.source_x)
        target.vx += (1 if target.x >= self.source_x else -1) * self.knockback
        target.vy -= 1.2
        self.alive = False
        return True


# ---------------------------------------------------------------------------
# MuzzleFlash — brief burst at rifle muzzle when firing
# ---------------------------------------------------------------------------

class MuzzleFlash:
    """Short-lived muzzle flash for AK-47 firing animation."""

    def __init__(self, x: float, y: float, facing: int) -> None:
        """Args:
            x: muzzle x.
            y: muzzle y.
            facing: 1 right, -1 left.
        """
        self.x = x
        self.y = y
        self.facing = facing
        self._life = 6
        self._max = 6

    @property
    def alive(self) -> bool:
        return self._life > 0

    def update(self) -> None:
        self._life -= 1

    def draw(self, surf: pygame.Surface) -> None:
        """Render star-shaped flash.

        Args:
            surf: target surface.
        """
        if not self.alive:
            return
        t = self._life / self._max
        size = int(10 + (1.0 - t) * 8)
        alpha = int(220 * t)
        flash = pygame.Surface((size * 3, size * 2), pygame.SRCALPHA)
        cx, cy = size + 4, size
        col = (*c.AK47_MUZZLE_FLASH, alpha)
        # Star burst
        pts = []
        for i in range(8):
            ang = i * (math.tau / 8)
            r = size if i % 2 == 0 else size * 0.45
            pts.append((cx + math.cos(ang) * r, cy + math.sin(ang) * r * 0.6))
        pygame.draw.polygon(flash, col, [_ip(*p) for p in pts])
        pygame.draw.circle(flash, (255, 255, 255, min(255, alpha + 30)), (cx, cy), max(2, size // 3))
        rect = flash.get_rect(center=_ip(self.x, self.y))
        if self.facing < 0:
            flash = pygame.transform.flip(flash, True, False)
            rect = flash.get_rect(center=_ip(self.x, self.y))
        surf.blit(flash, rect)


# ---------------------------------------------------------------------------
# ShellCasing — ejected brass casing for firing feedback
# ---------------------------------------------------------------------------

class ShellCasing:
    """Small casing particle ejected sideways when a round is fired."""

    def __init__(self, x: float, y: float, facing: int) -> None:
        """Args:
            x: ejection point x.
            y: ejection point y.
            facing: shooter facing.
        """
        self.x = x
        self.y = y
        self.vx = -facing * random.uniform(2.0, 5.0)
        self.vy = random.uniform(-4.0, -1.5)
        self._life = random.randint(18, 28)
        self._rot = random.uniform(0, math.tau)

    @property
    def alive(self) -> bool:
        return self._life > 0

    def update(self) -> None:
        self.vy += 0.18
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.98
        self._rot += 0.35
        self._life -= 1

    def draw(self, surf: pygame.Surface) -> None:
        """Draw small brass rectangle.

        Args:
            surf: target surface.
        """
        if not self.alive:
            return
        w, h = 5, 2
        casing = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(casing, c.AK47_CASING, (0, 0, w, h))
        rotated = pygame.transform.rotate(casing, math.degrees(self._rot))
        surf.blit(rotated, rotated.get_rect(center=_ip(self.x, self.y)))


# ---------------------------------------------------------------------------
# BlastParticle — spark/debris from grenade explosions
# ---------------------------------------------------------------------------

class BlastParticle:
    """Single ember particle ejected from a grenade blast."""

    def __init__(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        color: tuple[int, int, int],
        size: float,
        life: int,
    ) -> None:
        """Args:
            x: spawn x.
            y: spawn y.
            vx: horizontal velocity.
            vy: vertical velocity.
            color: RGB spark colour.
            size: initial radius in pixels.
            life: frames until fade-out.
        """
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.size = size
        self._life = life
        self._max_life = life

    @property
    def alive(self) -> bool:
        return self._life > 0

    def update(self) -> None:
        """Step particle motion and decay."""
        self.vy += 0.12
        self.vx *= 0.97
        self.vy *= 0.98
        self.x += self.vx
        self.y += self.vy
        self._life -= 1

    def draw(self, surf: pygame.Surface) -> None:
        """Render glowing spark with alpha fade.

        Args:
            surf: target surface.
        """
        if not self.alive:
            return
        t = self._life / self._max_life
        radius = max(1, int(self.size * (0.4 + 0.6 * t)))
        alpha = int(255 * t)
        glow = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
        cx, cy = radius * 2, radius * 2
        pygame.draw.circle(glow, (*self.color, alpha), (cx, cy), radius)
        pygame.draw.circle(
            glow, (255, 255, 220, min(255, alpha + 40)), (cx, cy), max(1, radius // 2)
        )
        surf.blit(glow, glow.get_rect(center=_ip(self.x, self.y)))


# ---------------------------------------------------------------------------
# Grenade — arcing explosive projectile
# ---------------------------------------------------------------------------

class Grenade:
    """Throwable grenade with fuse timer and area-of-effect explosion."""

    def __init__(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        owner_id: int,
        damage: float = c.GRENADE_DAMAGE,
    ) -> None:
        """Args:
            x: initial x.
            y: initial y.
            vx: horizontal launch velocity.
            vy: vertical launch velocity.
            owner_id: id() of thrower (used for friendly-fire skip).
            damage: damage dealt at blast center.
        """
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.owner_id = owner_id
        self.damage = damage
        self._fuse = c.GRENADE_FUSE_F
        self._exploded = False
        self._explosion_life = 0
        self._just_exploded = False
        self._particles: list[BlastParticle] = []
        self.alive = True

    @property
    def just_exploded(self) -> bool:
        """True on the exact frame the fuse pops."""
        return self._just_exploded

    @property
    def exploded(self) -> bool:
        """True once explosion has started."""
        return self._exploded

    def update(self, platforms: list[Platform]) -> None:
        """Advance grenade movement and fuse.

        Args:
            platforms: collision ledges.
        """
        self._just_exploded = False
        if not self.alive:
            return

        if self._exploded:
            self._explosion_life -= 1
            for particle in self._particles:
                particle.update()
            self._particles = [p for p in self._particles if p.alive]
            if self._explosion_life <= 0 and not self._particles:
                self.alive = False
            return

        self._fuse -= 1
        if self._fuse <= 0:
            self._explode()
            return

        self.vy = min(self.vy + c.GRAVITY, c.MAX_FALL)
        self.vx *= c.GRENADE_AIR_DRAG
        self.x += self.vx
        self.y += self.vy

        # Platform/floor bounces.
        for plat in platforms:
            pr = plat.rect
            if not (pr.left - 8 <= self.x <= pr.right + 8):
                continue
            if self.y >= pr.top and self.y <= pr.top + abs(self.vy) + 6 and self.vy > 0:
                self.y = pr.top
                self.vy = -abs(self.vy) * c.GRENADE_BOUNCE
                self.vx *= 0.85

        floor_y = c.SCREEN_H - 20
        if self.y >= floor_y:
            self.y = floor_y
            self.vy = -abs(self.vy) * c.GRENADE_BOUNCE
            self.vx *= 0.8

        if self.x <= 0 or self.x >= c.SCREEN_W:
            self.x = max(0, min(c.SCREEN_W, self.x))
            self.vx = -self.vx * 0.65

    def _spawn_blast_particles(self) -> None:
        """Emit red/orange sparks radiating from the blast center."""
        self._particles = []
        for _ in range(c.GRENADE_BLAST_PARTICLE_COUNT):
            ang = random.uniform(0, math.tau)
            speed = random.uniform(4.0, 14.0)
            col = random.choice(c.GRENADE_PARTICLE_COLORS)
            life = random.randint(14, 28)
            size = random.uniform(2.5, 6.5)
            self._particles.append(
                BlastParticle(
                    self.x, self.y,
                    math.cos(ang) * speed,
                    math.sin(ang) * speed - random.uniform(1.0, 4.0),
                    col, size, life,
                )
            )

    def _explode(self) -> None:
        """Trigger explosion state and particle burst."""
        self._exploded = True
        self._just_exploded = True
        self._explosion_life = c.GRENADE_EXPLOSION_LIFE_F
        self.vx = 0.0
        self.vy = 0.0
        self._spawn_blast_particles()

    def apply_explosion(self, targets: list["Stickman"]) -> list["Stickman"]:
        """Apply AoE damage/knockback once at explosion.

        Args:
            targets: all stickmen in scene.

        Returns:
            Stickmen that were hit by this explosion.
        """
        if not self._just_exploded:
            return []

        hits: list["Stickman"] = []
        for target in targets:
            if not target.alive or id(target) == self.owner_id:
                continue
            cx = target.x
            cy = target.y - target.TOTAL_H / 2
            dist = math.hypot(cx - self.x, cy - self.y)
            if dist > c.GRENADE_RADIUS:
                continue
            # Linear falloff so center hits harder.
            scale = 1.0 - (dist / c.GRENADE_RADIUS)
            dmg = self.damage * (0.35 + 0.65 * scale)
            target.take_damage(dmg, source_x=self.x)
            push = 4.5 + 5.5 * scale
            target.vx += (1 if cx >= self.x else -1) * push
            target.vy -= 2.0 + 4.0 * scale
            hits.append(target)
        return hits

    def draw(self, surf: pygame.Surface) -> None:
        """Draw grenade body or explosion pulse.

        Args:
            surf: target surface.
        """
        if not self.alive:
            return
        if not self._exploded:
            pygame.draw.circle(surf, c.GRENADE_COL, _ip(self.x, self.y), 7)
            pygame.draw.circle(surf, c.GRENADE_PIN, _ip(self.x + 3, self.y - 5), 2)
            # Fuse blink indicator.
            if (self._fuse // 8) % 2 == 0:
                pygame.draw.circle(surf, (255, 220, 120), _ip(self.x, self.y - 9), 2)
            return

        # Layered red/orange fireball — vivid multi-ring blast.
        total = float(c.GRENADE_EXPLOSION_LIFE_F)
        t = 1.0 - (self._explosion_life / total)
        cx, cy = _ip(self.x, self.y)

        r_smoke = int(18 + c.GRENADE_RADIUS * t * 1.15)
        r_outer = int(14 + c.GRENADE_RADIUS * t)
        r_mid = int(r_outer * 0.72)
        r_inner = int(r_outer * 0.48)
        r_core = max(4, int(r_outer * 0.22))

        pad = r_smoke + 8
        boom = pygame.Surface((pad * 2, pad * 2), pygame.SRCALPHA)
        center = (pad, pad)

        # Outer ember smoke (deep red, soft edge).
        pygame.draw.circle(boom, (*c.GRENADE_EXPLODE_SMOKE, 75), center, r_smoke)
        pygame.draw.circle(boom, (*c.GRENADE_EXPLODE_OUTER, 130), center, r_outer)
        pygame.draw.circle(boom, (*c.GRENADE_EXPLODE_MID, 185), center, r_mid)
        pygame.draw.circle(boom, (*c.GRENADE_EXPLODE_INNER, 220), center, r_inner)
        pygame.draw.circle(boom, (*c.GRENADE_EXPLODE_CORE, 245), center, r_core)

        # Early-frame white-hot flash for extra punch.
        if t < 0.25:
            flash_r = int(r_core * (1.6 - t * 2.0))
            pygame.draw.circle(boom, (255, 255, 255, 200), center, max(2, flash_r))

        surf.blit(boom, boom.get_rect(center=(cx, cy)))

        # Flying sparks on top of the fireball.
        for particle in self._particles:
            particle.draw(surf)


# ---------------------------------------------------------------------------
# BowPickup — timed bow + arrow set with shiny spawn animation
# ---------------------------------------------------------------------------

class BowPickup:
    """World pickup: bow plus 20 arrows, despawns after a 10-second countdown."""

    def __init__(self, x: float, y: float) -> None:
        """Args:
            x: centre x on the arena.
            y: feet-level y (pickup floats above this point).
        """
        self.x = x
        self.y = y - 36          # float above ground
        self._timer = c.BOW_PICKUP_DURATION_F
        self._shine_phase = random.uniform(0, math.tau)
        self._bob_phase = random.uniform(0, math.tau)

    @property
    def active(self) -> bool:
        """Return True while the pickup is still on the field."""
        return self._timer > 0

    @property
    def seconds_left(self) -> int:
        """Whole seconds remaining before despawn."""
        return max(0, math.ceil(self._timer / c.FPS))

    def update(self) -> None:
        """Tick countdown and animation phases."""
        self._timer -= 1
        self._shine_phase += 0.12
        self._bob_phase += 0.08

    def try_collect(self, player: Player) -> bool:
        """Give the bow set to the player if they touch the pickup.

        Args:
            player: the human stickman.

        Returns:
            True if collected this frame.
        """
        if not self.active:
            return False
        bob = math.sin(self._bob_phase) * 4
        cy = self.y + bob
        dist = math.hypot(player.x - self.x, player.y - cy - 20)
        if dist > c.BOW_PICKUP_RADIUS + c.STICK_W:
            return False
        player.equip_bow(c.BOW_ARROWS_PER_SET)
        self._timer = 0
        return True

    def draw(self, surf: pygame.Surface) -> None:
        """Render shiny bow pickup with countdown.

        Args:
            surf: target surface.
        """
        if not self.active:
            return

        bob = math.sin(self._bob_phase) * 4
        cx, cy = int(self.x), int(self.y + bob)
        pulse = 0.5 + 0.5 * math.sin(self._shine_phase * 2)

        # Outer glow rings (shiny animation)
        for i in range(3):
            r = int(c.BOW_PICKUP_RADIUS + 10 + i * 8 + pulse * 6)
            alpha = int(90 - i * 25)
            glow = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*c.BOW_GLOW, alpha), (r, r), r)
            surf.blit(glow, glow.get_rect(center=(cx, cy)))

        # Rotating sparkles
        for i in range(6):
            ang = self._shine_phase + i * (math.tau / 6)
            sx = cx + math.cos(ang) * (c.BOW_PICKUP_RADIUS + 6)
            sy = cy + math.sin(ang) * (c.BOW_PICKUP_RADIUS + 6)
            sparkle_col = (255, 255, 200) if i % 2 == 0 else (255, 220, 80)
            pygame.draw.circle(surf, sparkle_col, _ip(sx, sy), 3)

        # Bow shape
        bow_rect = pygame.Rect(cx - 14, cy - 18, 28, 36)
        pygame.draw.arc(surf, c.BOW_COL, bow_rect, math.radians(70), math.radians(290), 4)
        pygame.draw.line(surf, c.BOW_STRING, (cx, cy - 16), (cx, cy + 16), 2)

        # Arrow bundle indicator
        pygame.draw.line(surf, (210, 180, 120), (cx + 8, cy - 10), (cx + 22, cy - 4), 2)
        pygame.draw.line(surf, (210, 180, 120), (cx + 8, cy), (cx + 20, cy + 2), 2)

        # Label + countdown
        font = pygame.font.SysFont("Arial", 16, bold=True)
        label = font.render(f"Bow x{c.BOW_ARROWS_PER_SET}", True, c.WHITE)
        surf.blit(label, label.get_rect(midbottom=(cx, cy - 34)))

        timer_font = pygame.font.SysFont("Arial", 20, bold=True)
        secs = self.seconds_left
        timer_col = (255, 220, 80) if secs <= 3 else (180, 230, 255)
        timer_txt = timer_font.render(f"{secs}s", True, timer_col)
        surf.blit(timer_txt, timer_txt.get_rect(midtop=(cx, cy + 26)))


# ---------------------------------------------------------------------------
# AK47Pickup — spawns 30 s after match start, 30 rounds preloaded
# ---------------------------------------------------------------------------

class AK47Pickup:
    """World pickup: AK-47 rifle with 30 rounds. Stays until collected."""

    def __init__(self, x: float, y: float) -> None:
        """Args:
            x: centre x on the arena.
            y: feet-level y (pickup floats above).
        """
        self.x = x
        self.y = y - 36
        self._shine_phase = random.uniform(0, math.tau)
        self._bob_phase = random.uniform(0, math.tau)
        self.active = True

    def update(self) -> None:
        """Animate shiny pulse."""
        self._shine_phase += 0.14
        self._bob_phase += 0.09

    def try_collect(self, player: "Player") -> bool:
        """Give AK-47 to player on contact.

        Args:
            player: human stickman.

        Returns:
            True if collected.
        """
        if not self.active:
            return False
        bob = math.sin(self._bob_phase) * 4
        cy = self.y + bob
        dist = math.hypot(player.x - self.x, player.y - cy - 20)
        if dist > c.AK47_PICKUP_RADIUS + c.STICK_W:
            return False
        player.equip_ak47(c.AK47_ROUNDS_PER_PICKUP)
        self.active = False
        return True

    def draw(self, surf: pygame.Surface) -> None:
        """Render glowing AK-47 pickup.

        Args:
            surf: target surface.
        """
        if not self.active:
            return

        bob = math.sin(self._bob_phase) * 4
        cx, cy = int(self.x), int(self.y + bob)
        pulse = 0.5 + 0.5 * math.sin(self._shine_phase * 2)

        for i in range(3):
            r = int(c.AK47_PICKUP_RADIUS + 8 + i * 7 + pulse * 5)
            alpha = int(85 - i * 22)
            glow = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*c.AK47_GLOW, alpha), (r, r), r)
            surf.blit(glow, glow.get_rect(center=(cx, cy)))

        for i in range(5):
            ang = self._shine_phase + i * (math.tau / 5)
            sx = cx + math.cos(ang) * (c.AK47_PICKUP_RADIUS + 5)
            sy = cy + math.sin(ang) * (c.AK47_PICKUP_RADIUS + 5)
            pygame.draw.circle(surf, c.AK47_SHINE, _ip(sx, sy), 3)

        # Rifle silhouette on ground
        pygame.draw.line(surf, c.AK47_WOOD, (cx - 22, cy + 4), (cx - 8, cy + 2), 4)
        pygame.draw.line(surf, c.AK47_METAL, (cx - 8, cy + 2), (cx + 24, cy), 4)
        pygame.draw.rect(surf, c.AK47_COL, (cx - 2, cy + 2, 8, 12))
        pygame.draw.line(surf, c.AK47_METAL, (cx + 24, cy), (cx + 32, cy - 1), 3)

        font = pygame.font.SysFont("Arial", 16, bold=True)
        label = font.render(f"AK-47 x{c.AK47_ROUNDS_PER_PICKUP}", True, c.WHITE)
        surf.blit(label, label.get_rect(midbottom=(cx, cy - 36)))


# ---------------------------------------------------------------------------
# Stickman — base class (drawn procedurally, no sprite images)
# ---------------------------------------------------------------------------

class Stickman:
    """Base class for all stickmen (player and enemies).

    Drawing uses a parametric limb system.  Every frame, _joints() computes
    the pixel positions of every body segment based on the current walk_phase
    and attack_phase.  Physics is Euler-step with simple AABB platform landing.

    States: IDLE, WALK, JUMP, ATTACK, HURT, DEAD.
    """

    # ---- Anatomy (class constants, can be overridden per subclass) ----
    HEAD_R   = c.HEAD_R
    NECK_H   = c.NECK_H
    TORSO_H  = c.TORSO_H
    U_ARM    = c.UPPER_ARM
    L_ARM    = c.LOWER_ARM
    U_LEG    = c.UPPER_LEG
    L_LEG    = c.LOWER_LEG
    LW       = c.LINE_W
    TOTAL_H  = c.STICK_H
    TOTAL_W  = c.STICK_W

    # ---- State labels ----
    ST_IDLE   = "idle"
    ST_WALK   = "walk"
    ST_JUMP   = "jump"
    ST_ATTACK = "attack"
    ST_HURT   = "hurt"
    ST_DEAD   = "dead"

    def __init__(
        self,
        x: float,
        y: float,
        color: tuple[int, int, int],
        health: float,
        weapon_name: str,
    ) -> None:
        """Args:
            x: initial centre-x (feet level).
            y: initial feet-y.
            color: RGB fill colour for this stickman.
            health: starting HP.
            weapon_name: key into config.WEAPONS.
        """
        self.x = x          # centre-x
        self.y = y          # feet-y
        self.color = color
        self.max_health = health
        self.health = health
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.facing = 1     # 1 = right, −1 = left
        self.walk_phase = 0.0
        self.state = self.ST_IDLE

        # Attack tracking — full 360° weapon spin
        self.attack_phase = 0.0       # 0 → 1 over one full rotation
        self.attack_speed = c.ATTACK_SPIN_SPEED
        self._attack_cd = 0           # remaining cooldown frames
        self._hit_targets: set[int] = set()  # ids hit in this swing

        # Consecutive jumps (ground + mid-air)
        self._jumps_left = c.MAX_CONSECUTIVE_JUMPS

        # Grenades (everyone gets the same match allotment).
        self.grenades_left = c.GRENADES_PER_MATCH
        self._grenade_cd = 0

        # Rifle firing animation (AK-47 recoil flash).
        self._fire_flash_frames = 0

        # Hurt flash
        self._hurt_frames = 0

        # Weapon
        self.weapon_name = weapon_name
        self.weapon = c.WEAPONS[weapon_name]

    # ------------------------------------------------------------------
    # Rect — used for collision queries
    # ------------------------------------------------------------------

    @property
    def rect(self) -> pygame.Rect:
        """Bounding rect (top-left origin, derived from feet position)."""
        return pygame.Rect(
            int(self.x - self.TOTAL_W / 2),
            int(self.y - self.TOTAL_H),
            self.TOTAL_W,
            self.TOTAL_H,
        )

    @property
    def alive(self) -> bool:
        return self.state != self.ST_DEAD

    # ------------------------------------------------------------------
    # Joint computation
    # ------------------------------------------------------------------

    def _joints(self) -> dict:
        """Compute pixel coords of every drawn joint for the current frame.

        Returns:
            Dict mapping joint names to (float, float) pixel positions.
        """
        x, y = self.x, self.y   # feet
        ph   = self.walk_phase

        # ---- Vertical chain ----
        hip_y      = y  - (self.U_LEG + self.L_LEG)
        torso_bot  = hip_y
        torso_top  = hip_y - self.TORSO_H
        neck_y     = torso_top
        head_cy    = neck_y - self.HEAD_R - self.NECK_H
        shoulder_y = torso_top + 8   # slightly below neck

        # ---- Legs — opposite-phase pendulum swing ----
        leg_amp = 0.50   # amplitude in radians
        r_leg_ang = self.facing * math.sin(ph) * leg_amp
        l_leg_ang = self.facing * math.sin(ph + math.pi) * leg_amp

        def _leg_pts(ang: float) -> tuple[tuple, tuple]:
            """Return (knee, foot) for a leg with given upper angle."""
            kx = x + math.sin(ang) * self.U_LEG
            ky = torso_bot + math.cos(ang) * self.U_LEG
            # Lower leg follows same direction, bent slightly forward
            fx = kx + math.sin(ang * 0.65) * self.L_LEG
            fy = ky + math.cos(ang * 0.65) * self.L_LEG
            return (kx, ky), (fx, fy)

        r_knee, r_foot = _leg_pts(r_leg_ang)
        l_knee, l_foot = _leg_pts(l_leg_ang)

        # ---- Arms — opposite to legs; weapon arm spins 360° during attack ----
        arm_swing = -self.facing * math.sin(ph) * 0.35

        if self.state == self.ST_ATTACK:
            # Full 360° rotation around the shoulder while attacking
            spin = self.attack_phase * 2.0 * math.pi
            w_ang = spin * self.facing
            o_ang = spin * self.facing + math.pi * 0.85
        elif self.weapon_name == "ak47":
            # Two-hand rifle pose with recoil kick while firing
            recoil = self._fire_flash_frames * math.radians(9.0)
            w_ang = self.facing * (math.radians(-12.0) - recoil) + arm_swing
            o_ang = -self.facing * math.radians(28.0) - arm_swing * 0.5
        else:
            w_ang = self.facing * math.radians(10.0) + arm_swing
            o_ang = -self.facing * math.radians(10.0) - arm_swing

        def _arm_pts(ang: float) -> tuple[tuple, tuple]:
            ex = x + math.sin(ang) * self.U_ARM
            ey = shoulder_y + math.cos(ang) * self.U_ARM
            hx = ex + math.sin(ang) * self.L_ARM
            hy = ey + math.cos(ang) * self.L_ARM
            return (ex, ey), (hx, hy)

        w_elbow, w_hand  = _arm_pts(w_ang)
        o_elbow, o_hand  = _arm_pts(o_ang)

        return {
            "head":       (x, head_cy),
            "torso_top":  (x, torso_top),
            "torso_bot":  (x, torso_bot),
            "shoulder":   (x, shoulder_y),
            "r_knee": r_knee, "r_foot": r_foot,
            "l_knee": l_knee, "l_foot": l_foot,
            "w_ang":  w_ang,
            "w_elbow": w_elbow, "w_hand": w_hand,
            "o_elbow": o_elbow, "o_hand": o_hand,
        }

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw(self, surf: pygame.Surface) -> None:
        """Render the stickman onto surf.

        Args:
            surf: target pygame Surface.
        """
        if self.state == self.ST_DEAD:
            return

        j   = self._joints()
        col = (255, 255, 255) if (self._hurt_frames > 0 and (self._hurt_frames // 3) % 2) else self.color
        lw  = self.LW

        def pts(*coords: tuple) -> list[tuple[int, int]]:
            return [_ip(*p) for p in coords]

        # Back leg (slightly offset so it reads as behind)
        pygame.draw.lines(surf, col, False, pts(j["torso_bot"], j["l_knee"], j["l_foot"]), lw)
        # Back arm
        pygame.draw.lines(surf, col, False, pts(j["shoulder"], j["o_elbow"], j["o_hand"]), lw)
        # Torso
        pygame.draw.line(surf, col, _ip(*j["torso_top"]), _ip(*j["torso_bot"]), lw)
        # Front leg
        pygame.draw.lines(surf, col, False, pts(j["torso_bot"], j["r_knee"], j["r_foot"]), lw)
        # Weapon arm (front)
        pygame.draw.lines(surf, col, False, pts(j["shoulder"], j["w_elbow"], j["w_hand"]), lw)
        # Head
        pygame.draw.circle(surf, col, _ip(*j["head"]), self.HEAD_R, lw)

        # Stylised eyes (3-D-glasses vibe, like the reference screenshot)
        hx, hy = j["head"]
        pygame.draw.circle(surf, (255, 50,  50), _ip(hx + self.facing * 4,     hy - 1), 3)
        pygame.draw.circle(surf, (50,  80, 255), _ip(hx + self.facing * 4 - self.facing * 8, hy - 1), 3)

        # Weapon
        self._draw_weapon(surf, j)

        # Health bar
        self._draw_hp(surf, j["head"])

    def _draw_weapon(self, surf: pygame.Surface, j: dict) -> None:
        """Render the held weapon extending from the weapon hand.

        Args:
            surf: target surface.
            j: joint dict from _joints().
        """
        wx, wy = j["w_hand"]
        ang    = j["w_ang"]           # weapon arm angle
        reach  = self.weapon["reach"]
        col    = self.weapon["color"]
        gcol   = self.weapon["guard_color"]
        name   = self.weapon_name

        # Weapon extends in the same direction as the arm
        ux = math.sin(ang)
        uy = math.cos(ang)

        tip_x = wx + ux * reach
        tip_y = wy + uy * reach

        if name == "sword":
            # Long thin blade
            pygame.draw.line(surf, col, _ip(wx, wy), _ip(tip_x, tip_y), 4)
            # Guard (crosspiece near hand)
            gx, gy = wx + ux * 4, wy + uy * 4
            pygame.draw.line(surf, gcol,
                             _ip(gx - uy * 9, gy + ux * 9),
                             _ip(gx + uy * 9, gy - ux * 9), 3)

        elif name == "hammer":
            # Handle (shorter, thicker)
            mid_x, mid_y = wx + ux * reach * 0.75, wy + uy * reach * 0.75
            pygame.draw.line(surf, gcol, _ip(wx, wy), _ip(mid_x, mid_y), 4)
            # Block head
            hw, hh = 10, 8
            corners = [
                (tip_x - uy * hw + ux * hh, tip_y + ux * hw + uy * hh),
                (tip_x + uy * hw + ux * hh, tip_y - ux * hw + uy * hh),
                (tip_x + uy * hw - ux * hh, tip_y - ux * hw - uy * hh),
                (tip_x - uy * hw - ux * hh, tip_y + ux * hw - uy * hh),
            ]
            pygame.draw.polygon(surf, col, [_ip(*p) for p in corners])
            pygame.draw.polygon(surf, gcol, [_ip(*p) for p in corners], 2)

        elif name == "pickaxe":
            # Handle
            mid_x, mid_y = wx + ux * reach * 0.8, wy + uy * reach * 0.8
            pygame.draw.line(surf, gcol, _ip(wx, wy), _ip(mid_x, mid_y), 4)
            # Pick head (asymmetric triangle)
            tip2_x = tip_x - uy * 12
            tip2_y = tip_y + ux * 12
            base_x = tip_x + uy * 6
            base_y = tip_y - ux * 6
            pick_pts = [_ip(mid_x, mid_y), _ip(tip2_x, tip2_y), _ip(base_x, base_y)]
            pygame.draw.polygon(surf, col, pick_pts)
            pygame.draw.polygon(surf, gcol, pick_pts, 2)

        elif name == "bow":
            # Curved bow held in weapon hand
            hand_x, hand_y = int(wx), int(wy)
            bow_h = 28
            perp_x = -uy * 10 * self.facing
            perp_y = ux * 10 * self.facing
            top = (hand_x + perp_x, hand_y - bow_h // 2 + perp_y * 0.3)
            bot = (hand_x + perp_x, hand_y + bow_h // 2 + perp_y * 0.3)
            back = (hand_x - self.facing * 6, hand_y)
            pygame.draw.lines(surf, col, False, [_ip(*top), _ip(*back), _ip(*bot)], 3)
            pygame.draw.line(surf, gcol, _ip(*top), _ip(*bot), 1)
            # Nocked arrow when idle
            if self.state != self.ST_ATTACK:
                nock_x = hand_x + self.facing * reach * 0.6
                nock_y = hand_y
                tip_n = (nock_x + self.facing * 14, nock_y)
                pygame.draw.line(surf, (210, 180, 120), _ip(nock_x, nock_y), _ip(*tip_n), 2)

        elif name == "ak47":
            # Stock → receiver → barrel + curved magazine
            stock_x = wx - self.facing * 18
            stock_y = wy + 4
            barrel_end_x = wx + self.facing * reach
            barrel_end_y = wy - 2
            pygame.draw.line(surf, gcol, _ip(stock_x, stock_y), _ip(wx, wy), 4)
            pygame.draw.line(surf, col, _ip(wx, wy), _ip(barrel_end_x, barrel_end_y), 4)
            # Magazine
            mag_x = wx + self.facing * 6
            mag_pts = [
                _ip(mag_x, wy + 2),
                _ip(mag_x + self.facing * 6, wy + 14),
                _ip(mag_x + self.facing * 2, wy + 16),
                _ip(mag_x - self.facing * 2, wy + 4),
            ]
            pygame.draw.polygon(surf, c.AK47_COL, mag_pts)
            # Muzzle brake
            pygame.draw.line(
                surf, c.AK47_METAL,
                _ip(barrel_end_x, barrel_end_y - 3),
                _ip(barrel_end_x, barrel_end_y + 3), 2,
            )

    def muzzle_position(self) -> tuple[float, float]:
        """Return world position of the current weapon muzzle.

        Returns:
            (muzzle_x, muzzle_y).
        """
        j = self._joints()
        wx, wy = j["w_hand"]
        ang = j["w_ang"]
        reach = self.weapon["reach"]
        return wx + math.sin(ang) * reach, wy + math.cos(ang) * reach

    def _draw_hp(self, surf: pygame.Surface, head: tuple) -> None:
        """Draw health bar above the stickman's head.

        Args:
            surf: target surface.
            head: (x, y) of head centre.
        """
        hx, hy = head
        bw, bh = 40, 5
        ratio  = max(0.0, self.health / self.max_health)
        bx     = int(hx - bw // 2)
        by     = int(hy - self.HEAD_R - 14)
        pygame.draw.rect(surf, c.HP_RED,    (bx, by, bw, bh))
        pygame.draw.rect(surf, c.HP_GREEN,  (bx, by, int(bw * ratio), bh))
        pygame.draw.rect(surf, c.HP_BORDER, (bx, by, bw, bh), 1)

    # ------------------------------------------------------------------
    # Physics helpers
    # ------------------------------------------------------------------

    def _apply_gravity(self) -> None:
        self.vy = min(self.vy + c.GRAVITY, c.MAX_FALL)

    def _move(self) -> None:
        self.x += self.vx
        self.y += self.vy

    def _collide_platforms(self, platforms: list[Platform]) -> None:
        """Land on top of any platform the stickman falls onto.

        Args:
            platforms: all Platform sprites in the scene.
        """
        self.on_ground = False
        half_w = self.TOTAL_W / 2
        for plat in platforms:
            pr = plat.rect
            if self.x + half_w <= pr.left or self.x - half_w >= pr.right:
                continue
            # Check crossing platform top from above this frame
            prev_feet = self.y - self.vy      # feet position last frame
            if prev_feet <= pr.top + 2 and self.y >= pr.top and self.vy >= 0:
                self.y  = float(pr.top)
                self.vy = 0.0
                self.on_ground = True
                self._jumps_left = c.MAX_CONSECUTIVE_JUMPS

    def _collide_screen(self) -> None:
        """Bounce off left/right walls; die if falling out of bottom."""
        hw = self.TOTAL_W / 2
        if self.x - hw < 0:
            self.x  = hw
            self.vx = abs(self.vx) * 0.3
        if self.x + hw > c.SCREEN_W:
            self.x  = c.SCREEN_W - hw
            self.vx = -abs(self.vx) * 0.3
        if self.y > c.SCREEN_H + 60:
            self.take_damage(self.health)   # instant kill if falling off screen

    # ------------------------------------------------------------------
    # Attack
    # ------------------------------------------------------------------

    def can_attack(self) -> bool:
        """Return True when this stickman is allowed to start a new attack."""
        return self._attack_cd <= 0 and self.state not in (
            self.ST_ATTACK, self.ST_DEAD, self.ST_HURT
        )

    def start_attack(self) -> None:
        """Begin an attack swing."""
        self.state        = self.ST_ATTACK
        self.attack_phase = 0.0
        self._attack_cd   = self.weapon["cooldown_f"]
        self.attack_speed = self.weapon.get("spin_speed", c.ATTACK_SPIN_SPEED)
        self._hit_targets = set()

    def try_jump(self) -> bool:
        """Perform a ground jump or mid-air jump if jumps remain.

        Returns:
            True if a jump was executed.
        """
        if self._jumps_left <= 0:
            return False
        if self.on_ground:
            self.vy = c.JUMP_VEL
        else:
            self.vy = c.DOUBLE_JUMP_VEL
        self._jumps_left -= 1
        self.on_ground = False
        return True

    def can_throw_grenade(self) -> bool:
        """Return True when this stickman can throw a grenade."""
        return (
            self.alive
            and self.grenades_left > 0
            and self._grenade_cd <= 0
            and self.state not in (self.ST_HURT, self.ST_DEAD)
        )

    def throw_grenade_at(self, target_x: float, target_y: float) -> Optional[Grenade]:
        """Create a grenade with an arcing trajectory toward target point.

        Args:
            target_x: aim x.
            target_y: aim y.

        Returns:
            New Grenade if thrown, else None.
        """
        if not self.can_throw_grenade():
            return None

        dx = target_x - self.x
        aim_y = target_y - (self.y - self.TOTAL_H * 0.5)
        vx = _clamp(dx / 26.0, -9.0, 9.0)
        if abs(vx) < 3.2:
            vx = 3.2 if dx >= 0 else -3.2
        vy = _clamp(-10.5 + (aim_y / 120.0), c.GRENADE_THROW_MIN_VY, c.GRENADE_THROW_MAX_VY)

        self.grenades_left -= 1
        self._grenade_cd = c.GRENADE_COOLDOWN_F
        self.facing = 1 if dx >= 0 else -1

        j = self._joints()
        hand_x, hand_y = j["w_hand"]
        return Grenade(hand_x, hand_y, vx, vy, owner_id=id(self))

    def weapon_tip(self) -> tuple[float, float]:
        """Return the world position of the weapon tip (for hit-checking).

        Returns:
            (tip_x, tip_y) in world pixels.
        """
        j   = self._joints()
        wx, wy = j["w_hand"]
        ang    = j["w_ang"]
        reach  = self.weapon["reach"]
        return wx + math.sin(ang) * reach, wy + math.cos(ang) * reach

    def weapon_hitbox(self) -> Optional[pygame.Rect]:
        """Return a circle-bounding rect at the weapon tip during a spin.

        The tip sweeps a full 360° arc, so hit detection tracks the tip
        position each frame rather than a fixed forward swing window.

        Returns:
            Rect covering the weapon tip hit zone, or None if not attacking.
        """
        if self.state != self.ST_ATTACK or not (0.04 < self.attack_phase < 0.96):
            return None
        tx, ty = self.weapon_tip()
        r = c.WEAPON_HIT_RADIUS
        return pygame.Rect(int(tx - r), int(ty - r), r * 2, r * 2)

    def check_weapon_hits(self, targets: list[Stickman], damage: float,
                          knockback: float) -> list[tuple[Stickman, float, float]]:
        """Test weapon tip against targets and apply damage on contact.

        Args:
            targets: stickmen that can be damaged.
            damage: HP to subtract per hit.
            knockback: horizontal push strength.

        Returns:
            List of (target, tip_x, tip_y) for each new hit this frame.
        """
        hitbox = self.weapon_hitbox()
        if hitbox is None:
            return []

        hits: list[tuple[Stickman, float, float]] = []
        tx, ty = self.weapon_tip()

        for target in targets:
            if not target.alive or id(target) == id(self):
                continue
            if id(target) in self._hit_targets:
                continue
            if not hitbox.colliderect(target.rect):
                # Also accept tip proximity to body centre for fast spins
                cx = target.x
                cy = target.y - target.TOTAL_H / 2
                if math.hypot(tx - cx, ty - cy) > c.WEAPON_HIT_RADIUS + 28:
                    continue
            target.take_damage(damage, source_x=self.x)
            target.vx += self.facing * knockback
            target.vy -= 2.5
            self._hit_targets.add(id(target))
            hits.append((target, tx, ty))

        return hits

    # ------------------------------------------------------------------
    # Damage
    # ------------------------------------------------------------------

    def take_damage(self, amount: float, source_x: Optional[float] = None) -> None:
        """Reduce health and trigger hurt state; kill if HP reaches zero.

        Args:
            amount: damage dealt.
            source_x: x position of attacker, used to compute knockback direction.
        """
        if self.state == self.ST_DEAD:
            return
        self.health      -= amount
        self._hurt_frames = 16
        self.state        = self.ST_HURT

        # Knockback away from attacker
        if source_x is not None:
            direction = 1 if self.x >= source_x else -1
            self.vx  += direction * 3.5
            self.vy  -= 2.0

        if self.health <= 0:
            self.health = 0.0
            self.state  = self.ST_DEAD

    # ------------------------------------------------------------------
    # Tire interaction
    # ------------------------------------------------------------------

    def push_tire(self, tire: Tire) -> None:
        """Shove a tire based on the stickman's current velocity.

        Args:
            tire: the Tire to push.
        """
        dx = tire._cx - self.x
        dy = tire._cy - self.y
        dist = math.hypot(dx, dy) or 1.0
        speed = math.hypot(self.vx, self.vy) + 2.0
        tire.apply_impulse(dx / dist * speed * 0.6, dy / dist * speed * 0.4 - 1.0)

    # ------------------------------------------------------------------
    # Per-frame update (called from both Player and Enemy)
    # ------------------------------------------------------------------

    def _base_update(self, platforms: list[Platform]) -> None:
        """Shared per-frame logic: physics, animation, cooldown ticks.

        Args:
            platforms: platform list for collision.
        """
        if self.state == self.ST_DEAD:
            return

        self._apply_gravity()
        self._move()
        self._collide_platforms(platforms)
        self._collide_screen()

        # Walk animation phase — advances with horizontal movement
        if abs(self.vx) > 0.3 and self.on_ground:
            self.walk_phase += 0.18
        else:
            self.walk_phase *= 0.90   # decay back to neutral gradually

        # Attack phase advancement
        if self.state == self.ST_ATTACK:
            self.attack_phase += self.attack_speed
            if self.attack_phase >= 1.0:
                self.attack_phase = 0.0
                self.state        = self.ST_IDLE

        # Cooldowns
        if self._attack_cd > 0:
            self._attack_cd -= 1
        if self._grenade_cd > 0:
            self._grenade_cd -= 1
        if self._fire_flash_frames > 0:
            self._fire_flash_frames -= 1
        if self._hurt_frames > 0:
            self._hurt_frames -= 1
            if self._hurt_frames == 0 and self.state == self.ST_HURT:
                self.state = self.ST_IDLE

        # Update movement state label
        if self.state not in (self.ST_ATTACK, self.ST_HURT, self.ST_DEAD):
            if not self.on_ground:
                self.state = self.ST_JUMP
            elif abs(self.vx) > 0.4:
                self.state = self.ST_WALK
            else:
                self.state = self.ST_IDLE

        # Friction on ground
        if self.on_ground:
            self.vx *= c.GROUND_FRICTION


# ---------------------------------------------------------------------------
# Player — human-controlled stickman (blue by default)
# ---------------------------------------------------------------------------

class Player(Stickman):
    """Keyboard-controlled blue stickman.

    Controls:
        Left/Right or A/D — move
        Up or W           — jump
        Z or J            — attack
    """

    def __init__(self, x: float, y: float, health: float, weapon_name: str) -> None:
        """Args:
            x: starting centre-x.
            y: starting feet-y.
            health: max HP (scaled by difficulty).
            weapon_name: starting weapon key.
        """
        super().__init__(x, y, c.BLUE_COL, health, weapon_name)
        self.facing = 1
        self._jump_pressed = False   # for edge-triggered jump
        self._stored_melee = weapon_name
        self._arrows_left = 0
        self._rounds_left = 0
        self._shoot_pressed = False
        self._pending_shot = False
        self._grenade_pressed = False
        self._pending_grenade = False
        self._atk_held = False

    def equip_bow(self, arrow_count: int) -> None:
        """Switch to bow and load arrows.

        Args:
            arrow_count: number of arrows in this set.
        """
        if self.weapon_name not in ("bow", "ak47"):
            self._stored_melee = self.weapon_name
        self.weapon_name = "bow"
        self.weapon = c.WEAPONS["bow"]
        self._arrows_left = arrow_count
        self._rounds_left = 0

    def equip_ak47(self, rounds: int) -> None:
        """Switch to AK-47 with a full magazine.

        Args:
            rounds: rifle rounds loaded.
        """
        if self.weapon_name not in ("bow", "ak47"):
            self._stored_melee = self.weapon_name
        self.weapon_name = "ak47"
        self.weapon = c.WEAPONS["ak47"]
        self._rounds_left = rounds
        self._arrows_left = 0

    def equip_melee(self) -> None:
        """Revert to the last melee weapon when ranged ammo runs out."""
        self.weapon_name = self._stored_melee
        self.weapon = c.WEAPONS[self._stored_melee]
        self._arrows_left = 0
        self._rounds_left = 0

    def is_using_bow(self) -> bool:
        """Return True when the bow is the active weapon."""
        return self.weapon_name == "bow" and self._arrows_left > 0

    def is_using_ak47(self) -> bool:
        """Return True when the AK-47 is equipped with ammo."""
        return self.weapon_name == "ak47" and self._rounds_left > 0

    def is_using_ranged(self) -> bool:
        """Return True when a ranged weapon is active."""
        return self.is_using_bow() or self.is_using_ak47()

    def try_fire_arrow(self) -> Optional[Arrow]:
        """Launch one arrow if bow is equipped and cooldown allows.

        Returns:
            New Arrow instance, or None if unable to fire.
        """
        if not self.is_using_bow() or self._attack_cd > 0:
            return None
        if self.state in (self.ST_DEAD, self.ST_HURT):
            return None

        self._attack_cd = self.weapon["cooldown_f"]
        self._arrows_left -= 1

        j = self._joints()
        wx, wy = j["w_hand"]
        speed = c.ARROW_SPEED
        # Slight upward arc for readability
        vx = self.facing * speed
        vy = -2.0
        arrow = Arrow(
            wx + self.facing * 8, wy, vx, vy,
            self.weapon["damage"], self.weapon["knockback"], self.x,
        )

        if self._arrows_left <= 0:
            self.equip_melee()

        return arrow

    def try_fire_rifle(
        self, atk_held: bool,
    ) -> tuple[Optional[RifleBullet], Optional[MuzzleFlash], Optional[ShellCasing]]:
        """Fire AK-47 while attack key is held (automatic).

        Args:
            atk_held: whether Z/J is currently pressed.

        Returns:
            Tuple of (bullet, muzzle_flash, shell_casing) — any may be None.
        """
        if not atk_held or not self.is_using_ak47() or self._attack_cd > 0:
            return None, None, None
        if self.state in (self.ST_DEAD, self.ST_HURT):
            return None, None, None

        self._attack_cd = self.weapon["cooldown_f"]
        self._rounds_left -= 1
        self._fire_flash_frames = c.AK47_RECOIL_FRAMES

        j = self._joints()
        wx, wy = j["w_hand"]
        ang = j["w_ang"]
        reach = self.weapon["reach"]
        muzzle_x = wx + math.sin(ang) * reach
        muzzle_y = wy + math.cos(ang) * reach
        ux = math.sin(ang)
        uy = math.cos(ang)
        speed = c.AK47_BULLET_SPEED
        bullet = RifleBullet(
            muzzle_x + ux * 4, muzzle_y + uy * 4,
            ux * speed, uy * speed,
            self.weapon["damage"], self.weapon["knockback"], self.x,
        )
        flash = MuzzleFlash(muzzle_x + self.facing * 6, muzzle_y, self.facing)
        casing = ShellCasing(wx, wy - 4, self.facing)

        if self._rounds_left <= 0:
            self.equip_melee()

        return bullet, flash, casing

    def handle_input(self, keys: pygame.key.ScancodeWrapper) -> None:
        """Read keyboard state and move / jump / attack accordingly.

        Args:
            keys: result of pygame.key.get_pressed().
        """
        if self.state == self.ST_DEAD:
            return

        moving = False

        if keys[c.KEY_LEFT] or keys[c.KEY_LEFT2]:
            self.vx    -= 0.9
            self.vx     = max(self.vx, -c.PLAYER_SPEED)
            self.facing = -1
            moving      = True

        if keys[c.KEY_RIGHT] or keys[c.KEY_RIGHT2]:
            self.vx    += 0.9
            self.vx     = min(self.vx, c.PLAYER_SPEED)
            self.facing = 1
            moving      = True

        jump_held = keys[c.KEY_JUMP] or keys[c.KEY_JUMP2]
        if jump_held and not self._jump_pressed:
            self.try_jump()
        self._jump_pressed = jump_held

        atk_held = keys[c.KEY_ATK] or keys[c.KEY_ATK2]
        if atk_held and not self._shoot_pressed:
            if self.is_using_bow():
                self._pending_shot = True
            elif not self.is_using_ak47() and self.can_attack():
                self.start_attack()
        self._shoot_pressed = atk_held
        self._atk_held = atk_held

        grenade_held = keys[c.KEY_GRENADE]
        if grenade_held and not self._grenade_pressed and self.can_throw_grenade():
            self._pending_grenade = True
        self._grenade_pressed = grenade_held

    def consume_shot(self) -> Optional[Arrow]:
        """Fire a pending arrow request (called once per frame from GameScene).

        Returns:
            Arrow if fired, else None.
        """
        if not self._pending_shot:
            return None
        self._pending_shot = False
        return self.try_fire_arrow()

    def consume_rifle_shot(
        self,
    ) -> tuple[Optional[RifleBullet], Optional[MuzzleFlash], Optional[ShellCasing]]:
        """Attempt automatic AK-47 fire for this frame.

        Returns:
            Tuple of (bullet, muzzle_flash, shell_casing).
        """
        return self.try_fire_rifle(self._atk_held)

    def update(self, platforms: list[Platform]) -> None:
        """Step player physics and animation.

        Args:
            platforms: current level platforms.
        """
        self._base_update(platforms)

    def consume_grenade_throw(self) -> Optional[Grenade]:
        """Throw pending player grenade toward where they face.

        Returns:
            Grenade if thrown, else None.
        """
        if not self._pending_grenade:
            return None
        self._pending_grenade = False
        target_x = self.x + self.facing * 170
        target_y = self.y - 45
        return self.throw_grenade_at(target_x, target_y)


# ---------------------------------------------------------------------------
# Enemy — AI-controlled red stickman
# ---------------------------------------------------------------------------

class Enemy(Stickman):
    """Simple AI opponent that chases and attacks the player.

    AI state machine:
        IDLE   → walk toward player when within 500 px
        CHASE  → move toward player; jump if player is above
        ATTACK → swing when within attack-range and cooldown ready
        BACK   → briefly retreat after being hurt
    """

    AI_IDLE   = "ai_idle"
    AI_CHASE  = "ai_chase"
    AI_ATTACK = "ai_attack"
    AI_BACK   = "ai_back"

    def __init__(
        self,
        x: float,
        y: float,
        health: float,
        speed: float,
        damage: float,
        attack_cd: int,
        weapon_name: str,
        color: tuple[int, int, int] = c.RED_COL,
    ) -> None:
        """Args:
            x: starting centre-x.
            y: starting feet-y.
            health: max HP.
            speed: horizontal chase speed (px/frame).
            damage: damage dealt per hit.
            attack_cd: frames between attacks.
            weapon_name: weapon key from config.WEAPONS.
            color: stickman colour (red by default).
        """
        super().__init__(x, y, color, health, weapon_name)
        self.speed     = speed
        self.damage    = damage
        self.weapon["cooldown_f"] = attack_cd   # override with difficulty value
        self._ai_state = self.AI_IDLE
        self._back_frames = 0
        self.facing = -1   # enemies start facing left (toward player spawn)

    def update(self, platforms: list[Platform], player: Optional[Player]) -> None:  # type: ignore[override]
        """Advance AI logic and physics.

        Args:
            platforms: current level platforms.
            player: the human player (None if dead).
        """
        if player and player.state != Stickman.ST_DEAD:
            self._ai_decide(player, platforms)
        self._base_update(platforms)

    # ------------------------------------------------------------------
    # AI decision
    # ------------------------------------------------------------------

    def _ai_decide(self, player: Player, platforms: list[Platform]) -> None:
        """Choose movement and action based on player position.

        Args:
            player: the target.
            platforms: used for jump logic.
        """
        if self.state == self.ST_DEAD:
            return

        dx = player.x - self.x
        dy = player.y - self.y   # positive = player is below enemy

        # Transition from HURT
        if self.state == self.ST_HURT:
            self._ai_state    = self.AI_BACK
            self._back_frames = 30
            return

        # Back-off after hurt
        if self._ai_state == self.AI_BACK:
            self._back_frames -= 1
            retreat = -1 if dx > 0 else 1
            self.vx += retreat * 1.2
            self.vx  = _clamp(self.vx, -self.speed, self.speed)
            if self._back_frames <= 0:
                self._ai_state = self.AI_CHASE
            return

        dist = abs(dx)

        # Attack range
        if dist < c.TIRE_RADIUS * 2.2 + 20:   # roughly 60–70 px
            self._ai_state = self.AI_ATTACK
            self.facing    = 1 if dx > 0 else -1
            self.vx       *= 0.7   # slow down when attacking
            if self.can_attack():
                self.start_attack()
            return

        # Chase player
        self._ai_state = self.AI_CHASE
        self.facing    = 1 if dx > 0 else -1
        self.vx       += self.facing * 1.0
        self.vx        = _clamp(self.vx, -self.speed, self.speed)

        # Jump to reach player on higher platform (player y is smaller = higher on screen)
        if dy < -40 and self.on_ground and random.random() < 0.03:
            self.try_jump()
        elif dy < -80 and not self.on_ground and self._jumps_left > 0 and random.random() < 0.02:
            self.try_jump()

    # ------------------------------------------------------------------
    # Deliver damage to player when attack connects
    # ------------------------------------------------------------------

    def check_hit_player(self, player: Player) -> bool:
        """Return True (and deal damage) if this attack hit the player.

        Args:
            player: the target to test.

        Returns:
            True if the player was hit this call.
        """
        hits = self.check_weapon_hits([player], self.damage, self.weapon["knockback"])
        return len(hits) > 0

    def maybe_throw_grenade(self, player: Player, difficulty_cfg: dict) -> Optional[Grenade]:
        """Decide whether to throw a grenade based on distance and difficulty.

        Args:
            player: target player.
            difficulty_cfg: current mode configuration dict.

        Returns:
            Grenade if enemy decided to throw one this frame.
        """
        if not self.can_throw_grenade() or not player.alive:
            return None

        dx = player.x - self.x
        dist = abs(dx)
        # Avoid suicidal tosses at point-blank range.
        if dist < 110 or dist > 420:
            return None
        # Prefer throwing when target is elevated or moving.
        vertical_adv = player.y < self.y - 25
        player_moving = abs(player.vx) > 1.0
        intent_bonus = 0.16 if vertical_adv else 0.0
        intent_bonus += 0.1 if player_moving else 0.0

        throw_prob = float(difficulty_cfg.get("enemy_grenade_chance", 0.5)) + intent_bonus
        if random.random() > min(0.95, throw_prob):
            return None

        lead_x = player.x + player.vx * 14.0
        target_y = player.y - 40.0
        grenade = self.throw_grenade_at(lead_x, target_y)
        if grenade is not None:
            self._grenade_cd = int(difficulty_cfg.get("enemy_grenade_cooldown", c.GRENADE_COOLDOWN_F))
        return grenade
