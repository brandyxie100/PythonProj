"""Pixel tile rendering and map collision helpers."""

from __future__ import annotations

import pygame as pg

import config as cfg


def logical_to_screen(x: float, y: float) -> tuple[int, int]:
    """Convert logical map pixels to screen pixels."""
    return int(x * cfg.SCALE), int(y * cfg.SCALE)


def make_tile_surfaces() -> dict[int, pg.Surface]:
    """Build fine tiles plus tank-sized brick/steel unit faces."""
    t = cfg.TILE
    tiles: dict[int, pg.Surface] = {}

    empty = pg.Surface((t, t))
    empty.fill(cfg.BLACK)
    tiles[cfg.T_EMPTY] = empty

    # Fine brick kept for rare partial cells; unit face is the play standard.
    brick = pg.Surface((t, t))
    brick.fill(cfg.BRICK_R)
    for y in range(0, t, 2):
        for x in range(0, t, 4):
            ox = 2 if (y // 2) % 2 else 0
            pg.draw.rect(brick, cfg.BRICK_DK, pg.Rect(x + ox, y, 2, 2))
    pg.draw.line(brick, cfg.BRICK_DK, (0, t // 2 - 1), (t, t // 2 - 1))
    tiles[cfg.T_BRICK] = brick

    steel = pg.Surface((t, t))
    steel.fill(cfg.STEEL)
    pg.draw.rect(steel, cfg.STEEL_DK, pg.Rect(0, 0, t, t), 1)
    pg.draw.line(steel, cfg.UI_WHITE, (1, 1), (t - 2, 1))
    pg.draw.line(steel, cfg.UI_WHITE, (1, 1), (1, t - 2))
    tiles[cfg.T_STEEL] = steel

    water = pg.Surface((t, t))
    water.fill(cfg.WATER_A)
    for i in range(0, t, 2):
        pg.draw.line(water, cfg.WATER_B, (0, i), (t, i))
    tiles[cfg.T_WATER] = water

    grass = pg.Surface((t, t))
    grass.fill(cfg.BLACK)
    for ox, oy in ((1, 1), (4, 2), (2, 5), (5, 6), (6, 3)):
        pg.draw.line(grass, cfg.GRASS, (ox, oy), (ox + 1, oy - 2))
        pg.draw.line(grass, cfg.GRASS_DK, (ox + 1, oy), (ox + 2, oy - 1))
    tiles[cfg.T_GRASS] = grass

    ice = pg.Surface((t, t))
    ice.fill(cfg.ICE)
    pg.draw.line(ice, cfg.ICE_DK, (0, 2), (t, 2))
    pg.draw.line(ice, cfg.UI_WHITE, (1, 5), (6, 5))
    tiles[cfg.T_ICE] = ice

    base = pg.Surface((t, t))
    base.fill(cfg.BLACK)
    tiles[cfg.T_BASE] = base

    # Tank-sized wall blocks (one bullet destroys one of these).
    u = cfg.BRICK_UNIT
    brick_unit = pg.Surface((u, u))
    brick_unit.fill(cfg.BRICK_R)
    mortar = cfg.BRICK_DK
    # Four classic brick courses across the tank footprint.
    for row in range(4):
        y = row * (u // 4)
        h = u // 4
        pg.draw.line(brick_unit, mortar, (0, y), (u, y))
        offset = (u // 4) if row % 2 else 0
        for x in range(offset, u + u // 2, u // 2):
            pg.draw.line(brick_unit, mortar, (x % u, y), (x % u, y + h))
    pg.draw.rect(brick_unit, mortar, pg.Rect(0, 0, u, u), 1)
    tiles["brick_unit"] = brick_unit

    steel_unit = pg.Surface((u, u))
    steel_unit.fill(cfg.STEEL)
    pg.draw.rect(steel_unit, cfg.STEEL_DK, pg.Rect(0, 0, u, u), 1)
    pg.draw.line(steel_unit, cfg.UI_WHITE, (1, 1), (u - 2, 1))
    pg.draw.line(steel_unit, cfg.UI_WHITE, (1, 1), (1, u - 2))
    pg.draw.line(steel_unit, cfg.STEEL_DK, (u // 2, 0), (u // 2, u))
    pg.draw.line(steel_unit, cfg.STEEL_DK, (0, u // 2), (u, u // 2))
    tiles["steel_unit"] = steel_unit

    return tiles


class StageMap:
    """Mutable 26×26 tile map with brick destruction and base fortify."""

    def __init__(self, grid: list[list[int]]) -> None:
        """Copy stage grid and normalize walls onto the tank-sized grid."""
        self.grid = [row[:] for row in grid]
        self._snap_walls_to_units()
        self.tiles = make_tile_surfaces()
        self.water_phase = 0.0
        self.base_alive = True
        self.shovel_left = 0.0
        self._shovel_was_active = False

    def _snap_walls_to_units(self) -> None:
        """Expand any brick/steel so each wall occupies a full tank footprint."""
        visited: set[tuple[int, int]] = set()
        for ty in range(cfg.MAP_H):
            for tx in range(cfg.MAP_W):
                v = self.grid[ty][tx]
                if v not in (cfg.T_BRICK, cfg.T_STEEL):
                    continue
                ox, oy = (
                    (tx // cfg.BRICK_CELLS) * cfg.BRICK_CELLS,
                    (ty // cfg.BRICK_CELLS) * cfg.BRICK_CELLS,
                )
                if (ox, oy) in visited:
                    continue
                visited.add((ox, oy))
                for dy in range(cfg.BRICK_CELLS):
                    for dx in range(cfg.BRICK_CELLS):
                        cx, cy = ox + dx, oy + dy
                        if not (0 <= cx < cfg.MAP_W and 0 <= cy < cfg.MAP_H):
                            continue
                        # Don't overwrite water/grass/base/ice with wall fill.
                        if self.grid[cy][cx] in (cfg.T_EMPTY, cfg.T_BRICK, cfg.T_STEEL):
                            self.grid[cy][cx] = v

    def in_bounds(self, tx: int, ty: int) -> bool:
        return 0 <= tx < cfg.MAP_W and 0 <= ty < cfg.MAP_H

    def get(self, tx: int, ty: int) -> int:
        if not self.in_bounds(tx, ty):
            return cfg.T_STEEL
        return self.grid[ty][tx]

    def set(self, tx: int, ty: int, value: int) -> None:
        if self.in_bounds(tx, ty):
            self.grid[ty][tx] = value

    def solid_for_tank(self, tx: int, ty: int) -> bool:
        """Tiles that block tank movement."""
        v = self.get(tx, ty)
        return v in (cfg.T_BRICK, cfg.T_STEEL, cfg.T_WATER, cfg.T_BASE)

    def blocks_bullet(self, tx: int, ty: int) -> bool:
        v = self.get(tx, ty)
        return v in (cfg.T_BRICK, cfg.T_STEEL, cfg.T_BASE)

    def unit_origin(self, tx: int, ty: int) -> tuple[int, int]:
        """Snap fine-tile coords to the tank-sized wall unit origin."""
        return (
            (tx // cfg.BRICK_CELLS) * cfg.BRICK_CELLS,
            (ty // cfg.BRICK_CELLS) * cfg.BRICK_CELLS,
        )

    def damage_wall_at(self, px: float, py: float, power: int) -> bool:
        """Destroy one tank-sized wall unit at the bullet impact point.

        Bricks (and steel at max power) clear a full BRICK_UNIT × BRICK_UNIT
        block — the same footprint as a tank. Returns True if the shot stopped.
        """
        tx, ty = int(px) // cfg.TILE, int(py) // cfg.TILE
        if not self.blocks_bullet(tx, ty):
            return False

        ox, oy = self.unit_origin(tx, ty)
        cells = [
            (ox + dx, oy + dy)
            for dy in range(cfg.BRICK_CELLS)
            for dx in range(cfg.BRICK_CELLS)
        ]
        kinds = {self.get(cx, cy) for cx, cy in cells}

        # Eagle HQ: one hit levels the whole tank-sized base block.
        if cfg.T_BASE in kinds:
            self.base_alive = False
            for cx, cy in cells:
                if self.get(cx, cy) == cfg.T_BASE:
                    self.set(cx, cy, cfg.T_EMPTY)
            # Also clear any remaining base tiles nearby (2×2 eagle).
            for cy in range(cfg.MAP_H):
                for cx in range(cfg.MAP_W):
                    if self.get(cx, cy) == cfg.T_BASE:
                        self.set(cx, cy, cfg.T_EMPTY)
            return True

        if cfg.T_BRICK in kinds:
            for cx, cy in cells:
                if self.get(cx, cy) == cfg.T_BRICK:
                    self.set(cx, cy, cfg.T_EMPTY)
            return True

        if cfg.T_STEEL in kinds:
            if power >= 3:
                for cx, cy in cells:
                    if self.get(cx, cy) == cfg.T_STEEL:
                        self.set(cx, cy, cfg.T_EMPTY)
            return True  # blocked either way

        return False

    def damage_tile(self, tx: int, ty: int, power: int) -> bool:
        """Compatibility wrapper — damages the tank-sized unit containing (tx, ty)."""
        return self.damage_wall_at(
            tx * cfg.TILE + cfg.TILE * 0.5,
            ty * cfg.TILE + cfg.TILE * 0.5,
            power,
        )
    def rect_blocked(self, x: float, y: float, size: float = cfg.TANK_SIZE) -> bool:
        """True if the axis-aligned tank rect overlaps solid tiles."""
        x0 = int(x)
        y0 = int(y)
        x1 = int(x + size - 0.01)
        y1 = int(y + size - 0.01)
        for ty in range(y0 // cfg.TILE, y1 // cfg.TILE + 1):
            for tx in range(x0 // cfg.TILE, x1 // cfg.TILE + 1):
                if self.solid_for_tank(tx, ty):
                    return True
        return False

    def on_ice(self, x: float, y: float, size: float = cfg.TANK_SIZE) -> bool:
        cx = int(x + size / 2) // cfg.TILE
        cy = int(y + size / 2) // cfg.TILE
        return self.get(cx, cy) == cfg.T_ICE

    def update(self, dt: float) -> None:
        """Animate water and manage shovel fortify timer."""
        self.water_phase += dt
        if self.shovel_left > 0:
            self.shovel_left -= dt
            if self.shovel_left <= 0 and self._shovel_was_active:
                self._restore_base_bricks()
                self._shovel_was_active = False

    def fortify_base(self) -> None:
        """Shovel power-up: steel ring around the eagle (tank-sized blocks)."""
        self.shovel_left = cfg.SHOVEL_TIME
        self._shovel_was_active = True
        for tx, ty in self._base_ring():
            if self.get(tx, ty) == cfg.T_BASE:
                continue
            ox, oy = self.unit_origin(tx, ty)
            for dy in range(cfg.BRICK_CELLS):
                for dx in range(cfg.BRICK_CELLS):
                    cx, cy = ox + dx, oy + dy
                    if self.get(cx, cy) != cfg.T_BASE:
                        self.set(cx, cy, cfg.T_STEEL)

    def _restore_base_bricks(self) -> None:
        restored: set[tuple[int, int]] = set()
        for tx, ty in self._base_ring():
            ox, oy = self.unit_origin(tx, ty)
            if (ox, oy) in restored:
                continue
            restored.add((ox, oy))
            for dy in range(cfg.BRICK_CELLS):
                for dx in range(cfg.BRICK_CELLS):
                    cx, cy = ox + dx, oy + dy
                    if self.get(cx, cy) == cfg.T_STEEL:
                        self.set(cx, cy, cfg.T_BRICK)
    def _base_ring(self) -> list[tuple[int, int]]:
        # Eagle sits at tiles (12,24)-(13,25) typically.
        cells: list[tuple[int, int]] = []
        for ty in range(23, 26):
            for tx in range(11, 15):
                if self.get(tx, ty) == cfg.T_BASE:
                    continue
                if ty == 23 or tx in (11, 14):
                    cells.append((tx, ty))
        return cells

    def draw(self, surface: pg.Surface) -> None:
        """Blit terrain; brick/steel use tank-sized unit faces."""
        if int(self.water_phase * 4) % 2 == 0:
            water = self.tiles[cfg.T_WATER]
        else:
            water = self.tiles[cfg.T_WATER].copy()
            water.fill(cfg.WATER_B)
            for i in range(1, cfg.TILE, 2):
                pg.draw.line(water, cfg.WATER_A, (0, i), (cfg.TILE, i))

        unit_px = cfg.BRICK_UNIT * cfg.SCALE
        brick_face = pg.transform.scale(self.tiles["brick_unit"], (unit_px, unit_px))
        steel_face = pg.transform.scale(self.tiles["steel_unit"], (unit_px, unit_px))
        drawn_units: set[tuple[int, int]] = set()

        for ty in range(cfg.MAP_H):
            for tx in range(cfg.MAP_W):
                v = self.grid[ty][tx]
                if v in (cfg.T_BRICK, cfg.T_STEEL):
                    ox, oy = self.unit_origin(tx, ty)
                    if (ox, oy) in drawn_units:
                        continue
                    drawn_units.add((ox, oy))
                    face = brick_face if v == cfg.T_BRICK else steel_face
                    # Prefer steel face if the unit is mixed (rare after snap).
                    for dy in range(cfg.BRICK_CELLS):
                        for dx in range(cfg.BRICK_CELLS):
                            if self.get(ox + dx, oy + dy) == cfg.T_STEEL:
                                face = steel_face
                    surface.blit(
                        face,
                        (ox * cfg.TILE * cfg.SCALE, oy * cfg.TILE * cfg.SCALE),
                    )
                    continue

                if v == cfg.T_GRASS:
                    src = self.tiles[cfg.T_EMPTY]
                elif v == cfg.T_WATER:
                    src = water
                else:
                    src = self.tiles.get(v, self.tiles[cfg.T_EMPTY])
                scaled = pg.transform.scale(src, (cfg.TILE * cfg.SCALE, cfg.TILE * cfg.SCALE))
                surface.blit(scaled, (tx * cfg.TILE * cfg.SCALE, ty * cfg.TILE * cfg.SCALE))

    def draw_grass_overlay(self, surface: pg.Surface) -> None:
        """Draw camouflage grass above tanks."""
        grass = pg.transform.scale(
            self.tiles[cfg.T_GRASS], (cfg.TILE * cfg.SCALE, cfg.TILE * cfg.SCALE)
        )
        for ty in range(cfg.MAP_H):
            for tx in range(cfg.MAP_W):
                if self.grid[ty][tx] == cfg.T_GRASS:
                    surface.blit(grass, (tx * cfg.TILE * cfg.SCALE, ty * cfg.TILE * cfg.SCALE))

    def draw_eagle(self, surface: pg.Surface) -> None:
        """Paint the HQ eagle (or ruined flag) at the base tiles."""
        # Find base top-left
        bx = by = None
        for ty in range(cfg.MAP_H):
            for tx in range(cfg.MAP_W):
                if self.grid[ty][tx] == cfg.T_BASE:
                    bx, by = tx, ty
                    break
            if bx is not None:
                break
        if bx is None:
            # Destroyed — draw rubble at classic HQ spot
            bx, by = 12, 24
            self._draw_ruined(surface, bx, by)
            return
        self._draw_eagle_sprite(surface, bx, by)

    def _draw_eagle_sprite(self, surface: pg.Surface, tx: int, ty: int) -> None:
        px, py = tx * cfg.TILE * cfg.SCALE, ty * cfg.TILE * cfg.SCALE
        s = cfg.SCALE
        # 16×16 logical eagle in a 2×2 tile pocket
        body = [
            (4, 10), (8, 2), (12, 10), (10, 14), (6, 14),
        ]
        pts = [(px + x * s, py + y * s) for x, y in body]
        pg.draw.polygon(surface, cfg.EAGLE, pts)
        pg.draw.polygon(surface, cfg.EAGLE_DK, pts, 1)
        pg.draw.rect(surface, cfg.UI_WHITE, pg.Rect(px + 7 * s, py + 6 * s, 2 * s, 2 * s))

    def _draw_ruined(self, surface: pg.Surface, tx: int, ty: int) -> None:
        px, py = tx * cfg.TILE * cfg.SCALE, ty * cfg.TILE * cfg.SCALE
        s = cfg.SCALE
        pg.draw.line(surface, cfg.UI_ORANGE, (px + 2 * s, py + 2 * s), (px + 14 * s, py + 14 * s), 2)
        pg.draw.line(surface, cfg.UI_ORANGE, (px + 14 * s, py + 2 * s), (px + 2 * s, py + 14 * s), 2)
