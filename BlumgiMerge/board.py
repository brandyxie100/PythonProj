"""Merge board grid — buy, drag-merge, and animate placements."""

from __future__ import annotations

from dataclasses import dataclass, field

import pygame

import config as c
from slime import Slime


@dataclass
class Board:
    """COLS x ROWS slime grid with drag-and-drop merging."""

    cells: list[list[Slime | None]] = field(default_factory=list)
    dragging: Slime | None = None
    drag_from: tuple[int, int] | None = None
    drag_pos: tuple[float, float] = (0.0, 0.0)
    last_merge_at: tuple[float, float] | None = None

    def __post_init__(self) -> None:
        if not self.cells:
            self.cells = [[None for _ in range(c.COLS)] for _ in range(c.ROWS)]

    def clear(self) -> None:
        self.cells = [[None for _ in range(c.COLS)] for _ in range(c.ROWS)]
        self.dragging = None
        self.drag_from = None

    def count(self) -> int:
        return sum(1 for row in self.cells for s in row if s is not None)

    def first_empty(self) -> tuple[int, int] | None:
        for r in range(c.ROWS):
            for col in range(c.COLS):
                if self.cells[r][col] is None:
                    return r, col
        return None

    def cell_center(self, row: int, col: int) -> tuple[float, float]:
        x = c.BOARD_X + col * c.CELL + c.CELL / 2
        y = c.BOARD_Y + row * c.CELL + c.CELL / 2
        return x, y

    def hit_cell(self, pos: tuple[int, int]) -> tuple[int, int] | None:
        px, py = pos
        if px < c.BOARD_X or py < c.BOARD_Y:
            return None
        col = (px - c.BOARD_X) // c.CELL
        row = (py - c.BOARD_Y) // c.CELL
        if 0 <= row < c.ROWS and 0 <= col < c.COLS:
            return int(row), int(col)
        return None

    def try_buy(self, tier: int = 1) -> tuple[bool, tuple[float, float] | None]:
        """Place a new slime in the first empty cell."""
        spot = self.first_empty()
        if spot is None:
            return False, None
        r, col = spot
        self.cells[r][col] = Slime(tier)
        return True, self.cell_center(r, col)

    def total_dps(self) -> int:
        return sum(s.dps for row in self.cells for s in row if s is not None)

    def total_hp(self) -> int:
        return sum(s.hp for row in self.cells for s in row if s is not None)

    def army(self) -> list[Slime]:
        return [s for row in self.cells for s in row if s is not None]

    def update(self, dt: float) -> None:
        for row in self.cells:
            for s in row:
                if s is not None:
                    s.update(dt)
        if self.dragging is not None:
            self.dragging.update(dt)

    def start_drag(self, pos: tuple[int, int]) -> bool:
        cell = self.hit_cell(pos)
        if cell is None:
            return False
        r, col = cell
        slime = self.cells[r][col]
        if slime is None:
            return False
        self.dragging = slime
        self.drag_from = (r, col)
        self.cells[r][col] = None
        self.drag_pos = (float(pos[0]), float(pos[1]))
        return True

    def move_drag(self, pos: tuple[int, int]) -> None:
        if self.dragging is None:
            return
        self.drag_pos = (float(pos[0]), float(pos[1]))

    def end_drag(self, pos: tuple[int, int]) -> str:
        """Finish drag. Returns 'merge', 'move', 'cancel', or 'none'."""
        if self.dragging is None or self.drag_from is None:
            return "none"
        src_r, src_c = self.drag_from
        cell = self.hit_cell(pos)
        result = "cancel"
        if cell is None:
            self.cells[src_r][src_c] = self.dragging
            result = "cancel"
        else:
            r, col = cell
            target = self.cells[r][col]
            if target is None:
                self.cells[r][col] = self.dragging
                result = "move"
            elif target.tier == self.dragging.tier and target.tier < c.MAX_TIER:
                # Merge into higher tier
                merged = Slime(target.tier + 1)
                merged.merge_flash = 0.45
                self.cells[r][col] = merged
                self.last_merge_at = self.cell_center(r, col)
                result = "merge"
            elif (r, col) == (src_r, src_c):
                self.cells[r][col] = self.dragging
                result = "cancel"
            else:
                # Swap
                self.cells[src_r][src_c] = target
                self.cells[r][col] = self.dragging
                result = "move"
        self.dragging = None
        self.drag_from = None
        return result

    def draw(self, surf: pygame.Surface) -> None:
        # Grid panel
        board_w = c.COLS * c.CELL
        board_h = c.ROWS * c.CELL
        pygame.draw.rect(
            surf,
            c.PANEL,
            pygame.Rect(c.BOARD_X - 10, c.BOARD_Y - 10, board_w + 20, board_h + 20),
            border_radius=16,
        )
        pygame.draw.rect(
            surf,
            c.PANEL_EDGE,
            pygame.Rect(c.BOARD_X - 10, c.BOARD_Y - 10, board_w + 20, board_h + 20),
            width=3,
            border_radius=16,
        )
        for r in range(c.ROWS):
            for col in range(c.COLS):
                x = c.BOARD_X + col * c.CELL
                y = c.BOARD_Y + r * c.CELL
                pygame.draw.rect(
                    surf,
                    (60, 40, 110),
                    pygame.Rect(x + 4, y + 4, c.CELL - 8, c.CELL - 8),
                    border_radius=12,
                )
                slime = self.cells[r][col]
                if slime is not None:
                    cx, cy = self.cell_center(r, col)
                    slime.draw(surf, cx, cy)
        if self.dragging is not None:
            self.dragging.draw(
                surf, self.drag_pos[0], self.drag_pos[1], scale=1.12
            )
