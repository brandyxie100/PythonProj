"""Stationary pillar-top fighter for the versus projectile duel mode."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import pygame

import config as c
from coords import lerp
from geom import point_in_circle, point_near_segment
from weapon_draw import draw_weapon

Point = tuple[float, float]


@dataclass(slots=True)
class BodySegment:
    """One damageable body part with an accumulating redness level."""

    name: str
    weight: float
    is_head: bool
    radius: float
    damage_mult: float = 1.0  # scales incoming damage (head/torso hit harder)
    redness: float = 0.0  # 0..1, drives red glow and death calculation

    def add_damage(self, amount: float) -> None:
        """Increase redness by the multiplier-scaled amount, clamped to 1.0."""
        self.redness = max(0.0, min(1.0, self.redness + amount * self.damage_mult))


@dataclass(slots=True)
class EmbeddedWeapon:
    """A projectile stuck in a fighter, kept only for rendering."""

    weapon_key: str
    x: float
    y: float
    angle: float


# Segment layout: (name, weight, is_head, radius, damage_mult).
# Weights sum to ~1.0 for the body-red ratio; limbs are the 1x damage baseline.
_SEGMENT_LAYOUT: tuple[tuple[str, float, bool, float, float], ...] = (
    ("head", 0.10, True, c.HEAD_R + 2.0, c.HEAD_DAMAGE_MULT),
    ("torso", 0.34, False, 11.0, c.TORSO_DAMAGE_MULT),
    ("arm_throw", 0.11, False, 7.0, c.LIMB_DAMAGE_MULT),
    ("arm_off", 0.11, False, 7.0, c.LIMB_DAMAGE_MULT),
    ("leg_front", 0.17, False, 8.0, c.LIMB_DAMAGE_MULT),
    ("leg_back", 0.17, False, 8.0, c.LIMB_DAMAGE_MULT),
)


class DuelFighter:
    """A fixed-position stick figure that only aims and throws weapons."""

    def __init__(
        self,
        team: str,
        x: float,
        ground_y: float,
        facing: int,
        weapon_key: str,
    ) -> None:
        """Create a duel fighter anchored on a pillar top.

        Args:
            team: Team id ("player" or "enemy").
            x: Horizontal anchor (feet center).
            ground_y: Y of the pillar top surface the fighter stands on.
            facing: 1 faces right, -1 faces left.
            weapon_key: Initial throw-weapon key.
        """
        self.team = team
        self.x = x
        self.ground_y = ground_y
        self.facing = facing
        self.weapon_key = weapon_key

        self.aim_elev = 0.72  # start angled upward
        self.power = c.THROW_POWER_MIN
        self.charging = False
        self.throw_cooldown = 0.0
        self.throw_anim_timer = 0.0  # counts down during the throw swing
        self.dead = False

        self.segments: dict[str, BodySegment] = {
            name: BodySegment(name, weight, is_head, radius, damage_mult)
            for name, weight, is_head, radius, damage_mult in _SEGMENT_LAYOUT
        }
        self.embedded: list[EmbeddedWeapon] = []

    # -- pose geometry ------------------------------------------------------
    @property
    def hip(self) -> Point:
        """Hip joint position."""
        return self.x, self.ground_y - c.LEG_LEN

    @property
    def neck(self) -> Point:
        """Neck/top-of-torso position."""
        hx, hy = self.hip
        return hx, hy - c.TORSO_LEN

    @property
    def shoulder(self) -> Point:
        """Shoulder pivot position (where the throwing arm rotates)."""
        hx, hy = self.hip
        return hx, hy - c.TORSO_LEN * 0.82

    @property
    def head_center(self) -> Point:
        """Head circle center."""
        nx, ny = self.neck
        return nx, ny - c.HEAD_R

    def aim_direction(self) -> Point:
        """Unit vector of the current aim (facing-aware)."""
        return self.facing * math.cos(self.aim_elev), -math.sin(self.aim_elev)

    def _throw_arm_offset(self) -> float:
        """Elevation offset (radians) of the drawn arm during a throw swing.

        The arm cocks back (higher elevation), whips forward past the aim line,
        then eases back to the resting aim angle. Purely cosmetic; the projectile
        is launched along the true aim direction at release.
        """
        if self.throw_anim_timer <= 0.0:
            return 0.0
        t = 1.0 - self.throw_anim_timer / c.THROW_ANIM_TIME  # 0 -> 1
        if t < 0.5:
            return lerp(0.85, -0.5, t / 0.5)  # cock back then whip forward/down
        return lerp(-0.5, 0.0, (t - 0.5) / 0.5)  # follow-through settle

    def _drawn_arm_direction(self) -> Point:
        """Facing-aware unit vector for the drawn throwing arm (with animation)."""
        elev = self.aim_elev + self._throw_arm_offset()
        return self.facing * math.cos(elev), -math.sin(elev)

    def _drawn_hand(self) -> Point:
        """Throwing-hand position for drawing/hit tests (animation-aware)."""
        sx, sy = self.shoulder
        dx, dy = self._drawn_arm_direction()
        return sx + dx * c.ARM_LEN, sy + dy * c.ARM_LEN

    def hand_point(self) -> Point:
        """Throwing-hand position along the true aim direction (projectile muzzle)."""
        sx, sy = self.shoulder
        dx, dy = self.aim_direction()
        return sx + dx * c.ARM_LEN, sy + dy * c.ARM_LEN

    def muzzle_point(self) -> Point:
        """Spawn point just beyond the hand so projectiles clear the body."""
        hx, hy = self.hand_point()
        dx, dy = self.aim_direction()
        return hx + dx * 12.0, hy + dy * 12.0

    def _geometry(self) -> dict[str, tuple]:
        """Compute current segment geometry for drawing and hit tests."""
        hip = self.hip
        neck = self.neck
        shoulder = self.shoulder
        hand = self._drawn_hand()
        # Off-arm rests across the body, slightly downward and backward.
        off_dir = (-self.facing * 0.55, 0.83)
        off_hand = (shoulder[0] + off_dir[0] * c.ARM_LEN, shoulder[1] + off_dir[1] * c.ARM_LEN)
        # Wide stance like the reference image (one leg forward, one back).
        front_foot = (hip[0] + self.facing * c.LEG_LEN * 0.62, self.ground_y)
        back_foot = (hip[0] - self.facing * c.LEG_LEN * 0.5, self.ground_y)
        return {
            "head": ("circle", self.head_center, self.segments["head"].radius),
            "torso": ("capsule", hip, neck, self.segments["torso"].radius),
            "arm_throw": ("capsule", shoulder, hand, self.segments["arm_throw"].radius),
            "arm_off": ("capsule", shoulder, off_hand, self.segments["arm_off"].radius),
            "leg_front": ("capsule", hip, front_foot, self.segments["leg_front"].radius),
            "leg_back": ("capsule", hip, back_foot, self.segments["leg_back"].radius),
        }

    # -- control ------------------------------------------------------------
    def rotate_aim(self, direction: int, dt: float) -> None:
        """Adjust aim elevation; positive direction aims higher."""
        self.aim_elev += direction * c.AIM_ROTATE_SPEED * dt
        self.aim_elev = max(c.AIM_MIN_ELEV, min(c.AIM_MAX_ELEV, self.aim_elev))

    def cycle_weapon(self) -> None:
        """Switch to the next throw weapon."""
        idx = c.THROW_WEAPON_ORDER.index(self.weapon_key)
        self.weapon_key = c.THROW_WEAPON_ORDER[(idx + 1) % len(c.THROW_WEAPON_ORDER)]

    def start_charge(self) -> None:
        """Begin charging throw power if allowed."""
        if self.throw_cooldown <= 0.0 and not self.dead:
            self.charging = True
            self.power = c.THROW_POWER_MIN

    def start_throw_animation(self) -> None:
        """Trigger the throwing-arm swing animation."""
        self.throw_anim_timer = c.THROW_ANIM_TIME

    def release_charge(self) -> float | None:
        """Release a charged throw; returns launch power or None if invalid."""
        if not self.charging:
            return None
        self.charging = False
        if self.throw_cooldown > 0.0 or self.dead:
            return None
        self.throw_cooldown = c.THROW_COOLDOWN
        self.start_throw_animation()
        return self.power

    def can_throw(self) -> bool:
        """Whether a new throw may start this frame."""
        return self.throw_cooldown <= 0.0 and not self.dead

    def update(self, dt: float) -> None:
        """Advance charge, cooldown, and throw-animation timers."""
        if self.throw_cooldown > 0.0:
            self.throw_cooldown = max(0.0, self.throw_cooldown - dt)
        if self.throw_anim_timer > 0.0:
            self.throw_anim_timer = max(0.0, self.throw_anim_timer - dt)
        if self.charging:
            self.power = min(c.THROW_POWER_MAX, self.power + c.THROW_CHARGE_RATE * dt)

    # -- damage -------------------------------------------------------------
    def hit_test(self, point: Point) -> str | None:
        """Return the name of the first body segment containing ``point``."""
        geometry = self._geometry()
        for name, shape in geometry.items():
            if shape[0] == "circle":
                _, center, radius = shape
                if point_in_circle(point, center, radius):
                    return name
            else:
                _, a, b, radius = shape
                if point_near_segment(point, a, b, radius):
                    return name
        return None

    def apply_hit(self, segment_name: str, damage: float, embed: EmbeddedWeapon) -> None:
        """Apply projectile damage to a segment and embed the weapon."""
        segment = self.segments.get(segment_name)
        if segment is None:
            return
        segment.add_damage(damage)
        self.embedded.append(embed)
        self._check_death(segment)

    def body_red_ratio(self) -> float:
        """Weighted fraction of the body that has turned red."""
        return sum(seg.redness * seg.weight for seg in self.segments.values())

    def _check_death(self, struck: BodySegment) -> None:
        """Evaluate death conditions after a hit."""
        if c.HEAD_LETHAL and struck.is_head and struck.redness > 0.0:
            self.dead = True
            return
        if self.body_red_ratio() >= c.BODY_RED_DEATH_RATIO:
            self.dead = True

    def reset_health(self) -> None:
        """Clear all damage and embedded weapons for a fresh duel."""
        for segment in self.segments.values():
            segment.redness = 0.0
        self.embedded.clear()
        self.dead = False
        self.throw_cooldown = 0.0
        self.charging = False
        self.power = c.THROW_POWER_MIN

    # -- rendering ----------------------------------------------------------
    def _segment_color(self, name: str) -> tuple[int, int, int]:
        """Interpolate segment color from silhouette black toward damage red.

        Uses a gain so even light wounds read clearly against the black body.
        """
        redness = min(1.0, self.segments[name].redness * c.DAMAGE_COLOR_GAIN)
        base = c.DUEL_FIGHTER_BLACK
        return (
            int(lerp(base[0], c.DAMAGE_RED[0], redness)),
            int(lerp(base[1], c.DAMAGE_RED[1], redness)),
            int(lerp(base[2], c.DAMAGE_RED[2], redness)),
        )

    def _draw_damage_glow(self, surf: pygame.Surface, geometry: dict[str, tuple]) -> None:
        """Draw a translucent red halo behind any wounded body segment."""
        top = int(self.head_center[1] - 44)
        left = int(self.x - 130)
        width = 260
        height = int(self.ground_y - top + 34)
        glow = pygame.Surface((width, height), pygame.SRCALPHA)
        wounded = False
        for name, shape in geometry.items():
            redness = self.segments[name].redness
            if redness <= 0.02:
                continue
            wounded = True
            alpha = int(min(1.0, redness) * 185)
            color = (*c.DAMAGE_GLOW, alpha)
            if shape[0] == "circle":
                _, center, radius = shape
                pygame.draw.circle(
                    glow,
                    color,
                    (int(center[0] - left), int(center[1] - top)),
                    int(radius + 9),
                )
            else:
                _, a, b, radius = shape
                pygame.draw.line(
                    glow,
                    color,
                    (int(a[0] - left), int(a[1] - top)),
                    (int(b[0] - left), int(b[1] - top)),
                    int(radius * 2 + 11),
                )
        if wounded:
            surf.blit(glow, (left, top))

    def draw(self, surf: pygame.Surface) -> None:
        """Draw the silhouette fighter with red-glowing damaged segments."""
        geometry = self._geometry()

        # Red halo behind the body highlights damaged segments.
        self._draw_damage_glow(surf, geometry)

        # Legs
        for leg in ("leg_back", "leg_front"):
            _, a, b, _ = geometry[leg]
            pygame.draw.line(
                surf, self._segment_color(leg), _i(a), _i(b), 6
            )
        # Torso
        _, hip, neck, _ = geometry["torso"]
        pygame.draw.line(surf, self._segment_color("torso"), _i(hip), _i(neck), 7)
        # Arms
        for arm in ("arm_off", "arm_throw"):
            _, a, b, _ = geometry[arm]
            pygame.draw.line(surf, self._segment_color(arm), _i(a), _i(b), 5)
        # Head
        _, center, radius = geometry["head"]
        pygame.draw.circle(surf, self._segment_color("head"), _i(center), int(radius))

        # Held weapon in the throwing hand (shows current loadout while aiming).
        self._draw_held_weapon(surf)

        # Embedded weapons stuck in the body.
        for weapon in self.embedded:
            _draw_embedded(surf, weapon)

    def _draw_held_weapon(self, surf: pygame.Surface) -> None:
        """Draw the loaded weapon in the (animated) throwing hand.

        Hidden briefly right after release so the weapon reads as thrown.
        """
        if self.throw_anim_timer > c.THROW_ANIM_TIME * 0.5:
            return
        stats = c.THROW_WEAPONS[self.weapon_key]
        hand = self._drawn_hand()
        dx, dy = self._drawn_arm_direction()
        tip = (hand[0] + dx * stats.length, hand[1] + dy * stats.length)
        draw_weapon(surf, self.weapon_key, hand, tip, scale=1.0)


def _draw_embedded(surf: pygame.Surface, weapon: EmbeddedWeapon) -> None:
    """Draw a weapon embedded in a body, protruding at its impact angle."""
    stats = c.THROW_WEAPONS[weapon.weapon_key]
    protrude = stats.length * 0.55
    back_x = weapon.x - math.cos(weapon.angle) * protrude
    back_y = weapon.y - math.sin(weapon.angle) * protrude
    # Bow impacts as an arrow shaft stuck in the body.
    key = "arrow" if weapon.weapon_key == "bow" else weapon.weapon_key
    draw_weapon(surf, key, (back_x, back_y), (weapon.x, weapon.y), scale=0.75)


def _i(point: Point) -> tuple[int, int]:
    """Round a point to integer pixel coordinates."""
    return int(point[0]), int(point[1])
