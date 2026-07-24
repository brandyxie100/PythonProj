"""Stage map definitions for Tank 1990 (26×26 grids)."""

from __future__ import annotations

import config as cfg

# Legend:
# . empty   # brick   @ steel   ~ water   % grass   = ice   E eagle (marks 2×2)
_CHAR = {
    ".": cfg.T_EMPTY,
    "#": cfg.T_BRICK,
    "@": cfg.T_STEEL,
    "~": cfg.T_WATER,
    "%": cfg.T_GRASS,
    "=": cfg.T_ICE,
    "E": cfg.T_BASE,
}


def _parse(rows: list[str]) -> list[list[int]]:
    """Parse 26 string rows into a tile grid; expand E into a 2×2 base."""
    assert len(rows) == cfg.MAP_H, f"need {cfg.MAP_H} rows"
    grid = [[_CHAR.get(c, cfg.T_EMPTY) for c in row] for row in rows]
    for ty, row in enumerate(rows):
        assert len(row) == cfg.MAP_W, f"row {ty} len {len(row)}"
        for tx, c in enumerate(row):
            if c == "E":
                for dy in range(2):
                    for dx in range(2):
                        if ty + dy < cfg.MAP_H and tx + dx < cfg.MAP_W:
                            grid[ty + dy][tx + dx] = cfg.T_BASE
    return grid


def _base_row_pair(above: str, eagle_row: str) -> list[str]:
    """Helper unused — stages written fully."""
    return [above, eagle_row]


# Each stage: 26 rows × 26 chars. Player spawn is always near bottom center.
# Enemy spawn corridors kept open at top: cols 0-1, 12-13, 24-25 roughly.

STAGE_1 = _parse([
    "..........................",
    "..........................",
    "..##..##..##..##..##..##..",
    "..##..##..##..##..##..##..",
    "..##..##..##..##..##..##..",
    "..##..##..##@@##..##..##..",
    "..##..##..##@@##..##..##..",
    "..........................",
    "..........................",
    "..##..######..######..##..",
    "..##..######..######..##..",
    "..##..............##..##..",
    "@@@@@@......##......@@@@@@",
    "@@@@@@......##......@@@@@@",
    "..##..............##..##..",
    "..##..######..######..##..",
    "..##..######..######..##..",
    "..........................",
    "..........................",
    "..##..##..##..##..##..##..",
    "..##..##..##..##..##..##..",
    "..##..##..........##..##..",
    "..##..##...####...##..##..",
    "...........#EE#...........",
    "...........#EE#...........",
    "..........................",
])

STAGE_2 = _parse([
    "..........................",
    "..........................",
    ".####....####....####.....",
    ".####....####....####.....",
    "..........................",
    "....@@@@@@....@@@@@@......",
    "....@@@@@@....@@@@@@......",
    "..........................",
    ".##~~~~~~~~~~~~~~~~##.....",
    ".##~~~~~~~~~~~~~~~~##.....",
    ".##......####......##.....",
    ".##......####......##.....",
    "..........................",
    "%%%%..##......##..%%%%....",
    "%%%%..##......##..%%%%....",
    "......##@@@@@@##..........",
    "......##@@@@@@##..........",
    "..........................",
    ".####............####.....",
    ".####............####.....",
    "..........................",
    "......##...####...##......",
    "......##...#EE#...##......",
    "...........#EE#...........",
    "..........................",
    "..........................",
])

STAGE_3 = _parse([
    "..........................",
    "..@@..................@@..",
    "..@@..##############..@@..",
    "......##..........##......",
    "......##..@@@@@@..##......",
    "..##..##..@@@@@@..##..##..",
    "..##..................##..",
    "..##..%%%%..%%%%..%%%%##..",
    "......%%%%..%%%%..%%%%....",
    "##########......##########",
    "##########......##########",
    "..........................",
    "~~##~~##~~##~~##~~##~~##~~",
    "~~##~~##~~##~~##~~##~~##~~",
    "..........................",
    "....##..##......##..##....",
    "....##..##@@@@@@##..##....",
    "........##@@@@@@##........",
    "##########################",
    "..........................",
    "..##..##..........##..##..",
    "..##..##...####...##..##..",
    "...........#EE#...........",
    "...........#EE#...........",
    "..........................",
    "..........................",
])

STAGE_4 = _parse([
    "..........................",
    "..........................",
    "========........========..",
    "========........========..",
    "....##............##......",
    "....##@@@@@@@@@@@@##......",
    "........##....##..........",
    "########~~....~~##########",
    "########~~....~~##########",
    "........##....##..........",
    "..%%%%............%%%%....",
    "..%%%%..########..%%%%....",
    "........########..........",
    "@@....................@@..",
    "@@..################..@@..",
    "....##............##......",
    "....##..########..##......",
    "........########..........",
    "====................====..",
    "====....##....##....====..",
    "........##....##..........",
    "......##...####...##......",
    "......##...#EE#...##......",
    "...........#EE#...........",
    "..........................",
    "..........................",
])

