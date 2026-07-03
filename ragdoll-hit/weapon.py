"""Weapon rigid bodies attached to ragdoll hands."""

from __future__ import annotations

from typing import Optional

import pygame
import pymunk

import config as c
from coords import pymunk_to_pygame
from physics_world import WEAPON_SHAPE_OWNER
from ragdoll import Ragdoll


class Weapon:
    """Physics weapon pinned to a ragdoll hand with a motor-driven swing."""

    def __init__(
        self,
        space: pymunk.Space,
        owner: Ragdoll,
        weapon_name: str = c.DEFAULT_WEAPON,
    ) -> None:
        """Create weapon body, shape, and hand pivot joint.

        Args:
            space: Active pymunk space.
            owner: Ragdoll wielding the weapon.
            weapon_name: Key into ``WEAPON_DATA``.
        """
        self.space = space
        self.owner = owner
        self.stats = c.WEAPON_DATA[weapon_name]
        self.swing_frames = 0
        self._motor: Optional[pymunk.SimpleMotor] = None
        self._pivot: Optional[pymunk.PivotJoint] = None

        hand = owner.hand_body
        grip = owner.hand_anchor
        length = self.stats["length"]
        half = length * 0.5
        moment = pymunk.moment_for_segment(
            self.stats["mass"],
            (-half, 0),
            (half, 0),
            self.stats["thickness"],
        )
        self.body = pymunk.Body(self.stats["mass"], moment)
        self.body.position = grip
        self.body.angle = hand.angle

        self.shape = pymunk.Segment(
            self.body,
            (-half, 0),
            (half, 0),
            self.stats["thickness"],
        )
        self.shape.friction = 0.6
        self.shape.collision_type = c.COL_WEAPON
        # Share the wielder's collision group so the weapon never physically
        # collides with its own owner's body parts (only the opponent's).
        self.shape.filter = pymunk.ShapeFilter(group=owner.group)
        self.space.add(self.body, self.shape)

        self._pivot = pymunk.PivotJoint(self.body, hand, grip)
        self._pivot.collide_bodies = False
        self.space.add(self._pivot)

        WEAPON_SHAPE_OWNER[self.shape] = self

    def _lock_to_hand(self) -> None:
        """Pin weapon motion to the forearm while not swinging.

        A free-hanging staff applies constant gravity torque on the arm
        chain, which slowly topples an otherwise stable standing pose.
        """
        hand = self.owner.hand_body
        grip = self.owner.hand_anchor
        self.body.position = grip
        self.body.angle = hand.angle
        self.body.velocity = hand.velocity
        self.body.angular_velocity = hand.angular_velocity

    def begin_swing(self) -> None:
        """Start a timed weapon swing if not already swinging."""
        if self.swing_frames > 0 or self.owner.is_down:
            return
        self.swing_frames = self.stats["swing_duration_f"]
        direction = self.owner.facing
        self.body.apply_impulse_at_local_point(
            (0, direction * self.stats["mass"] * self.stats["swing_speed"] * 40.0),
            (self.stats["length"] * 0.4, 0),
        )

    def update(self) -> None:
        """Tick swing timer and apply motor torque while attacking."""
        if self.swing_frames <= 0:
            if self._motor is not None:
                self.space.remove(self._motor)
                self._motor = None
            self._lock_to_hand()
            return

        self.swing_frames -= 1
        if self._motor is None:
            self._motor = pymunk.SimpleMotor(
                self.body,
                self.owner.hand_body,
                self.owner.facing * self.stats["swing_speed"],
            )
            self.space.add(self._motor)

    def draw(self, surf: pygame.Surface) -> None:
        """Draw the weapon segment."""
        a = pymunk_to_pygame(self.body.local_to_world(self.shape.a))
        b = pymunk_to_pygame(self.body.local_to_world(self.shape.b))
        pygame.draw.line(
            surf,
            self.stats["colour"],
            a,
            b,
            int(self.stats["thickness"] * 2),
        )
