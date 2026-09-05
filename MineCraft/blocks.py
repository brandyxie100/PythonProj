"""Block registry: IDs, names, textures, and breakable flags."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

TEXTURE_DIR = Path(__file__).resolve().parent / "textures"


@dataclass(frozen=True)
class BlockType:
    """One placeable / breakable block kind."""

    id: int
    name: str
    texture: str
    breakable: bool = True
    # Optional separate top face (classic grass look)
    texture_top: str | None = None


# Hotbar order: keys 1–8 map to these (bedrock is not on hotbar)
HOTBAR_BLOCKS: list[BlockType] = [
    BlockType(1, "Grass", "grass.png", texture_top="grass_top.png"),
    BlockType(2, "Dirt", "dirt.png"),
    BlockType(3, "Stone", "stone.png"),
    BlockType(4, "Wood", "wood.png", texture_top="wood_top.png"),
    BlockType(5, "Leaves", "leaves.png"),
    BlockType(6, "Sand", "sand.png"),
    BlockType(7, "Water", "water.png"),
    BlockType(8, "Planks", "planks.png"),
]

BEDROCK = BlockType(0, "Bedrock", "bedrock.png", breakable=False)

ALL_BLOCKS: dict[int, BlockType] = {BEDROCK.id: BEDROCK}
for _b in HOTBAR_BLOCKS:
    ALL_BLOCKS[_b.id] = _b


def texture_path(filename: str) -> str:
    """Path relative to MineCraft/ for Ursina asset_folder loading."""
    # Ursina resolves textures from application.asset_folder
    return f"textures/{filename}"


def get_block(block_id: int) -> BlockType:
    """Return block type by id, defaulting to dirt if unknown."""
    return ALL_BLOCKS.get(block_id, HOTBAR_BLOCKS[1])
