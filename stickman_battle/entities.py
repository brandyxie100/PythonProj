"""Stickman Battle — game entities.

Contains all in-game objects:
  Platform, Tire, SpringBall, HitEffect, Stickman (base), Player, Enemy.

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

        if (keys[c.KEY_ATK] or keys[c.KEY_ATK2]) and self.can_attack():
            self.start_attack()

    def update(self, platforms: list[Platform]) -> None:
        """Step player physics and animation.

        Args:
            platforms: current level platforms.
        """
        self._base_update(platforms)


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
