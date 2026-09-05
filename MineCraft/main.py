"""
Kid Minecraft Sandbox — creative voxel play (original textures, not Mojang assets).

Run:
  cd MineCraft
  python main.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure local imports work when launched from any cwd
sys.path.insert(0, str(Path(__file__).resolve().parent))

from textures import ensure_textures

ensure_textures()

from ursina import (
    Sky,
    Text,
    Ursina,
    Vec3,
    application,
    color,
    mouse,
)
from ursina.prefabs.first_person_controller import FirstPersonController

# Textures live under MineCraft/textures/ — must set before spawning voxels
application.asset_folder = Path(__file__).resolve().parent

from blocks import HOTBAR_BLOCKS
from player_ui import HotbarUI
from world import DEMO_PATH, KID_PATH, WorldStore

app = Ursina(
    title="Kid Minecraft Sandbox",
    borderless=False,
    fullscreen=False,
    development_mode=False,
)

world = WorldStore()
hotbar = HotbarUI()
player: FirstPersonController | None = None
menu_visible = True
current_world_name = "Menu"

menu_panel = Text(
    text=(
        "KID MINECRAFT SANDBOX\n\n"
        "[1] Play Demo Island (parent showcase)\n"
        "[2] New Creative World (kid builds)\n"
        "[3] Load My World\n\n"
        "Click window, then press a number.\n"
        "WASD move · mouse look · Esc unlock mouse"
    ),
    origin=(0, 0),
    position=(0, 0.05),
    scale=1.4,
    background=True,
)


def spawn_player(at: Vec3) -> None:
    global player
    if player is not None:
        player.position = at
        return
    player = FirstPersonController(
        position=at,
        speed=6,
        jump_height=1.6,
        mouse_sensitivity=Vec3(40, 40, 0),
    )
    player.cursor.visible = True


def hide_menu() -> None:
    global menu_visible
    menu_visible = False
    menu_panel.enabled = False
    mouse.locked = True


def show_menu() -> None:
    global menu_visible
    menu_visible = True
    menu_panel.enabled = True
    mouse.locked = False
    hotbar.set_mode_label("Menu")


def start_demo() -> None:
    global current_world_name
    # Always rebuild from code (avoids loading oversized legacy JSON that freezes)
    world.build_demo_island()
    current_world_name = "Demo Island"
    hotbar.set_mode_label(current_world_name)
    hide_menu()
    spawn_player(Vec3(0, world.height_at(0, 0), -2))


def start_creative() -> None:
    global current_world_name
    world.build_bedrock_and_flat(0)
    current_world_name = "Creative"
    hotbar.set_mode_label(current_world_name)
    hide_menu()
    spawn_player(Vec3(0, 3, 0))


def load_kid_world() -> None:
    global current_world_name
    if not world.load(KID_PATH):
        hotbar.mode_text.text = "Saved world too big or missing — Creative"
        start_creative()
        return
    current_world_name = "My World"
    hotbar.set_mode_label(current_world_name)
    hide_menu()
    spawn_player(Vec3(0, world.height_at(0, 0), 0))


def save_kid_world() -> None:
    if menu_visible or not world.voxels:
        return
    world.save(KID_PATH)
    hotbar.mode_text.text = f"Saved → worlds/my_world.json"


Sky(color=color.rgb(135, 206, 235))

# Soft lighting only (DirectionalLight + many cubes can stutter)
from ursina import AmbientLight

AmbientLight(color=color.rgba(220, 220, 220, 0.85))


def input(key: str) -> None:  # noqa: A001 — Ursina callback name
    if menu_visible:
        if key == "1":
            start_demo()
        elif key == "2":
            start_creative()
        elif key == "3":
            load_kid_world()
        return

    if key == "m":
        show_menu()
        return

    if key == "f5":
        save_kid_world()
        return

    if key == "f9":
        load_kid_world()
        return

    # Hotbar 1–8
    if key in "12345678":
        idx = int(key) - 1
        if idx < len(HOTBAR_BLOCKS):
            hotbar.set_selected(idx)
            world.selected_id = hotbar.selected_block_id()
        return

    if key == "left mouse down":
        world.try_break()
    elif key == "right mouse down":
        world.selected_id = hotbar.selected_block_id()
        world.try_place()


def update() -> None:
    if player is None or menu_visible:
        return
    # Soft kill: if fallen below world, respawn
    if player.y < -10:
        player.position = Vec3(0, world.height_at(0, 0), 0)


# Boot into menu (no world until choice)
mouse.locked = False
world.selected_id = hotbar.selected_block_id()

if __name__ == "__main__":
    app.run()
