"""Stickman entity with simple physics and controllable limbs."""

from __future__ import annotations

import math
from dataclasses import dataclass

import pygame

import config as c
from terrain import Arena
from weapon import Weapon
from weapon_draw import draw_weapon


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


@dataclass(slots=True)
class Stickman:
    """Fighter with basic platform physics and rotating limbs."""

    sid: int
    team: str
    x: float
    y: float
    color: tuple[int, int, int]
    weapon: Weapon
    max_health: float
    move_scale: float
    attack_scale: float
    facing: int = 1
    vx: float = 0.0
    vy: float = 0.0
    health: float = 100.0
    grounded: bool = False
    jumps_used: int = 0
    arm_main_angle: float = -0.2
    arm_off_angle: float = -2.8
    leg_pose: float = 0.1
    walk_phase: float = 0.0
    stun_timer: float = 0.0  # remaining knockback stun (blocks full movement)

    def __post_init__(self) -> None:
        self.health = self.max_health

    @property
    def alive(self) -> bool:
        """Return True while fighter has health."""
        return self.health > 0.0

    @property
    def is_stunned(self) -> bool:
        """True while recovering from a hit knockback."""
        return self.stun_timer > 0.0

    @property
    def shoulder(self) -> tuple[float, float]:
        """Approximate shoulder pivot in screen coordinates."""
        return self.x, self.y - c.TORSO_LEN * 0.78

    @property
    def neck(self) -> tuple[float, float]:
        """Top of torso segment."""
        return self.x, self.y - c.TORSO_LEN

    @property
    def torso_center(self) -> tuple[float, float]:
        """Torso hit center used by combat checks."""
        return self.x, self.y - c.TORSO_LEN * 0.45

    @property
    def head_center(self) -> tuple[float, float]:
        """Head center used by combat checks."""
        _, neck_y = self.neck
        return self.x, neck_y - c.HEAD_R

    def apply_move_axis(self, axis: int, dt: float) -> None:
        """Accelerate toward horizontal movement target.

        While stunned from a hit, movement authority is heavily reduced so
        knockback is not cancelled by AI/player steering on the next frame.
        """
        axis = int(_clamp(float(axis), -1.0, 1.0))
        target = axis * c.MOVE_SPEED * self.move_scale
        accel = c.MOVE_ACCEL * dt
        if self.weapon.is_attacking:
            target *= 0.72
        if self.is_stunned:
            target *= c.ATTACK_HIT_STUN_MOVE_SCALE
            accel *= c.ATTACK_HIT_STUN_MOVE_SCALE
        if self.vx < target:
            self.vx = min(target, self.vx + accel)
        else:
            self.vx = max(target, self.vx - accel)
        if axis == 0 and not self.is_stunned:
            self.vx *= c.MOVE_FRICTION
            if abs(self.vx) < 3.0:
                self.vx = 0.0
        elif axis != 0:
            self.walk_phase += dt * (5.0 + abs(self.vx) * 0.02)
            self.facing = axis

    def rotate_primary_arm(self, direction: int, dt: float) -> None:
        """Manual control for attacking arm angle."""
        self.arm_main_angle += direction * c.ARM_ROTATE_SPEED * dt
        self.arm_main_angle = _clamp(self.arm_main_angle, c.MIN_ARM_ANGLE, c.MAX_ARM_ANGLE)

    def rotate_off_arm(self, direction: int, dt: float) -> None:
        """Manual control for supporting arm angle."""
        self.arm_off_angle += direction * c.ARM_ROTATE_SPEED * dt
        self.arm_off_angle = _clamp(self.arm_off_angle, c.MIN_ARM_ANGLE, c.MAX_ARM_ANGLE)

    def rotate_legs(self, direction: int, dt: float) -> None:
        """Adjust leg spread/pose from keyboard input."""
        self.leg_pose += direction * c.LEG_ROTATE_SPEED * dt
        self.leg_pose = _clamp(self.leg_pose, -c.MAX_LEG_POSE, c.MAX_LEG_POSE)

    def try_jump(self) -> bool:
        """Perform jump if allowed (includes one extra mid-air jump)."""
        if self.is_stunned:
            return False
        if self.jumps_used >= c.MAX_JUMPS:
            return False
        self.vy = -c.JUMP_SPEED
        self.jumps_used += 1
        self.grounded = False
        return True

    def try_attack(self) -> bool:
        """Start attack swing for current weapon."""
        if self.is_stunned:
            return False
        return self.weapon.try_start_attack(self.arm_main_angle, self.facing)

    def take_damage(self, amount: float, knockback_x: float, knockback_y: float) -> None:
        """Apply damage and launch the fighter with knockback.

        Sets the fighter airborne and starts a short stun so the impulse is
        not immediately cancelled by movement input.
        """
        self.health = max(0.0, self.health - amount)
        self.vx += knockback_x
        # Absolute upward launch so grounded fighters leave the floor.
        self.vy = min(self.vy, 0.0) - knockback_y
        self.grounded = False
        self.jumps_used = max(1, self.jumps_used)
        self.stun_timer = max(self.stun_timer, c.ATTACK_HIT_STUN)
        if abs(knockback_x) > 1.0:
            self.facing = -1 if knockback_x > 0.0 else 1

    def update(self, arena: Arena, dt: float) -> None:
        """Advance fighter physics and environment interactions."""
        self.weapon.update(dt)
        if self.stun_timer > 0.0:
            self.stun_timer = max(0.0, self.stun_timer - dt)
        previous_foot_y = self.y + c.LEG_LEN

        self.vy = min(self.vy + c.GRAVITY * dt, c.MAX_FALL_SPEED)
        self.x += self.vx * dt
        self.x = _clamp(self.x, 20.0, c.SCREEN_W - 20.0)
        self.y += self.vy * dt
        self.y, self.vy, self.grounded = arena.resolve_ground(
            self.x,
            self.y,
            previous_foot_y,
            self.vy,
        )
        if self.grounded:
            self.jumps_used = 0
            if self.weapon.is_attacking:
                self.vx *= 0.95
            elif self.is_stunned:
                # Slide to a stop after landing from a hit.
                self.vx *= 0.88
            else:
                pass
        else:
            self.vx *= 0.995

        # Hazard damage checks for torso and feet.
        damage = arena.obstacle_damage_at(self.torso_center) + arena.obstacle_damage_at(
            (self.x, self.y + c.LEG_LEN - 2.0)
        )
        if damage > 0.0:
            self.health = max(0.0, self.health - damage * dt)

    def _leg_points(self) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float], tuple[float, float]]:
        """Compute left/right leg segment endpoints for drawing."""
        hip = (self.x, self.y)
        stride = 0.28 * math.sin(self.walk_phase)
        left_angle = math.pi / 2 + self.leg_pose + stride
        right_angle = math.pi / 2 - self.leg_pose - stride
        left_foot = (
            hip[0] + math.cos(left_angle) * c.LEG_LEN,
            hip[1] + math.sin(left_angle) * c.LEG_LEN,
        )
        right_foot = (
            hip[0] + math.cos(right_angle) * c.LEG_LEN,
            hip[1] + math.sin(right_angle) * c.LEG_LEN,
        )
        return hip, left_foot, hip, right_foot

    def weapon_segment(self) -> tuple[tuple[float, float], tuple[float, float], float]:
        """Return attacking segment and weapon damage for hit checks."""
        shoulder_x, shoulder_y = self.shoulder
        arm_angle = self.weapon.current_angle(self.arm_main_angle)
        hand_x = shoulder_x + math.cos(arm_angle) * c.ARM_LEN
        hand_y = shoulder_y + math.sin(arm_angle) * c.ARM_LEN
        tip_x = hand_x + math.cos(arm_angle) * self.weapon.stats.length
        tip_y = hand_y + math.sin(arm_angle) * self.weapon.stats.length
        return (hand_x, hand_y), (tip_x, tip_y), self.weapon.stats.damage * self.attack_scale

    def fist_point(self) -> tuple[float, float]:
        """Return primary fist location for unarmed punch hit checks."""
        shoulder_x, shoulder_y = self.shoulder
        arm_angle = self.weapon.current_angle(self.arm_main_angle)
        return (
            shoulder_x + math.cos(arm_angle) * c.ARM_LEN,
            shoulder_y + math.sin(arm_angle) * c.ARM_LEN,
        )

    def draw(self, surf: pygame.Surface, is_player: bool = False) -> None:
        """Render stickman with head, torso, arms, legs, and weapon."""
        neck_x, neck_y = self.neck
        shoulder_x, shoulder_y = self.shoulder
        hip_x, hip_y = self.x, self.y

        # Torso
        pygame.draw.line(
            surf,
            self.color,
            (int(hip_x), int(hip_y)),
            (int(neck_x), int(neck_y)),
            5,
        )
        # Head
        head_x, head_y = self.head_center
        pygame.draw.circle(surf, self.color, (int(head_x), int(head_y)), int(c.HEAD_R), 0)

        # Arms
        main_angle = self.weapon.current_angle(self.arm_main_angle)
        off_angle = self.arm_off_angle
        for angle, width in ((main_angle, 4), (off_angle, 3)):
            hx = shoulder_x + math.cos(angle) * c.ARM_LEN
            hy = shoulder_y + math.sin(angle) * c.ARM_LEN
            pygame.draw.line(
                surf,
                self.color,
                (int(shoulder_x), int(shoulder_y)),
                (int(hx), int(hy)),
                width,
            )

        # Legs
        hip_l, foot_l, hip_r, foot_r = self._leg_points()
        pygame.draw.line(
            surf,
            self.color,
            (int(hip_l[0]), int(hip_l[1])),
            (int(foot_l[0]), int(foot_l[1])),
            4,
        )
        pygame.draw.line(
            surf,
            self.color,
            (int(hip_r[0]), int(hip_r[1])),
            (int(foot_r[0]), int(foot_r[1])),
            4,
        )

        # Weapon (multi-part silhouette matching real-world structure)
        (wx1, wy1), (wx2, wy2), _ = self.weapon_segment()
        draw_weapon(
            surf,
            self.weapon.weapon_key,
            (wx1, wy1),
            (wx2, wy2),
            scale=1.0,
        )
        if is_player:
            pygame.draw.circle(surf, c.WHITE, (int(head_x), int(head_y)), int(c.HEAD_R), 1)
