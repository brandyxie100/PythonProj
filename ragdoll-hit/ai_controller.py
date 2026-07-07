"""Simple AI controller for enemy stickmen."""

from __future__ import annotations

import math
from dataclasses import dataclass

import config as c
from stickman import Stickman
from terrain import Arena


@dataclass(slots=True)
class EnemyAI:
    """Momentum-aware AI tuned for platform fighting."""

    aggressiveness: float
    jump_cooldown: float = 0.0
    attack_cooldown: float = 0.0

    def update(
        self,
        enemy: Stickman,
        player: Stickman,
        arena: Arena,
        dt: float,
    ) -> tuple[int, bool, bool, int, int]:
        """Return (move_axis, jump, attack, arm_dir, leg_dir)."""
        del arena
        self.jump_cooldown = max(0.0, self.jump_cooldown - dt)
        self.attack_cooldown = max(0.0, self.attack_cooldown - dt)
        if not enemy.alive or not player.alive:
            return 0, False, False, 0, 0

        dx = player.x - enemy.x
        dy = player.y - enemy.y
        abs_dx = abs(dx)
        move_axis = 0
        desired = 80.0 - 20.0 * self.aggressiveness
        if abs_dx > desired:
            move_axis = 1 if dx > 0 else -1

        # Rotate attack arm toward player.
        sx, sy = enemy.shoulder
        target_angle = math.atan2(player.y - sy, player.x - sx)
        angle_delta = target_angle - enemy.arm_main_angle
        if angle_delta > math.pi:
            angle_delta -= 2 * math.pi
        elif angle_delta < -math.pi:
            angle_delta += 2 * math.pi
        arm_dir = 1 if angle_delta > 0.07 else -1 if angle_delta < -0.07 else 0

        jump = False
        if enemy.grounded and self.jump_cooldown <= 0.0:
            # Jump to contest elevated player or add pressure while approaching.
            should_hop = (dy < -58.0 and abs_dx < 260.0) or (
                abs_dx > 220.0 and self.aggressiveness > 1.0
            )
            if should_hop:
                jump = True
                self.jump_cooldown = 0.65 + 0.25 * (2.0 - self.aggressiveness)

        reach = enemy.weapon.stats.length + c.ARM_LEN + 18.0
        attack = False
        if abs_dx <= reach and abs(dy) <= 95.0 and self.attack_cooldown <= 0.0:
            attack = True
            self.attack_cooldown = 0.35 + 0.28 * (2.0 - self.aggressiveness)

        leg_dir = move_axis
        return move_axis, jump, attack, arm_dir, leg_dir