STAGE_5 = _parse([
    "..........................",
    "..##..##..##..##..##..##..",
    "..##@@##..##..##..##@@##..",
    "......##..........##......",
    "######~~##########~~######",
    "......~~..........~~......",
    "..%%%%##############%%%%..",
    "..%%%%..............%%%%..",
    "..........@@@@@@..........",
    "..##......@@@@@@......##..",
    "..##..................##..",
    "########..........########",
    "~~~~~~~~..######..~~~~~~~~",
    "~~~~~~~~..######..~~~~~~~~",
    "########..........########",
    "..##..................##..",
    "..##......@@@@@@......##..",
    "..........@@@@@@..........",
    "..%%%%..............%%%%..",
    "..%%%%##############%%%%..",
    "..........................",
    "......##...####...##......",
    "......##...#EE#...##......",
    "...........#EE#...........",
    "..........................",
    "..........................",
])


def _mirror_variety(base: list[list[int]], seed: int) -> list[list[int]]:
    """Derive later stages by flipping / thickening bricks."""
    g = [row[:] for row in base]
    if seed % 2 == 1:
        g = [list(reversed(row)) for row in g]
    if seed % 3 == 0:
        for ty in range(2, 20):
            for tx in range(2, 24):
                if g[ty][tx] == cfg.T_EMPTY and (tx + ty + seed) % 11 == 0:
                    g[ty][tx] = cfg.T_BRICK
    if seed % 4 == 0:
        for ty in range(4, 18):
            for tx in range(4, 22):
                if g[ty][tx] == cfg.T_BRICK and (tx * ty + seed) % 17 == 0:
                    g[ty][tx] = cfg.T_STEEL
    # Keep spawns and base clear corridors
    for tx in (0, 1, 12, 13, 24, 25):
        for ty in range(0, 3):
            g[ty][tx] = cfg.T_EMPTY
    for ty in range(23, 26):
        for tx in range(11, 15):
            if not (12 <= tx <= 13 and 24 <= ty <= 25):
                if g[ty][tx] == cfg.T_BASE:
                    continue
    # Ensure eagle
    for dy in range(2):
        for dx in range(2):
            g[24 + dy][12 + dx] = cfg.T_BASE
    # Clear player spawn
    for ty in range(22, 24):
        for tx in range(8, 11):
            if g[ty][tx] != cfg.T_BASE:
                g[ty][tx] = cfg.T_EMPTY
    return g


_HANDCRAFTED = [STAGE_1, STAGE_2, STAGE_3, STAGE_4, STAGE_5]


def get_stage(index: int) -> list[list[int]]:
    """Return a deep copy of stage grid (1-based index clamped)."""
    i = max(1, min(cfg.TOTAL_STAGES, index)) - 1
    if i < len(_HANDCRAFTED):
        return [row[:] for row in _HANDCRAFTED[i]]
    base = _HANDCRAFTED[i % len(_HANDCRAFTED)]
    return _mirror_variety(base, i + 7)


# Classic enemy mix per stage: list of kinds for the 20 spawns.
def enemy_queue(stage: int) -> list[str]:
    """Build the ordered list of 20 enemy tank types for a stage."""
    s = max(1, stage)
    basic = max(4, 14 - s)
    fast = min(8, 2 + s // 2)
    power = min(6, s // 2)
    armor = min(6, max(0, s - 3))
    # Normalize to 20
    total = basic + fast + power + armor
    while total < cfg.ENEMIES_PER_STAGE:
        basic += 1
        total += 1
    while total > cfg.ENEMIES_PER_STAGE:
        if basic > 0:
            basic -= 1
        elif fast > 0:
            fast -= 1
        else:
            power -= 1
        total -= 1
    q = (["basic"] * basic + ["fast"] * fast + ["power"] * power + ["armor"] * armor)
    # Interleave a bit for classic pacing
    out: list[str] = []
    pools = {"basic": basic, "fast": fast, "power": power, "armor": armor}
    order = ["basic", "fast", "basic", "power", "basic", "armor", "fast", "power"]
    i = 0
    while len(out) < cfg.ENEMIES_PER_STAGE:
        kind = order[i % len(order)]
        if pools[kind] > 0:
            out.append(kind)
            pools[kind] -= 1
        i += 1
        if i > 200:
            for k, n in pools.items():
                out.extend([k] * n)
            break
    return out[: cfg.ENEMIES_PER_STAGE]
