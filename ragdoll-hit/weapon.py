"""Weapon handling and swing geometry."""

from __future__ import annotations

from dataclasses import dataclass, field

import config as c


@dataclass(slots=True)
class Weapon:
    """Attack state and damage model for a stickman weapon."""

    weapon_key: str
    cooldown_timer: float = 0.0
    attack_timer: float = 0.0
    attack_start_angle: float = 0.0
    attack_sign: float = 1.0
    hit_target_ids: set[int] = field(default_factory=set)

    @property
    def stats(self) -> c.WeaponStats:
        """Return stats for current weapon key."""
        return c.WEAPONS[self.weapon_key]

    @property
    def is_attacking(self) -> bool:
        """Whether the weapon is in its active swing window."""
        return self.attack_timer > 0.0

    def cycle(self) -> None:
        """Switch to next weapon type in the configured order."""
        idx = c.WEAPON_ORDER.index(self.weapon_key)
        next_idx = (idx + 1) % len(c.WEAPON_ORDER)
        self.weapon_key = c.WEAPON_ORDER[next_idx]
        self.cooldown_timer = 0.0
        self.attack_timer = 0.0
        self.hit_target_ids.clear()

    def try_start_attack(self, arm_angle: float, facing: int) -> bool:
        """Begin a 180-degree swing if cooldown permits."""
        if self.cooldown_timer > 0.0 or self.attack_timer > 0.0:
            return False
        self.attack_start_angle = arm_angle
        self.attack_sign = 1.0 if facing >= 0 else -1.0
        self.attack_timer = self.stats.sweep_time
        self.cooldown_timer = self.stats.cooldown
        self.hit_target_ids.clear()
        return True

    def update(self, dt: float) -> None:
        """Advance attack and cooldown timers."""
        if self.cooldown_timer > 0.0:
            self.cooldown_timer = max(0.0, self.cooldown_timer - dt)
        if self.attack_timer > 0.0:
            self.attack_timer = max(0.0, self.attack_timer - dt)
            if self.attack_timer <= 0.0:
                self.hit_target_ids.clear()

    def current_angle(self, resting_arm_angle: float) -> float:
        """Return weapon arm angle; animated through a 180-degree sweep."""
        if not self.is_attacking:
            return resting_arm_angle
        elapsed = self.stats.sweep_time - self.attack_timer
        progress = max(0.0, min(1.0, elapsed / self.stats.sweep_time))
        return self.attack_start_angle + self.attack_sign * c.ATTACK_SWEEP_RAD * progress

    def can_hit(self, target_id: int) -> bool:
        """Return True when target has not been hit in current swing."""
        return target_id not in self.hit_target_ids

    def mark_hit(self, target_id: int) -> None:
        """Store one-hit-per-target for the current swing."""
        self.hit_target_ids.add(target_id)
