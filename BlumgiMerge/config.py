"""Blumgi Merge — merge slimes, auto-battle dungeon, 100 stages."""

from __future__ import annotations

from dataclasses import dataclass

# Display
SCREEN_W: int = 960
SCREEN_H: int = 640
FPS: int = 60
TITLE: str = "Blumgi Merge"

# Board
COLS: int = 5
ROWS: int = 4
CELL: int = 96
BOARD_X: int = 48
BOARD_Y: int = 110
MAX_TIER: int = 10

# Economy / combat
START_GOLD: int = 40
SLIME_COST: int = 10
COST_GROWTH: float = 1.0  # flat for simplicity; stages raise enemy HP
FIGHT_REWARD_BASE: int = 18

# Colors — vivid candy palette
BG_TOP: tuple[int, int, int] = (70, 40, 120)
BG_BOTTOM: tuple[int, int, int] = (30, 20, 70)
PANEL: tuple[int, int, int] = (45, 30, 90)
PANEL_EDGE: tuple[int, int, int] = (255, 120, 220)
UI: tuple[int, int, int] = (255, 250, 255)
UI_DIM: tuple[int, int, int] = (200, 180, 230)
GOLD: tuple[int, int, int] = (255, 210, 60)
BTN: tuple[int, int, int] = (80, 220, 140)
BTN_BUY: tuple[int, int, int] = (90, 180, 255)
BTN_FIGHT: tuple[int, int, int] = (255, 110, 90)

# Tier body colors (vivid)
TIER_COLORS: tuple[tuple[int, int, int], ...] = (
    (90, 255, 140),    # 1 lime
    (80, 200, 255),    # 2 sky
    (255, 110, 200),   # 3 hot pink
    (255, 220, 50),    # 4 yellow
    (180, 90, 255),    # 5 violet
    (255, 140, 60),    # 6 orange
    (60, 255, 230),    # 7 aqua
    (255, 70, 110),    # 8 crimson
    (160, 255, 80),    # 9 neon green
    (255, 255, 120),   # 10 gold legendary
)

TIER_NAMES: tuple[str, ...] = (
    "Blob", "Sprout", "Bouncer", "Zapling", "Thorn",
    "Blazer", "Aqua Knight", "Crimson", "Overlord", "Blumgi King",
)

# Per-tier DPS / HP contribution in battle
TIER_DPS: tuple[int, ...] = (3, 7, 14, 26, 45, 72, 110, 165, 240, 360)
TIER_HP: tuple[int, ...] = (20, 35, 55, 85, 125, 180, 250, 340, 460, 620)

TOTAL_STAGES: int = 100


@dataclass(frozen=True, slots=True)
class StageSpec:
    """Enemy wave for one dungeon floor."""

    number: int
    enemy_hp: int
    enemy_dps: int
    reward: int
    name: str


def stage_spec(n: int) -> StageSpec:
    """Escalating 1..100 dungeon floors."""
    if n < 1 or n > TOTAL_STAGES:
        raise ValueError(f"stage {n} out of range")
    # Mild early curve, steeper late game.
    hp = int(40 + n * 18 + (n ** 1.35) * 2.2)
    dps = int(2 + n * 0.85 + (n ** 1.2) * 0.15)
    reward = int(FIGHT_REWARD_BASE + n * 2.4 + (n // 10) * 8)
    titles = (
        "Slime Gate", "Moss Hall", "Candy Crypt", "Neon Nest", "Boss Door"
    )
    name = f"{titles[(n - 1) % len(titles)]} {n}"
    if n % 10 == 0:
        name = f"BOSS Floor {n}"
        hp = int(hp * 1.55)
        dps = int(dps * 1.25)
        reward = int(reward * 1.8)
    return StageSpec(n, hp, dps, reward, name)
