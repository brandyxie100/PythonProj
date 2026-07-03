"""Ragdoll stick figure built from pymunk rigid bodies and joints."""

from __future__ import annotations

from typing import Callable, Optional

import pygame
import pymunk

import config as c
from coords import pygame_to_pymunk, pymunk_to_pygame
from physics_world import BODY_SHAPE_OWNER

CallableShape = Callable[[pymunk.Body], pymunk.Shape]


class Ragdoll:
    """Physics ragdoll with head, torso, arms, and legs."""

    PART_NAMES: tuple[str, ...] = (
        "head",
        "torso",
        "upper_arm_l",
        "lower_arm_l",
        "upper_arm_r",
        "lower_arm_r",
        "upper_leg_l",
        "lower_leg_l",
        "upper_leg_r",
        "lower_leg_r",
    )

    def __init__(
        self,
        space: pymunk.Space,
        pygame_x: float,
        pygame_y: float,
        team: str,
        colour: tuple[int, int, int],
        facing: int = 1,
    ) -> None:
        """Build ragdoll bodies, joints, and stabilizer in the physics space.

        Args:
            space: Active pymunk space.
            pygame_x: Spawn X in screen coordinates.
            pygame_y: Spawn Y in screen coordinates.
            team: Team id string used to ignore friendly weapon hits.
            colour: Draw colour for limbs.
            facing: 1 faces right, -1 faces left.
        """
        self.space = space
        self.team = team
        self.colour = colour
        self.facing = facing
        self.health = c.MAX_HEALTH
        self.stagger_frames = 0
        self.get_up_frames = 0

        self.bodies: dict[str, pymunk.Body] = {}
        self.shapes: dict[str, pymunk.Shape] = {}
        self._shape_to_part: dict[pymunk.Shape, str] = {}
        self._joints: list[pymunk.Constraint] = []
        self._stabilizer: Optional[pymunk.DampedRotarySpring] = None
        self._ground_anchor: Optional[pymunk.Body] = None

        px, py = pygame_to_pymunk(pygame_x, pygame_y)
        self._build(px, py)
        self._register_shapes()

    def _add_part(
        self,
        name: str,
        mass: float,
        moment: float,
        pos: tuple[float, float],
        shape_factory: CallableShape,
    ) -> None:
        body = pymunk.Body(mass, moment)
        body.position = pos
        shape = shape_factory(body)
        shape.friction = c.GROUND_FRICTION
        shape.elasticity = c.GROUND_ELASTICITY
        shape.collision_type = c.COL_BODY
        self.bodies[name] = body
        self.shapes[name] = shape
        self.space.add(body, shape)

    def _build(self, x: float, y: float) -> None:
        """Assemble all body segments and joints at the spawn point."""
        torso_moment = pymunk.moment_for_box(c.PART_MASS_TORSO, (c.TORSO_W, c.TORSO_H))
        self._add_part(
            "torso",
            c.PART_MASS_TORSO,
            torso_moment,
            (x, y),
            lambda b: pymunk.Poly.create_box(b, (c.TORSO_W, c.TORSO_H)),
        )

        head_offset = c.TORSO_H * 0.5 + c.HEAD_R + 2
        self._add_part(
            "head",
            c.PART_MASS_HEAD,
            pymunk.moment_for_circle(c.PART_MASS_HEAD, 0, c.HEAD_R),
            (x, y + head_offset),
            lambda b: pymunk.Circle(b, c.HEAD_R),
        )

        shoulder_y = y + c.TORSO_H * 0.25
        hip_y = y - c.TORSO_H * 0.35
        side = self.facing

        self._add_limb_chain(
            "upper_arm_l",
            "lower_arm_l",
            (x - side * c.TORSO_W * 0.5, shoulder_y),
            side=-side,
            vertical=False,
        )
        self._add_limb_chain(
            "upper_arm_r",
            "lower_arm_r",
            (x + side * c.TORSO_W * 0.5, shoulder_y),
            side=side,
            vertical=False,
        )
        self._add_limb_chain(
            "upper_leg_l",
            "lower_leg_l",
            (x - c.TORSO_W * 0.25, hip_y),
            side=-1,
            vertical=True,
        )
        self._add_limb_chain(
            "upper_leg_r",
            "lower_leg_r",
            (x + c.TORSO_W * 0.25, hip_y),
            side=1,
            vertical=True,
        )

        self._connect_joints(x, y, shoulder_y, hip_y)
        self._add_stabilizer()

    def _add_limb_chain(
        self,
        upper_name: str,
        lower_name: str,
        upper_pos: tuple[float, float],
        side: int,
        vertical: bool,
    ) -> None:
        upper_moment = pymunk.moment_for_segment(
            c.PART_MASS_LIMB, (0, 0), (side * c.UPPER_LIMB, 0 if not vertical else -c.UPPER_LIMB), c.LIMB_THICK
        )
        lower_moment = pymunk.moment_for_segment(
            c.PART_MASS_LIMB, (0, 0), (side * c.LOWER_LIMB, 0 if not vertical else -c.LOWER_LIMB), c.LIMB_THICK
        )

        if vertical:
            upper_end = (upper_pos[0], upper_pos[1] - c.UPPER_LIMB)
            lower_end = (upper_end[0], upper_end[1] - c.LOWER_LIMB)
            upper_seg = lambda b: pymunk.Segment(b, (0, 0), (0, -c.UPPER_LIMB), c.LIMB_THICK)
            lower_seg = lambda b: pymunk.Segment(b, (0, 0), (0, -c.LOWER_LIMB), c.LIMB_THICK)
        else:
            upper_end = (upper_pos[0] + side * c.UPPER_LIMB, upper_pos[1])
            lower_end = (upper_end[0] + side * c.LOWER_LIMB, upper_end[1])
            upper_seg = lambda b: pymunk.Segment(b, (0, 0), (side * c.UPPER_LIMB, 0), c.LIMB_THICK)
            lower_seg = lambda b: pymunk.Segment(b, (0, 0), (side * c.LOWER_LIMB, 0), c.LIMB_THICK)

        self._add_part(upper_name, c.PART_MASS_LIMB, upper_moment, upper_pos, upper_seg)
        self._add_part(lower_name, c.PART_MASS_LIMB, lower_moment, lower_end, lower_seg)

    def _connect_joints(
        self,
        x: float,
        y: float,
        shoulder_y: float,
        hip_y: float,
    ) -> None:
        torso = self.bodies["torso"]
        head = self.bodies["head"]

        neck = pymunk.PivotJoint(head, torso, (x, y + c.TORSO_H * 0.45))
        neck.collide_bodies = False
        self._joints.append(neck)

        def pivot(a: pymunk.Body, b: pymunk.Body, anchor: tuple[float, float]) -> pymunk.PivotJoint:
            joint = pymunk.PivotJoint(a, b, anchor)
            joint.collide_bodies = False
            self._joints.append(joint)
            return joint

        side = self.facing
        pivot(self.bodies["upper_arm_l"], torso, (x - side * c.TORSO_W * 0.35, shoulder_y))
        pivot(self.bodies["upper_arm_r"], torso, (x + side * c.TORSO_W * 0.35, shoulder_y))
        pivot(
            self.bodies["lower_arm_l"],
            self.bodies["upper_arm_l"],
            self.bodies["upper_arm_l"].position
            + pymunk.Vec2d(-side * c.UPPER_LIMB, 0),
        )
        pivot(
            self.bodies["lower_arm_r"],
            self.bodies["upper_arm_r"],
            self.bodies["upper_arm_r"].position
            + pymunk.Vec2d(side * c.UPPER_LIMB, 0),
        )

        pivot(self.bodies["upper_leg_l"], torso, (x - c.TORSO_W * 0.2, hip_y))
        pivot(self.bodies["upper_leg_r"], torso, (x + c.TORSO_W * 0.2, hip_y))
        pivot(
            self.bodies["lower_leg_l"],
            self.bodies["upper_leg_l"],
            self.bodies["upper_leg_l"].position + pymunk.Vec2d(0, -c.UPPER_LIMB),
        )
        pivot(
            self.bodies["lower_leg_r"],
            self.bodies["upper_leg_r"],
            self.bodies["upper_leg_r"].position + pymunk.Vec2d(0, -c.UPPER_LIMB),
        )

        for pair in (("upper_arm_l", "lower_arm_l"), ("upper_arm_r", "lower_arm_r")):
            limit = pymunk.RotaryLimitJoint(
                self.bodies[pair[0]],
                self.bodies[pair[1]],
                c.ELBOW_MIN,
                c.ELBOW_MAX,
            )
            self._joints.append(limit)

        for pair in (("upper_leg_l", "lower_leg_l"), ("upper_leg_r", "lower_leg_r")):
            limit = pymunk.RotaryLimitJoint(
                self.bodies[pair[0]],
                self.bodies[pair[1]],
                c.KNEE_MIN,
                c.KNEE_MAX,
            )
            self._joints.append(limit)

        self.space.add(*self._joints)

    def _add_stabilizer(self) -> None:
        """Keep torso upright unless staggered."""
        if self._stabilizer is not None:
            return
        if self._ground_anchor is None:
            anchor = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
            anchor.position = self.bodies["torso"].position
            self.space.add(anchor)
            self._ground_anchor = anchor
        else:
            self._ground_anchor.position = self.bodies["torso"].position

        spring = pymunk.DampedRotarySpring(
            self.bodies["torso"],
            self._ground_anchor,
            0,
            c.STABILIZER_STIFFNESS,
            c.STABILIZER_DAMPING,
        )
        self.space.add(spring)
        self._stabilizer = spring

    def _register_shapes(self) -> None:
        """Map each shape to this ragdoll for collision callbacks."""
        for name, shape in self.shapes.items():
            self._shape_to_part[shape] = name
            BODY_SHAPE_OWNER[shape] = self

    def part_name_for_shape(self, shape: pymunk.Shape) -> str:
        """Return anatomical part name for a pymunk shape."""
        return self._shape_to_part.get(shape, "torso")

    @property
    def torso(self) -> pymunk.Body:
        """Main control body."""
        return self.bodies["torso"]

    @property
    def hand_body(self) -> pymunk.Body:
        """Weapon attach point (right hand / weapon side)."""
        return self.bodies["lower_arm_r"]

    @property
    def position(self) -> pymunk.Vec2d:
        """Torso position in pymunk coordinates."""
        return self.torso.position

    @property
    def is_down(self) -> bool:
        """True while ragdoll is staggered on the ground."""
        return self.stagger_frames > 0 or self.get_up_frames > 0

    @property
    def is_alive(self) -> bool:
        """True while health remains."""
        return self.health > 0.0

    def apply_control(self, move_dir: int, jump: bool) -> None:
        """Apply player/AI locomotion forces to the torso.

        Args:
            move_dir: -1 left, 0 idle, 1 right.
            jump: Whether to apply an upward impulse this frame.
        """
        if self.is_down:
            return
        if move_dir != 0:
            self.torso.apply_force_at_local_point((move_dir * c.MOVE_FORCE, 0), (0, 0))
        if jump:
            self.torso.apply_impulse_at_local_point((0, c.JUMP_IMPULSE), (0, 0))

        if self._ground_anchor is not None:
            self._ground_anchor.position = self.torso.position
            self._ground_anchor.angle = 0

    def take_hit(self, part_name: str, damage: float, impulse: pymunk.Vec2d) -> None:
        """Apply damage and knockback to a struck body part.

        Args:
            part_name: Name of the anatomical segment hit.
            damage: Hit points to subtract.
            impulse: Knockback impulse vector.
        """
        self.health = max(0.0, self.health - damage)
        body = self.bodies.get(part_name, self.torso)
        if impulse.length > 0:
            body.apply_impulse_at_local_point(impulse, (0, 0))
        if damage >= c.STAGGER_DAMAGE_THRESHOLD:
            self._enter_stagger()

    def _enter_stagger(self) -> None:
        """Disable stabilizer and flop the ragdoll briefly."""
        self.stagger_frames = c.STAGGER_DURATION_F
        self.get_up_frames = c.GET_UP_DURATION_F
        if self._stabilizer is not None:
            self.space.remove(self._stabilizer)
            self._stabilizer = None

    def update(self) -> None:
        """Tick stagger/get-up timers and restore stabilizer when ready."""
        if self.stagger_frames > 0:
            self.stagger_frames -= 1
        if self.get_up_frames > 0:
            self.get_up_frames -= 1
            if self.get_up_frames == 0 and self._stabilizer is None:
                self._add_stabilizer()

    def draw(self, surf: pygame.Surface) -> None:
        """Draw all ragdoll segments on a pygame surface."""
        for name, shape in self.shapes.items():
            if isinstance(shape, pymunk.Circle):
                pos = pymunk_to_pygame(shape.body.position)
                pygame.draw.circle(surf, self.colour, pos, int(shape.radius), 0)
            elif isinstance(shape, pymunk.Segment):
                a = pymunk_to_pygame(shape.body.local_to_world(shape.a))
                b = pymunk_to_pygame(shape.body.local_to_world(shape.b))
                pygame.draw.line(surf, self.colour, a, b, int(shape.radius * 2))
            elif isinstance(shape, pymunk.Poly):
                verts = [
                    pymunk_to_pygame(shape.body.local_to_world(v))
                    for v in shape.get_vertices()
                ]
                pygame.draw.polygon(surf, self.colour, verts)
