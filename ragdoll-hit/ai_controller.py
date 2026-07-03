"""Enemy AI state machine for stage combat."""

from __future__ import annotations

from enum import Enum

import config as c


class AIState(str, Enum):
    """High-level enemy behaviour states."""

    APPROACH = "approach"
    ATTACK = "attack"
    RECOVER = "recover"


class AIController:
    """Drives enemy movement and attacks toward the player."""

    def __init__(self) -> None:
        """Initialize idle AI state."""
        self.state = AIState.APPROACH
        self.cooldown = 0
        self.recover_timer = 0

    def reset(self) -> None:
        """Return AI to default approach behaviour."""
        self.state = AIState.APPROACH
        self.cooldown = 0
        self.recover_timer = 0

    def update(
        self,
        self_x: float,
        target_x: float,
        distance: float,
    ) -> tuple[int, bool, bool]:
        """Advance the state machine and return control outputs.

        Args:
            self_x: Enemy horizontal position.
            target_x: Player horizontal position.
            distance: Euclidean distance between ragdolls.

        Returns:
            Tuple of (move_dir, jump, attack) where move_dir is -1, 0, or 1.
        """
        if self.cooldown > 0:
            self.cooldown -= 1

        if self.state == AIState.RECOVER:
            self.recover_timer -= 1
            if self.recover_timer <= 0:
                self.state = AIState.APPROACH
            return 0, False, False

        if distance <= c.AI_ATTACK_RANGE and self.cooldown <= 0:
            self.state = AIState.ATTACK
            self.cooldown = c.AI_ATTACK_COOLDOWN_F
            self.recover_timer = c.AI_RECOVER_F
            self.state = AIState.RECOVER
            return 0, False, True

        if distance > c.AI_APPROACH_RANGE:
            move_dir = 1 if target_x > self_x else -1
            return move_dir, False, False

        move_dir = 1 if target_x > self_x else -1
        jump = distance > c.AI_ATTACK_RANGE * 0.8
        return move_dir, jump, False
