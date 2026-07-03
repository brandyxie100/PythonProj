"""Ragdoll stick figure built from pymunk rigid bodies and joints."""

from __future__ import annotations

from typing import Callable, Optional

import pygame
import pymunk

import config as c
from coords import pygame_to_pymunk, pymunk_to_pygame, pygame_y_to_pymunk
from physics_world import BODY_SHAPE_OWNER

CallableShape = Callable[[pymunk.Body], pymunk.Shape]


class Ragdoll:
    """Physics ragdoll with head, torso, arms, and legs."""

    _next_group: int = 1

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

        # Unique, non-zero pymunk shape-filter group: parts sharing a group
        # never collide with each other, so a ragdoll's own overlapping limbs
        # (e.g. both upper legs starting near the same hip point) don't kick
        # each other apart every physics substep.
        self.group = Ragdoll._next_group
        Ragdoll._next_group += 1

        self.bodies: dict[str, pymunk.Body] = {}
        self.shapes: dict[str, pymunk.Shape] = {}
        self._shape_to_part: dict[pymunk.Shape, str] = {}
        self._joints: list[pymunk.Constraint] = []
        self._posture_constraints: list[pymunk.Constraint] = []
        self._ground_anchor: Optional[pymunk.Body] = None
        self._commanded_vx: float = 0.0
        self._jump_cooldown: int = 0
        self._leg_shape_names: tuple[str, ...] = (
            "upper_leg_l",
            "lower_leg_l",
            "upper_leg_r",
            "lower_leg_r",
        )

        px, py = pygame_to_pymunk(pygame_x, pygame_y)
        self._build(px, py)
        self._standing_torso_y = self.torso.position.y
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
        shape.filter = pymunk.ShapeFilter(group=self.group)
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
        facing = self.facing

        shoulder_l = (x - facing * c.TORSO_W * 0.5, shoulder_y)
        shoulder_r = (x + facing * c.TORSO_W * 0.5, shoulder_y)
        hip_l = (x - c.TORSO_W * 0.25, hip_y)
        hip_r = (x + c.TORSO_W * 0.25, hip_y)

        elbow_l, _wrist_l = self._add_limb_chain("upper_arm_l", "lower_arm_l", shoulder_l, (-facing, 0))
        elbow_r, _wrist_r = self._add_limb_chain("upper_arm_r", "lower_arm_r", shoulder_r, (facing, 0))
        knee_l, _ankle_l = self._add_limb_chain("upper_leg_l", "lower_leg_l", hip_l, (0, -1))
        knee_r, _ankle_r = self._add_limb_chain("upper_leg_r", "lower_leg_r", hip_r, (0, -1))

        self._connect_joints(
            x, y, shoulder_l, shoulder_r, elbow_l, elbow_r, hip_l, hip_r, knee_l, knee_r
        )
        self._add_posture_springs()

    def _add_limb_chain(
        self,
        upper_name: str,
        lower_name: str,
        joint_pos: tuple[float, float],
        direction: tuple[float, float],
    ) -> tuple[tuple[float, float], tuple[float, float]]:
        """Build a two-segment limb chain running along ``direction`` from ``joint_pos``.

        Each segment's body sits at its own midpoint with a shape defined
        symmetrically (``-half`` to ``+half``) around that origin. This
        matters physically: pymunk always treats ``body.position`` as the
        center of gravity, so an *asymmetric* local shape (e.g. running from
        local (0, 0) out to (length, 0)) would apply gravity/forces at a
        point that doesn't match the mass's real centroid, producing
        spurious torque and an uncontrollable spin. Placing the body at the
        true midpoint keeps translation and rotation physically consistent.

        Returns:
            World positions of the middle joint (elbow/knee) and the far end
            (wrist/ankle), for use when wiring up pivot joints.
        """
        dx, dy = direction

        def add_segment(name: str, start: tuple[float, float], length: float) -> tuple[float, float]:
            end = (start[0] + dx * length, start[1] + dy * length)
            mid = ((start[0] + end[0]) * 0.5, (start[1] + end[1]) * 0.5)
            half = (dx * length * 0.5, dy * length * 0.5)
            moment = pymunk.moment_for_segment(c.PART_MASS_LIMB, (-half[0], -half[1]), half, c.LIMB_THICK)
            self._add_part(
                name,
                c.PART_MASS_LIMB,
                moment,
                mid,
                lambda b, h=half: pymunk.Segment(b, (-h[0], -h[1]), h, c.LIMB_THICK),
            )
            return end

        joint_mid = add_segment(upper_name, joint_pos, c.UPPER_LIMB)
        far_end = add_segment(lower_name, joint_mid, c.LOWER_LIMB)
        return joint_mid, far_end

    def _connect_joints(
        self,
        x: float,
        y: float,
        shoulder_l: tuple[float, float],
        shoulder_r: tuple[float, float],
        elbow_l: tuple[float, float],
        elbow_r: tuple[float, float],
        hip_l: tuple[float, float],
        hip_r: tuple[float, float],
        knee_l: tuple[float, float],
        knee_r: tuple[float, float],
    ) -> None:
        torso = self.bodies["torso"]
        head = self.bodies["head"]

        neck = pymunk.PivotJoint(head, torso, (x, y + c.TORSO_H * 0.45))
        neck.collide_bodies = False
        self._joints.append(neck)

        def pivot(a: pymunk.Body, b: pymunk.Body, anchor: tuple[float, float]) -> None:
            joint = pymunk.PivotJoint(a, b, anchor)
            joint.collide_bodies = False
            self._joints.append(joint)

        pivot(self.bodies["upper_arm_l"], torso, shoulder_l)
        pivot(self.bodies["upper_arm_r"], torso, shoulder_r)
        pivot(self.bodies["lower_arm_l"], self.bodies["upper_arm_l"], elbow_l)
        pivot(self.bodies["lower_arm_r"], self.bodies["upper_arm_r"], elbow_r)

        pivot(self.bodies["upper_leg_l"], torso, hip_l)
        pivot(self.bodies["upper_leg_r"], torso, hip_r)
        pivot(self.bodies["lower_leg_l"], self.bodies["upper_leg_l"], knee_l)
        pivot(self.bodies["lower_leg_r"], self.bodies["upper_leg_r"], knee_r)

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

    def _add_posture_springs(self) -> None:
        """Hold torso and legs near their standing pose.

        Standing on two legs is an inverted-pendulum problem: if the hip
        spring only held each thigh relative to the *torso*, any transient
        torso wobble would immediately drag the legs off-vertical too, and
        vice versa — errors compound around the chain and the whole ragdoll
        topples. Instead, torso AND both thighs each get their own
        independent spring back to the same fixed (kinematic) world-upright
        reference, so a wobble in one doesn't destabilize the others. Knees
        are then sprung relative to their own thigh to stay straight.

        A spring alone can only ever dampen an inverted pendulum, not
        guarantee it stays up, so a hard ``RotaryLimitJoint`` on the torso
        and each thigh caps tilt during normal play — an arcade-friendly
        safety net matching how the reference game's fighters never
        spontaneously topple while standing. All these constraints are
        removed together on stagger and rebuilt once the character gets up,
        giving a genuine full-body ragdoll flop on a big hit.
        """
        if self._posture_constraints:
            return

        if self._ground_anchor is None:
            anchor = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
            anchor.position = self.bodies["torso"].position
            self.space.add(anchor)
            self._ground_anchor = anchor
        else:
            self._ground_anchor.position = self.bodies["torso"].position

        anchor = self._ground_anchor
        torso = self.bodies["torso"]
        constraints: list[pymunk.Constraint] = [
            pymunk.DampedRotarySpring(
                torso, anchor, 0, c.STABILIZER_STIFFNESS, c.STABILIZER_DAMPING
            ),
            pymunk.RotaryLimitJoint(torso, anchor, -c.TORSO_TILT_LIMIT, c.TORSO_TILT_LIMIT),
        ]
        for hip, leg_side in (("upper_leg_l", "lower_leg_l"), ("upper_leg_r", "lower_leg_r")):
            hip_body = self.bodies[hip]
            constraints.append(
                pymunk.DampedRotarySpring(hip_body, anchor, 0, c.HIP_STIFFNESS, c.HIP_DAMPING)
            )
            constraints.append(
                pymunk.RotaryLimitJoint(hip_body, anchor, -c.HIP_TILT_LIMIT, c.HIP_TILT_LIMIT)
            )
            constraints.append(
                pymunk.DampedRotarySpring(
                    hip_body, self.bodies[leg_side], 0, c.KNEE_STIFFNESS, c.KNEE_DAMPING
                )
            )

        self.space.add(*constraints)
        self._posture_constraints = constraints

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
    def hand_anchor(self) -> pymunk.Vec2d:
        """World position of the wrist (grip point), not the elbow.

        ``lower_arm_r``'s body origin sits at the forearm midpoint (see
        ``_add_limb_chain``), so the wrist is half a limb-length further out.
        """
        arm = self.bodies["lower_arm_r"]
        return arm.local_to_world((self.facing * c.LOWER_LIMB * 0.5, 0))

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

    def _set_leg_friction(self, friction: float) -> None:
        """Apply friction to leg/foot shapes only (torso/arms keep default)."""
        for name in self._leg_shape_names:
            self.shapes[name].friction = friction

    def _ground_surface_y(self) -> float:
        """Pymunk Y of the main floor collision surface."""
        return pygame_y_to_pymunk(c.GROUND_Y) + c.TERRAIN_THICKNESS

    def _is_grounded(self) -> bool:
        """True when at least one foot is resting on the main floor."""
        ground_y = self._ground_surface_y()
        for name in ("lower_leg_l", "lower_leg_r"):
            body = self.bodies[name]
            foot_bottom = body.position.y - c.LOWER_LIMB * 0.5 - c.LIMB_THICK
            if foot_bottom <= ground_y + c.GROUNDED_TOLERANCE:
                return True
        return False

    def _clamp_upward_velocity(self) -> None:
        """Prevent runaway upward speed from impulse stacking or collisions."""
        for body in self.bodies.values():
            if body.velocity.y > c.MAX_UPWARD_VELOCITY:
                body.velocity = (body.velocity.x, c.MAX_UPWARD_VELOCITY)

    def _maintain_standing_height(self) -> None:
        """Nudge the whole body up if gravity has compressed the leg joints."""
        if not self._is_grounded():
            return
        error = self._standing_torso_y - self.torso.position.y
        if error <= 1.5:
            return
        shift = min(error, 8.0)
        for body in self.bodies.values():
            pos = body.position
            body.position = (pos.x, pos.y + shift)

    def apply_control(self, move_dir: int, jump: bool) -> None:
        """Apply player/AI locomotion to the whole body.

        Args:
            move_dir: -1 left, 0 idle, 1 right.
            jump: Whether to apply an upward impulse this frame.
        """
        if self.is_down:
            return

        target_vx = move_dir * c.MOVE_SPEED
        delta = target_vx - self._commanded_vx
        if abs(delta) > c.MOVE_ACCEL:
            delta = c.MOVE_ACCEL if delta > 0 else -c.MOVE_ACCEL
        self._commanded_vx += delta

        # Lower leg friction while actively driving horizontal motion so
        # planted feet do not slip against high friction and topple the torso.
        is_moving = move_dir != 0 or abs(self._commanded_vx) > 1.0
        self._set_leg_friction(c.MOVE_GROUND_FRICTION if is_moving else c.GROUND_FRICTION)

        if abs(self._commanded_vx) > 0.01:
            for body in self.bodies.values():
                body.velocity = (self._commanded_vx, body.velocity.y)
        elif self._is_grounded():
            # Kill residual downward drift while planted so the stance stays level.
            for body in self.bodies.values():
                if body.velocity.y < 0:
                    body.velocity = (body.velocity.x, 0)
            if move_dir == 0 and abs(self._commanded_vx) < 0.5:
                for body in self.bodies.values():
                    body.angular_velocity *= c.IDLE_ANGULAR_DAMPING

        if jump and self._is_grounded() and self._jump_cooldown <= 0:
            self.torso.apply_impulse_at_local_point((0, c.JUMP_IMPULSE), (0, 0))
            self._jump_cooldown = c.JUMP_COOLDOWN_F

        if self._ground_anchor is not None:
            self._ground_anchor.position = self.torso.position
            self._ground_anchor.angle = 0

        if move_dir == 0 and self._jump_cooldown <= 0:
            self._maintain_standing_height()

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
        """Disable all posture constraints and flop the ragdoll briefly."""
        self.stagger_frames = c.STAGGER_DURATION_F
        self.get_up_frames = c.GET_UP_DURATION_F
        self._commanded_vx = 0.0
        self._jump_cooldown = 0
        self._set_leg_friction(c.GROUND_FRICTION)
        if self._posture_constraints:
            self.space.remove(*self._posture_constraints)
            self._posture_constraints = []

    def update(self) -> None:
        """Tick stagger/get-up timers and restore posture constraints when ready."""
        if self._jump_cooldown > 0:
            self._jump_cooldown -= 1
        self._clamp_upward_velocity()
        if self.stagger_frames > 0:
            self.stagger_frames -= 1
        if self.get_up_frames > 0:
            self.get_up_frames -= 1
            if self.get_up_frames == 0 and not self._posture_constraints:
                self._add_posture_springs()

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
