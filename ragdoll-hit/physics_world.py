"""Pymunk space setup, collision handling, and damage calculation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

import pymunk

import config as c

if TYPE_CHECKING:
    from ragdoll import Ragdoll
    from weapon import Weapon

# Maps collision shapes back to game objects for arbiter callbacks.
BODY_SHAPE_OWNER: dict[pymunk.Shape, Ragdoll] = {}
WEAPON_SHAPE_OWNER: dict[pymunk.Shape, Weapon] = {}

# Pending hits drained by the stage each frame: (victim, damage, impulse, part_name).
HitCallback = Callable[["Ragdoll", float, pymunk.Vec2d, str], None]


def compute_damage(impact_speed: float, weapon_damage_mult: float) -> float:
    """Scale collision impulse into hit-point damage.

    Args:
        impact_speed: Relative contact speed in px/s.
        weapon_damage_mult: Per-weapon damage multiplier from config.

    Returns:
        Damage amount, or zero if impact is too weak.
    """
    if impact_speed < c.MIN_IMPACT_SPEED:
        return 0.0
    return impact_speed * c.DAMAGE_VELOCITY_SCALE * weapon_damage_mult


class PhysicsWorld:
    """Owns the pymunk space and weapon-vs-body collision routing."""

    def __init__(self) -> None:
        """Create space, gravity, and collision handlers."""
        self.space = pymunk.Space()
        self.space.gravity = c.GRAVITY
        self._pending_hits: list[tuple[Ragdoll, float, pymunk.Vec2d, str]] = []
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Wire weapon-body post-solve damage."""

        def post_solve(arbiter: pymunk.Arbiter, _space: pymunk.Space, _data: object) -> None:
            # Only score a fresh impact, not every frame a weapon happens to
            # stay in (or get tangled in) contact with a body — otherwise a
            # weapon wedged against an opponent racks up damage every single
            # physics substep it remains touching, instead of once per swing.
            if not arbiter.is_first_contact:
                return

            weapon_shape, body_shape = arbiter.shapes
            weapon = WEAPON_SHAPE_OWNER.get(weapon_shape)
            victim = BODY_SHAPE_OWNER.get(body_shape)
            if weapon is None or victim is None:
                return
            if weapon.owner is victim:
                return
            if weapon.owner.team == victim.team:
                return

            # Closing speed between the two bodies at the moment of contact —
            # not each body's own absolute speed, which would overstate
            # "impact" whenever both happen to be moving the same direction.
            relative_velocity = weapon_shape.body.velocity - body_shape.body.velocity
            impact_speed = relative_velocity.length

            damage = compute_damage(impact_speed, weapon.stats["damage_mult"])
            if damage <= 0.0:
                return

            part_name = victim.part_name_for_shape(body_shape)
            impulse = pymunk.Vec2d(weapon.shape.body.velocity.x, weapon.shape.body.velocity.y)
            if impulse.length > 0:
                impulse = impulse.normalized() * (damage * 12.0)
            self._pending_hits.append((victim, damage, impulse, part_name))

        self.space.on_collision(c.COL_WEAPON, c.COL_BODY, post_solve=post_solve)

    def step(self) -> None:
        """Advance physics by one frame with substeps."""
        dt = c.PHYSICS_DT / c.PHYSICS_SUBSTEPS
        for _ in range(c.PHYSICS_SUBSTEPS):
            self.space.step(dt)

    def drain_hits(self) -> list[tuple[Ragdoll, float, pymunk.Vec2d, str]]:
        """Return and clear hits queued during the last step.

        Returns:
            List of (victim, damage, impulse, part_name) tuples.
        """
        hits = self._pending_hits
        self._pending_hits = []
        return hits

    def clear_registries(self) -> None:
        """Remove shape ownership maps (used when resetting a stage)."""
        BODY_SHAPE_OWNER.clear()
        WEAPON_SHAPE_OWNER.clear()
