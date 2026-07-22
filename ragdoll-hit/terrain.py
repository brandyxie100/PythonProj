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
        """Draw terrain with posts, platform edges, ramps, and hazards."""
        # Floor
        pygame.draw.rect(
            surf,
            c.GROUND_COLOR,
            pygame.Rect(0, int(self.floor_y), c.SCREEN_W, c.SCREEN_H - int(self.floor_y)),
        )
        # Subtle floor lip
        pygame.draw.line(
            surf,
            (98, 108, 124),
            (0, int(self.floor_y)),
            (c.SCREEN_W, int(self.floor_y)),
            3,
        )

        # Support posts under elevated platforms for a more elaborate look.
        for platform in self.platforms:
            if platform.top >= self.floor_y - 8:
                continue
            post_w = 10 if platform.width < 100 else 14
            for frac in (0.18, 0.82):
                px = int(platform.left + platform.width * frac - post_w / 2)
                pygame.draw.rect(
                    surf,
                    (52, 58, 70),
                    pygame.Rect(px, platform.bottom, post_w, int(self.floor_y) - platform.bottom),
                )

        for platform in self.platforms:
            pygame.draw.rect(surf, c.PLATFORM_COLOR, platform, border_radius=5)
            # Top edge highlight — reads as a walkable ledge.
            pygame.draw.line(
                surf,
                (140, 156, 180),
                (platform.left + 4, platform.top + 2),
                (platform.right - 4, platform.top + 2),
                2,
            )

        for ramp in self.ramps:
            pygame.draw.line(
                surf,
                (70, 78, 94),
                (int(ramp.x1), int(ramp.y1) + 3),
                (int(ramp.x2), int(ramp.y2) + 3),
                12,
            )
            pygame.draw.line(
                surf,
                c.RAMP_COLOR,
                (int(ramp.x1), int(ramp.y1)),
                (int(ramp.x2), int(ramp.y2)),
                10,
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


def _plat(x: int, y: int, w: int, h: int = 16) -> pygame.Rect:
    """Shorthand for a walkable platform rect."""
    return pygame.Rect(x, y, w, h)


def level_config(level_number: int) -> LevelConfig:
    """Build one of the six stage levels with increasing vertical combat space."""
    floor = _base_floor()
    if level_number < 1 or level_number > 6:
        raise ValueError(f"Unsupported level: {level_number}")

    # Jump reach ~150px (single) / ~280px (double). Keep step gaps reachable.
    if level_number == 1:
        # Training yard — low platforms + one ramp for first airborne fights.
        arena = Arena(
            floor_y=floor,
            platforms=(
                _plat(260, 540, 140),
                _plat(460, 480, 170),
                _plat(700, 520, 130),
                _plat(880, 450, 160),
                _plat(540, 380, 110),  # high perch for double-jump duels
            ),
            ramps=(
                Ramp(80, floor, 270, 540),
                Ramp(830, floor, 960, 450),
            ),
            obstacles=(),
        )
        enemies = (
            (EnemySpawn(c.ENEMY_RED, "javelin", 0.9, 1.0, 0.9), (920.0, 450 - c.LEG_LEN)),
        )
    elif level_number == 2:
        # Twin towers — mirrored sides with a bridge and hazard ditch.
        arena = Arena(
            floor_y=floor,
            platforms=(
                _plat(120, 530, 130),
                _plat(300, 470, 120),
                _plat(480, 420, 200),  # center bridge
                _plat(740, 470, 120),
                _plat(920, 530, 130),
                _plat(200, 380, 100),
                _plat(860, 380, 100),
                _plat(540, 330, 100),  # high mid island
            ),
            ramps=(
                Ramp(40, floor, 160, 530),
                Ramp(1020, floor, 1140, 530),
                Ramp(400, 470, 500, 420),
                Ramp(660, 420, 760, 470),
            ),
            obstacles=(
                Obstacle(pygame.Rect(560, int(floor) - 20, 90, 20), 20.0),
            ),
        )
        enemies = (
            (EnemySpawn(c.ENEMY_YELLOW, "spear", 1.0, 1.05, 1.0), (860.0, 380 - c.LEG_LEN)),
            (EnemySpawn(c.ENEMY_RED, "bow", 1.0, 1.0, 0.95), (980.0, floor - c.LEG_LEN)),
        )
    elif level_number == 3:
        # Stepped arena — ascending left→right with mid floating pads.
        arena = Arena(
            floor_y=floor,
            platforms=(
                _plat(90, 540, 120),
                _plat(250, 490, 115),
                _plat(410, 440, 120),
                _plat(580, 390, 130),
                _plat(760, 340, 125),
                _plat(940, 400, 140),
                _plat(320, 360, 90),   # floating side pad
                _plat(680, 280, 95),   # high combat perch
                _plat(500, 520, 100),  # low mid pad
            ),
            ramps=(
                Ramp(30, floor, 130, 540),
                Ramp(200, 540, 280, 490),
                Ramp(360, 490, 440, 440),
                Ramp(530, 440, 610, 390),
                Ramp(700, 390, 790, 340),
                Ramp(860, floor, 980, 400),
            ),
            obstacles=(
                Obstacle(pygame.Rect(450, int(floor) - 18, 70, 18), 22.0),
                Obstacle(pygame.Rect(640, int(floor) - 18, 70, 18), 22.0),
            ),
        )
        enemies = (
            (EnemySpawn(c.ENEMY_RED, "axe", 1.05, 1.15, 1.1), (800.0, 340 - c.LEG_LEN)),
            (EnemySpawn(c.ENEMY_YELLOW, "broadsword", 1.03, 1.1, 1.0), (980.0, 400 - c.LEG_LEN)),
        )
    elif level_number == 4:
        # Fortress — thick ledges, stacked towers, gap jumps.
        arena = Arena(
            floor_y=floor,
            platforms=(
                _plat(60, 540, 150, 18),
                _plat(260, 490, 120),
                _plat(430, 440, 110),
                _plat(590, 390, 150, 18),  # thick battlement
                _plat(790, 340, 120),
                _plat(960, 290, 140, 18),  # high keep
                _plat(180, 400, 90),
                _plat(700, 460, 95),
                _plat(860, 500, 100),
                _plat(480, 320, 85),       # floating sparring pad
                _plat(340, 560, 80),
            ),
            ramps=(
                Ramp(20, floor, 100, 540),
                Ramp(210, 540, 280, 490),
                Ramp(380, 490, 450, 440),
                Ramp(540, 440, 610, 390),
                Ramp(740, 390, 820, 340),
                Ramp(910, 340, 990, 290),
                Ramp(880, floor, 1020, 500),
            ),
            obstacles=(
                Obstacle(pygame.Rect(500, int(floor) - 20, 75, 20), 26.0),
                Obstacle(pygame.Rect(680, int(floor) - 20, 75, 20), 26.0),
                Obstacle(pygame.Rect(360, int(floor) - 18, 55, 18), 24.0),
            ),
        )
        enemies = (
            (EnemySpawn(c.ENEMY_RED, "trident", 1.08, 1.25, 1.2), (1010.0, 290 - c.LEG_LEN)),
            (EnemySpawn(c.ENEMY_YELLOW, "axe", 1.08, 1.18, 1.1), (650.0, 390 - c.LEG_LEN)),
            (EnemySpawn(c.ENEMY_BLUE, "spear", 1.02, 1.1, 0.95), (900.0, floor - c.LEG_LEN)),
        )
    elif level_number == 5:
        # Sky ladders — staggered vertical routes, many mid-air islands.
        arena = Arena(
            floor_y=floor,
            platforms=(
                _plat(70, 545, 110),
                _plat(220, 495, 100),
                _plat(370, 445, 105),
                _plat(520, 395, 110),
                _plat(680, 345, 115),
                _plat(850, 295, 120),
                _plat(1010, 255, 110),
                _plat(150, 400, 85),
                _plat(300, 350, 80),
                _plat(460, 300, 85),
                _plat(620, 250, 80),
                _plat(780, 420, 90),
                _plat(940, 470, 95),
                _plat(400, 540, 90),
                _plat(740, 540, 90),
            ),
            ramps=(
                Ramp(20, floor, 100, 545),
                Ramp(180, 545, 250, 495),
                Ramp(320, 495, 400, 445),
                Ramp(470, 445, 550, 395),
                Ramp(630, 395, 710, 345),
                Ramp(800, 345, 880, 295),
                Ramp(960, 295, 1040, 255),
                Ramp(880, floor, 980, 470),
            ),
            obstacles=(
                Obstacle(pygame.Rect(280, int(floor) - 18, 70, 18), 28.0),
                Obstacle(pygame.Rect(520, int(floor) - 18, 70, 18), 28.0),
                Obstacle(pygame.Rect(760, int(floor) - 18, 70, 18), 28.0),
            ),
        )
        enemies = (
            (EnemySpawn(c.ENEMY_RED, "trident", 1.15, 1.38, 1.28), (1055.0, 255 - c.LEG_LEN)),
            (EnemySpawn(c.ENEMY_YELLOW, "broadsword", 1.12, 1.23, 1.18), (720.0, 345 - c.LEG_LEN)),
            (EnemySpawn(c.ENEMY_BLUE, "axe", 1.1, 1.2, 1.1), (560.0, 395 - c.LEG_LEN)),
        )
    else:  # level 6 — summit gauntlet
        arena = Arena(
            floor_y=floor,
            platforms=(
                _plat(40, 550, 100),
                _plat(170, 510, 95),
                _plat(300, 470, 95),
                _plat(430, 430, 100),
                _plat(570, 390, 105),
                _plat(720, 350, 100),
                _plat(860, 310, 100),
                _plat(1000, 270, 110, 18),  # summit
                _plat(110, 430, 75),
                _plat(250, 390, 75),
                _plat(390, 350, 75),
                _plat(530, 310, 75),
                _plat(670, 270, 75),
                _plat(810, 230, 80),        # double-jump sky pad
                _plat(940, 400, 85),
                _plat(640, 500, 90),
                _plat(480, 540, 85),
                _plat(200, 560, 80),
            ),
            ramps=(
                Ramp(0, floor, 70, 550),
                Ramp(140, 550, 200, 510),
                Ramp(260, 510, 330, 470),
                Ramp(390, 470, 460, 430),
                Ramp(530, 430, 600, 390),
                Ramp(670, 390, 750, 350),
                Ramp(810, 350, 890, 310),
                Ramp(950, 310, 1030, 270),
                Ramp(900, floor, 1000, 400),
                Ramp(560, floor, 680, 500),
            ),
            obstacles=(
                Obstacle(pygame.Rect(250, int(floor) - 18, 65, 18), 32.0),
                Obstacle(pygame.Rect(420, int(floor) - 18, 65, 18), 32.0),
                Obstacle(pygame.Rect(600, int(floor) - 18, 65, 18), 32.0),
                Obstacle(pygame.Rect(780, int(floor) - 18, 65, 18), 32.0),
                Obstacle(pygame.Rect(340, 470, 40, 12), 20.0),  # mid-air hazard
            ),
        )
        enemies = (
            (EnemySpawn(c.ENEMY_RED, "trident", 1.2, 1.55, 1.35), (1050.0, 270 - c.LEG_LEN)),
            (EnemySpawn(c.ENEMY_YELLOW, "axe", 1.18, 1.42, 1.3), (840.0, 230 - c.LEG_LEN)),
            (EnemySpawn(c.ENEMY_BLUE, "broadsword", 1.16, 1.35, 1.2), (760.0, 350 - c.LEG_LEN)),
            (EnemySpawn(c.ENEMY_RED, "javelin", 1.14, 1.25, 1.15), (500.0, 430 - c.LEG_LEN)),
        )

    player_spawn = (100.0, floor - c.LEG_LEN)
    reward = c.COIN_REWARD_PER_LEVEL[level_number - 1]
    return LevelConfig(
        number=level_number,
        arena=arena,
        player_spawn=player_spawn,
        enemy_spawns=enemies,
        reward_coins=reward,
    )
