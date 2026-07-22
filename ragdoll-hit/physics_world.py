"""Lightweight combat collision helpers for stickman battles."""

from __future__ import annotations

from dataclasses import dataclass

import config as c
from stickman import Stickman


@dataclass(frozen=True, slots=True)
class HitResult:
    """One attack result produced during simulation step."""

    victim_id: int
    damage: float
    knockback_x: float
    knockback_y: float


def _distance_sq(a: tuple[float, float], b: tuple[float, float]) -> float:
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    return dx * dx + dy * dy


def _point_segment_distance_sq(
    p: tuple[float, float],
    a: tuple[float, float],
    b: tuple[float, float],
) -> float:
    """Squared distance from point p to segment ab."""
    abx = b[0] - a[0]
    aby = b[1] - a[1]
    apx = p[0] - a[0]
    apy = p[1] - a[1]
    ab_len_sq = abx * abx + aby * aby
    if ab_len_sq <= 1e-6:
        return _distance_sq(p, a)
    t = max(0.0, min(1.0, (apx * abx + apy * aby) / ab_len_sq))
    nearest = (a[0] + abx * t, a[1] + aby * t)
    return _distance_sq(p, nearest)


def _segment_hits_circle(
    seg_a: tuple[float, float],
    seg_b: tuple[float, float],
    center: tuple[float, float],
    radius: float,
) -> bool:
    return _point_segment_distance_sq(center, seg_a, seg_b) <= radius * radius


def weapon_hit(attacker: Stickman, victim: Stickman) -> HitResult | None:
    """Return hit result when attack segment intersects victim body."""
    if not attacker.weapon.is_attacking:
        return None
    if not attacker.weapon.can_hit(victim.sid):
        return None

    seg_a, seg_b, damage = attacker.weapon_segment()
    hit = _segment_hits_circle(seg_a, seg_b, victim.torso_center, c.BODY_RADIUS)
    hit = hit or _segment_hits_circle(seg_a, seg_b, victim.head_center, c.HEAD_R + 2.0)
    if not hit:
        # Close fist follow-through hitbox.
        fist = attacker.fist_point()
        hit = _distance_sq(fist, victim.torso_center) <= (c.BODY_RADIUS + 10.0) ** 2
    if not hit:
        return None

    attacker.weapon.mark_hit(victim.sid)
    # Push the victim away from the attacker (not just along facing).
    dx = victim.x - attacker.x
    if abs(dx) < 1.0:
        knock_sign = 1.0 if attacker.facing >= 0 else -1.0
    else:
        knock_sign = 1.0 if dx > 0.0 else -1.0
    # Heavier weapons shove a bit harder.
    weight = 0.85 + min(0.45, attacker.weapon.stats.damage / 80.0)
    return HitResult(
        victim_id=victim.sid,
        damage=damage,
        knockback_x=knock_sign * c.ATTACK_HIT_KNOCKBACK_X * weight,
        knockback_y=c.ATTACK_HIT_KNOCKBACK_Y * weight,
    )
