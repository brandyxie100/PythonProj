"""Hotbar and on-screen help for the kid sandbox."""

from __future__ import annotations

from ursina import Text, Entity, Quad, camera, color

from blocks import HOTBAR_BLOCKS, get_block, texture_path


class HotbarUI:
    """Bottom slot strip; keys 1–8 select blocks."""

    def __init__(self) -> None:
        self.slots: list[Entity] = []
        self.labels: list[Text] = []
        self.highlight = Entity(
            parent=camera.ui,
            model=Quad(aspect=1),
            scale=(0.07, 0.07),
            color=color.rgba(255, 255, 100, 90),
            y=-0.42,
            z=-0.01,
        )
        self.help_text = Text(
            text="1-8 block | LMB break | RMB place | F5 save | F9 load | M menu | ESC free mouse",
            origin=(0, 0),
            position=(0, 0.45),
            scale=1.0,
            background=True,
        )
        self.mode_text = Text(
            text="World: Demo",
            origin=(-0.5, 0),
            position=(-0.85, 0.45),
            scale=1.2,
            background=True,
        )
        n = len(HOTBAR_BLOCKS)
        start_x = -0.28
        gap = 0.08
        for i, block in enumerate(HOTBAR_BLOCKS):
            x = start_x + i * gap
            slot = Entity(
                parent=camera.ui,
                model="quad",
                texture=texture_path(block.texture_top or block.texture),
                scale=(0.06, 0.06),
                position=(x, -0.42),
            )
            label = Text(
                text=str(i + 1),
                parent=camera.ui,
                position=(x - 0.02, -0.37),
                scale=0.8,
                origin=(0, 0),
            )
            self.slots.append(slot)
            self.labels.append(label)
        self.set_selected(0)

    def set_selected(self, index: int) -> None:
        index = max(0, min(len(HOTBAR_BLOCKS) - 1, index))
        self.selected_index = index
        x = -0.28 + index * 0.08
        self.highlight.x = x

    def set_mode_label(self, name: str) -> None:
        self.mode_text.text = f"World: {name}"

    def selected_block_id(self) -> int:
        return HOTBAR_BLOCKS[self.selected_index].id
