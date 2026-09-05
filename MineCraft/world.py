"""Voxel world: place/break, demo island, creative flat, JSON save/load."""

from __future__ import annotations

import json
import math
from pathlib import Path
from ursina import Button, Entity, color, destroy, mouse, scene

from blocks import BEDROCK, HOTBAR_BLOCKS, BlockType, get_block, texture_path

WORLDS_DIR = Path(__file__).resolve().parent / "worlds"
DEMO_PATH = WORLDS_DIR / "demo_island.json"
KID_PATH = WORLDS_DIR / "my_world.json"

# Bounded play area for v1 performance
WORLD_HALF = 10  # -10..9 → 20×20 (keeps FPS friendly)
REACH = 6


class Voxel(Button):
    """A single cube block in the world."""

    def __init__(self, position: tuple[int, int, int], block: BlockType):
        tex = texture_path(block.texture)
        super().__init__(
            parent=scene,
            position=position,
            model="cube",
            origin_y=0.5,
            texture=tex,
            color=color.white,
            highlight_color=color.rgba(255, 255, 200, 180),
            scale=1,
            collider="box",
        )
        self.block_id = block.id
        self.breakable = block.breakable
        # Grass / wood: tint slightly; top texture applied as extra entity if needed
        if block.texture_top:
            self.top_face = Entity(
                parent=self,
                model="quad",
                texture=texture_path(block.texture_top),
                position=(0, 0.501, 0),
                rotation_x=90,
                scale=0.999,
                double_sided=True,
            )
        else:
            self.top_face = None


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
        for (x, y, z), v in self.voxels.items():
            if x == xi and z == zi and y >= best:
                best = y
        return float(best + 2)

    def to_list(self) -> list[dict]:
        return [
            {"x": p[0], "y": p[1], "z": p[2], "type": v.block_id}
            for p, v in self.voxels.items()
        ]

    def load_list(self, blocks: list[dict]) -> None:
        self.clear()
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
        self.load_list(data.get("blocks", []))
        return True

    def build_bedrock_and_flat(self, y_surface: int = 0) -> None:
        """Kid-safe floor: bedrock under, grass/dirt flat creative pad."""
        for z in range(-WORLD_HALF, WORLD_HALF):
            for x in range(-WORLD_HALF, WORLD_HALF):
                self.set_block((x, -2, z), BEDROCK.id)
                self.set_block((x, -1, z), 2)  # dirt
                self.set_block((x, y_surface, z), 1)  # grass

    def build_demo_island(self) -> None:
        """Parent showcase: small island, path, and a simple house."""
        self.clear()
        # Bedrock only under playable island (not the whole map)
        for z in range(-WORLD_HALF, WORLD_HALF):
            for x in range(-WORLD_HALF, WORLD_HALF):
                dist = math.sqrt(x * x + z * z)
                if dist <= 12:
                    self.set_block((x, -3, z), BEDROCK.id)

        # Island disk with gentle height
        for z in range(-WORLD_HALF, WORLD_HALF):
            for x in range(-WORLD_HALF, WORLD_HALF):
                dist = math.sqrt(x * x + z * z)
                if dist > 10.5:
                    continue
                h = 0
                if dist < 8:
                    h = 1
                if dist < 4.5:
                    h = 2
                for y in range(-2, h):
                    bid = 3 if y < 0 else 2
                    self.set_block((x, y, z), bid)
                self.set_block((x, h, z), 1)
                if 8.8 < dist <= 10.5:
                    self.set_block((x, 0, z), 6)

        # Water ring (decorative)
        for z in range(-WORLD_HALF, WORLD_HALF):
            for x in range(-WORLD_HALF, WORLD_HALF):
                dist = math.sqrt(x * x + z * z)
                if 10.5 < dist < 12:
                    if (x, -3, z) not in self.voxels:
                        self.set_block((x, -3, z), BEDROCK.id)
                    self.set_block((x, -1, z), 7)
                    self.set_block((x, 0, z), 7)

        # Path of planks toward house
        for z in range(0, 5):
            self.set_block((0, 2, z), 8)

        # Simple house at (0, 2, 6)
        hx, hy, hz = 0, 2, 6
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                self.set_block((hx + dx, hy, hz + dz), 8)
        for y in range(1, 4):
            for dx in range(-2, 3):
                for dz in range(-2, 3):
                    edge = abs(dx) == 2 or abs(dz) == 2
                    if edge:
                        if y < 3 and dx == 0 and dz == -2:
                            continue
                        self.set_block((hx + dx, hy + y, hz + dz), 4)
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                self.set_block((hx + dx, hy + 4, hz + dz), 8)
        # little tree
        self.set_block((5, 2, 3), 4)
        self.set_block((5, 3, 3), 4)
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                self.set_block((5 + dx, 4, 3 + dz), 5)
        self.set_block((5, 5, 3), 5)

        self.save(DEMO_PATH)

    def try_break(self) -> None:
        hit = mouse.hovered_entity
        if not isinstance(hit, Voxel):
            return
        pos = (int(hit.x), int(hit.y), int(hit.z))
        # Ursina origin_y=0.5 means entity.y is bottom-ish; position tuple matches init
        key = self._key_for_entity(hit)
        if key:
            self.remove_block(key)

    def try_place(self) -> None:
        hit = mouse.hovered_entity
        if not isinstance(hit, Voxel):
            return
        key = self._key_for_entity(hit)
        if not key:
            return
        # Place adjacent to hovered face
        normal = mouse.normal
        if normal is None:
            return
        nx = key[0] + int(round(normal.x))
        ny = key[1] + int(round(normal.y))
        nz = key[2] + int(round(normal.z))
        if not self.in_bounds(nx, nz):
            return
        if ny < -3 or ny > 20:
            return
        if (nx, ny, nz) in self.voxels:
            return
        self.set_block((nx, ny, nz), self.selected_id)

    def _key_for_entity(self, ent: Voxel) -> tuple[int, int, int] | None:
        for k, v in self.voxels.items():
            if v is ent:
                return k
        # Fallback from position
        return (int(round(ent.x)), int(round(ent.y)), int(round(ent.z)))
