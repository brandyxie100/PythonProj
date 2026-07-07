"""Terrain and level generation for stage mode."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

import config as c


@dataclass(frozen=True, slots=True)
class Ramp:
    """Sloped walkable segment."""

    x1: float
    y1: float
    x2: float
    y2: float

    def contains_x(self, x: float) -> bool:
        """Return True if x lies within ramp span."""
        lo = min(self.x1, self.x2)
        hi = max(self.x1, self.x2)
        return lo <= x <= hi

    def y_at(self, x: float) -> float:
        """Interpolate y on ramp at given x."""
        if self.x2 == self.x1:
            return min(self.y1, self.y2)
        t = (x - self.x1) / (self.x2 - self.x1)
        return self.y1 + (self.y2 - self.y1) * t


@dataclass(frozen=True, slots=True)
class Obstacle:
    """Hazard zone that applies damage while touched."""

    rect: pygame.Rect
    dps: float


@dataclass(frozen=True, slots=True)
class EnemySpawn:
    """Enemy setup used for each level."""

    color: tuple[int, int, int]
    weapon_name: str
    speed_multiplier: float
    health_multiplier: float
    aggressiveness: float


@dataclass(frozen=True, slots=True)
class Arena:
    """Terrain geometry for one level."""

    floor_y: float
    platforms: tuple[pygame.Rect, ...]
    ramps: tuple[Ramp, ...]
    obstacles: tuple[Obstacle, ...]

    def _surface_candidates(self, x: float) -> list[float]:
        """Collect all walkable surface heights under horizontal position."""
        candidates = [self.floor_y]
        for platform in self.platforms:
            if platform.left <= x <= platform.right:
                candidates.append(float(platform.top))
        for ramp in self.ramps:
            if ramp.contains_x(x):
                candidates.append(ramp.y_at(x))
        return candidates

    def resolve_ground(
        self,
        x: float,
        current_y: float,
        previous_foot_y: float,
        vy: float,
    ) -> tuple[float, float, bool]:
        """Project a falling stickman onto nearest surface if landing this frame."""
        foot_y = current_y + c.LEG_LEN
        best_surface: float | None = None
        for surface_y in self._surface_candidates(x):
            if foot_y >= surface_y and previous_foot_y <= surface_y + 18.0 and vy >= 0:
                if best_surface is None or surface_y < best_surface:
                    best_surface = surface_y
        if best_surface is None:
            return current_y, vy, False
        return best_surface - c.LEG_LEN, 0.0, True

    def obstacle_damage_at(self, point: tuple[float, float]) -> float:
        """Sum obstacle DPS at the provided point."""
        total = 0.0
        for obstacle in self.obstacles:
            if obstacle.rect.collidepoint(point):
                total += obstacle.dps
        return total

    def draw(self, surf: pygame.Surface) -> None:
        """Draw all terrain primitives for the active arena."""
        pygame.draw.rect(
            surf,
            c.GROUND_COLOR,
            pygame.Rect(0, int(self.floor_y), c.SCREEN_W, c.SCREEN_H - int(self.floor_y)),
        )
        for platform in self.platforms:
            pygame.draw.rect(surf, c.PLATFORM_COLOR, platform, border_radius=6)
        for ramp in self.ramps:
            pygame.draw.line(
                surf,
                c.RAMP_COLOR,
                (int(ramp.x1), int(ramp.y1)),
                (int(ramp.x2), int(ramp.y2)),
                9,
            )
        for obstacle in self.obstacles:
            pygame.draw.rect(surf, c.OBSTACLE_COLOR, obstacle.rect, border_radius=4)
            pygame.draw.rect(surf, (255, 240, 240), obstacle.rect, 1, border_radius=4)


@dataclass(frozen=True, slots=True)
class LevelConfig:
    """Complete content for one stage level."""

    number: int
    arena: Arena
    player_spawn: tuple[float, float]
    enemy_spawns: tuple[tuple[EnemySpawn, tuple[float, float]], ...]
    reward_coins: int


def _base_floor() -> float:
    return float(c.SCREEN_H - 68)


def level_config(level_number: int) -> LevelConfig:
    """Build one of the six stage levels with increasing complexity."""
    floor = _base_floor()
    if level_number < 1 or level_number > 6:
        raise ValueError(f"Unsupported level: {level_number}")

    if level_number == 1:
        arena = Arena(
            floor_y=floor,
            platforms=(pygame.Rect(450, 455, 180, 16),),
            ramps=(),
            obstacles=(),
        )
        enemies = (
            (EnemySpawn(c.ENEMY_RED, "stick", 0.9, 1.0, 0.9), (900.0, floor - c.LEG_LEN)),
        )
    elif level_number == 2:
        arena = Arena(
            floor_y=floor,
            platforms=(
                pygame.Rect(280, 500, 170, 16),
                pygame.Rect(720, 430, 190, 16),
            ),
            ramps=(Ramp(130, floor, 320, 500),),
            obstacles=(Obstacle(pygame.Rect(560, int(floor) - 18, 70, 18), 18.0),),
        )
        enemies = (
            (EnemySpawn(c.ENEMY_YELLOW, "sword", 1.0, 1.05, 1.0), (845.0, floor - c.LEG_LEN)),
            (EnemySpawn(c.ENEMY_RED, "stick", 1.0, 1.0, 0.95), (980.0, floor - c.LEG_LEN)),
        )
    elif level_number == 3:
        arena = Arena(
            floor_y=floor,
            platforms=(
                pygame.Rect(210, 470, 160, 16),
                pygame.Rect(520, 410, 170, 16),
                pygame.Rect(840, 460, 150, 16),
            ),
            ramps=(Ramp(100, floor, 250, 470), Ramp(690, floor, 860, 460)),
            obstacles=(Obstacle(pygame.Rect(420, int(floor) - 18, 85, 18), 22.0),),
        )
        enemies = (
            (EnemySpawn(c.ENEMY_RED, "pickaxe", 1.05, 1.15, 1.1), (930.0, floor - c.LEG_LEN)),
            (EnemySpawn(c.ENEMY_YELLOW, "sword", 1.03, 1.1, 1.0), (760.0, floor - c.LEG_LEN)),
        )
    elif level_number == 4:
        arena = Arena(
            floor_y=floor,
            platforms=(
                pygame.Rect(170, 520, 150, 16),
                pygame.Rect(390, 460, 155, 16),
                pygame.Rect(645, 405, 170, 16),
                pygame.Rect(940, 350, 140, 16),
            ),
            ramps=(Ramp(300, floor, 450, 460), Ramp(820, floor, 980, 350)),
            obstacles=(
                Obstacle(pygame.Rect(560, int(floor) - 18, 72, 18), 24.0),
                Obstacle(pygame.Rect(725, int(floor) - 18, 72, 18), 24.0),
            ),
        )
        enemies = (
            (EnemySpawn(c.ENEMY_RED, "hammer", 1.08, 1.25, 1.2), (960.0, 350 - c.LEG_LEN)),
            (EnemySpawn(c.ENEMY_YELLOW, "pickaxe", 1.08, 1.18, 1.1), (760.0, 405 - c.LEG_LEN)),
            (EnemySpawn(c.ENEMY_BLUE, "stick", 1.02, 1.1, 0.95), (885.0, floor - c.LEG_LEN)),
        )
    elif level_number == 5:
        arena = Arena(
            floor_y=floor,
            platforms=(
                pygame.Rect(150, 530, 125, 16),
                pygame.Rect(330, 470, 130, 16),
                pygame.Rect(520, 420, 145, 16),
                pygame.Rect(740, 365, 150, 16),
                pygame.Rect(980, 315, 120, 16),
            ),
            ramps=(
                Ramp(40, floor, 180, 530),
                Ramp(255, 530, 365, 470),
                Ramp(650, floor, 805, 365),
            ),
            obstacles=(
                Obstacle(pygame.Rect(470, int(floor) - 18, 82, 18), 28.0),
                Obstacle(pygame.Rect(600, int(floor) - 18, 82, 18), 28.0),
            ),
        )
        enemies = (
            (EnemySpawn(c.ENEMY_RED, "hammer", 1.15, 1.38, 1.28), (1010.0, 315 - c.LEG_LEN)),
            (EnemySpawn(c.ENEMY_YELLOW, "sword", 1.12, 1.23, 1.18), (830.0, 365 - c.LEG_LEN)),
            (EnemySpawn(c.ENEMY_BLUE, "pickaxe", 1.1, 1.2, 1.1), (590.0, 420 - c.LEG_LEN)),
        )
    else:  # level 6
        arena = Arena(
            floor_y=floor,
            platforms=(
                pygame.Rect(90, 542, 120, 14),
                pygame.Rect(230, 500, 120, 14),
                pygame.Rect(375, 455, 125, 14),
                pygame.Rect(530, 410, 130, 14),
                pygame.Rect(705, 365, 130, 14),
                pygame.Rect(885, 320, 125, 14),
                pygame.Rect(1040, 280, 110, 14),
            ),
            ramps=(
                Ramp(0, floor, 100, 542),
                Ramp(210, 542, 300, 500),
                Ramp(500, floor, 700, 365),
                Ramp(845, floor, 1030, 280),
            ),
            obstacles=(
                Obstacle(pygame.Rect(280, int(floor) - 18, 76, 18), 32.0),
                Obstacle(pygame.Rect(430, int(floor) - 18, 76, 18), 32.0),
                Obstacle(pygame.Rect(600, int(floor) - 18, 76, 18), 32.0),
                Obstacle(pygame.Rect(770, int(floor) - 18, 76, 18), 32.0),
            ),
        )
        enemies = (
            (EnemySpawn(c.ENEMY_RED, "hammer", 1.2, 1.55, 1.35), (1065.0, 280 - c.LEG_LEN)),
            (EnemySpawn(c.ENEMY_YELLOW, "pickaxe", 1.18, 1.42, 1.3), (915.0, 320 - c.LEG_LEN)),
            (EnemySpawn(c.ENEMY_BLUE, "sword", 1.16, 1.35, 1.2), (735.0, 365 - c.LEG_LEN)),
            (EnemySpawn(c.ENEMY_RED, "stick", 1.14, 1.25, 1.15), (555.0, 410 - c.LEG_LEN)),
        )

    player_spawn = (120.0, floor - c.LEG_LEN)
    reward = c.COIN_REWARD_PER_LEVEL[level_number - 1]
    return LevelConfig(
        number=level_number,
        arena=arena,
        player_spawn=player_spawn,
        enemy_spawns=enemies,
        reward_coins=reward,
    )
