"""Voxel world: place/break, demo island, creative flat, JSON save/load.

Performance: keep entity count low. Ursina freezes if thousands of
Button+collider cubes spawn in one frame.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from ursina import Entity, Vec3, camera, color, destroy, mouse, raycast, scene

from blocks import BEDROCK, HOTBAR_BLOCKS, BlockType, get_block, texture_path

WORLDS_DIR = Path(__file__).resolve().parent / "worlds"
DEMO_PATH = WORLDS_DIR / "demo_island.json"
KID_PATH = WORLDS_DIR / "my_world.json"

# Small map — ~12×12. Larger than this freezes many laptops with per-cube Entities.
WORLD_HALF = 6
REACH = 5
MAX_LOAD_BLOCKS = 500


class Voxel(Entity):
    """A single cube block (Entity, not Button — much cheaper)."""

    def __init__(self, position: tuple[int, int, int], block: BlockType):
        super().__init__(
            parent=scene,
            position=position,
            model="cube",
            origin_y=0.5,
            texture=texture_path(block.texture),
            color=color.white,
            scale=1,
            collider="box",
        )
        self.block_id = block.id
        self.breakable = block.breakable


class WorldStore:
    """Owns voxels and world file I/O."""

    def __init__(self) -> None:
        self.voxels: dict[tuple[int, int, int], Voxel] = {}
        self.selected_id: int = HOTBAR_BLOCKS[0].id
        WORLDS_DIR.mkdir(parents=True, exist_ok=True)

    def clear(self) -> None:
        for v in list(self.voxels.values()):
            destroy(v)
        self.voxels.clear()

    def set_block(self, pos: tuple[int, int, int], block_id: int) -> None:
        if pos in self.voxels:
            destroy(self.voxels[pos])
            del self.voxels[pos]
        block = get_block(block_id)
        self.voxels[pos] = Voxel(pos, block)

    def remove_block(self, pos: tuple[int, int, int]) -> bool:
        v = self.voxels.get(pos)
        if not v or not v.breakable:
            return False
        destroy(v)
        del self.voxels[pos]
        return True

    def in_bounds(self, x: int, z: int) -> bool:
        return -WORLD_HALF <= x < WORLD_HALF and -WORLD_HALF <= z < WORLD_HALF

    def height_at(self, x: float, z: float) -> float:
        """Surface Y for spawn (highest solid at xz)."""
        xi, zi = int(round(x)), int(round(z))
        best = 0
        for (bx, by, bz) in self.voxels:
            if bx == xi and bz == zi and by >= best:
                best = by
        return float(best + 2)

    def to_list(self) -> list[dict]:
        return [
            {"x": p[0], "y": p[1], "z": p[2], "type": v.block_id}
            for p, v in self.voxels.items()
        ]

    def load_list(self, blocks: list[dict]) -> None:
        self.clear()
        # Cap oversized saves from older builds that froze machines
        if len(blocks) > MAX_LOAD_BLOCKS:
            blocks = blocks[:MAX_LOAD_BLOCKS]
        for b in blocks:
            self.set_block((int(b["x"]), int(b["y"]), int(b["z"])), int(b["type"]))

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {"version": 1, "blocks": self.to_list()}
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def load(self, path: Path) -> bool:
        if not path.exists():
            return False
        data = json.loads(path.read_text(encoding="utf-8"))
        blocks = data.get("blocks", [])
        # Reject huge legacy worlds — rebuild instead of freezing
        if len(blocks) > MAX_LOAD_BLOCKS:
            return False
        self.load_list(blocks)
        return True

    def build_bedrock_and_flat(self, y_surface: int = 0) -> None:
        """Kid-safe floor: one bedrock + one grass (≈288 cubes max)."""
        self.clear()
        for z in range(-WORLD_HALF, WORLD_HALF):
            for x in range(-WORLD_HALF, WORLD_HALF):
                self.set_block((x, -1, z), BEDROCK.id)
                self.set_block((x, y_surface, z), 1)  # grass

    def build_demo_island(self) -> None:
        """Small island + house (~200–300 cubes). Always regenerates (safe size)."""
        self.clear()

        # Disk terrain: surface only + thin under-layer
        for z in range(-WORLD_HALF, WORLD_HALF):
            for x in range(-WORLD_HALF, WORLD_HALF):
                dist = math.sqrt(x * x + z * z)
                if dist > 5.5:
                    continue
                h = 0
                if dist < 3.5:
                    h = 1
                self.set_block((x, -1, z), BEDROCK.id)
                if dist > 4.2:
                    self.set_block((x, 0, z), 6)  # sand shore
                else:
                    if h > 0:
                        self.set_block((x, 0, z), 2)  # dirt under hill
                    self.set_block((x, h, z), 1)  # grass

        # Tiny water puddles at edge (few blocks)
        for x, z in ((5, 0), (5, 1), (-5, 0), (0, 5), (0, -5)):
            if self.in_bounds(x, z) and (x, 0, z) not in self.voxels:
                self.set_block((x, -1, z), BEDROCK.id)
                self.set_block((x, 0, z), 7)

        # Path
        for z in range(0, 3):
            self.set_block((0, 1, z), 8)

        # Compact 3×3 house
        hx, hy, hz = 0, 1, 4
        for dx in range(-1, 2):
            for dz in range(-1, 2):
                self.set_block((hx + dx, hy, hz + dz), 8)
        for y in (1, 2):
            for dx in range(-1, 2):
                for dz in range(-1, 2):
                    if abs(dx) == 1 or abs(dz) == 1:
                        if y == 1 and dx == 0 and dz == -1:
                            continue  # door
                        self.set_block((hx + dx, hy + y, hz + dz), 4)
        for dx in range(-1, 2):
            for dz in range(-1, 2):
                self.set_block((hx + dx, hy + 3, hz + dz), 8)

        # Tree
        self.set_block((3, 1, 2), 4)
        self.set_block((3, 2, 2), 4)
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                self.set_block((3 + dx, 3, 2 + dz), 5)
        self.set_block((3, 4, 2), 5)

        self.save(DEMO_PATH)

    def _ray_hit_voxel(self) -> tuple[Voxel | None, Vec3 | None]:
        """Ray from camera; return hit Voxel and face normal."""
        hit = raycast(camera.world_position, camera.forward, distance=REACH, ignore=[camera])
        if not hit.hit:
            return None, None
        ent = hit.entity
        if not isinstance(ent, Voxel):
            # Walk up parent chain in case of nested visuals
            parent = getattr(ent, "parent", None)
            if isinstance(parent, Voxel):
                ent = parent
            else:
                return None, None
        return ent, hit.normal

    def try_break(self) -> None:
        ent, _ = self._ray_hit_voxel()
        if ent is None:
            return
        key = self._key_for_entity(ent)
        if key:
            self.remove_block(key)

    def try_place(self) -> None:
        ent, normal = self._ray_hit_voxel()
        if ent is None or normal is None:
            return
        key = self._key_for_entity(ent)
        if not key:
            return
        nx = key[0] + int(round(normal.x))
        ny = key[1] + int(round(normal.y))
        nz = key[2] + int(round(normal.z))
        if not self.in_bounds(nx, nz):
            return
        if ny < -2 or ny > 12:
            return
        if (nx, ny, nz) in self.voxels:
            return
        self.set_block((nx, ny, nz), self.selected_id)

    def _key_for_entity(self, ent: Voxel) -> tuple[int, int, int] | None:
        for k, v in self.voxels.items():
            if v is ent:
                return k
        return (int(round(ent.x)), int(round(ent.y)), int(round(ent.z)))
