"""
Plants vs Zombies - Core Tools and State Machine
================================================
Provides:
- State/Control base classes for the game state machine
- Image loading utilities (sprites, frames)
- JSON data loaders for plant and zombie entity configs

Asset paths are resolved relative to the project root so the game
works regardless of the current working directory.
"""

from __future__ import annotations

import json
import os
from abc import abstractmethod
from typing import Any

import pygame as pg

from . import constants as c

# ---------------------------------------------------------------------------
# Path resolution (works regardless of cwd when run from PythonProj or project root)
# ---------------------------------------------------------------------------
_SOURCE_DIR: str = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT: str = os.path.dirname(_SOURCE_DIR)
_RESOURCES_GRAPHICS: str = os.path.join(_PROJECT_ROOT, "resources", "graphics")


def _res_data(*parts: str) -> str:
    """Resolve path to a file under source/data/."""
    return os.path.join(_SOURCE_DIR, "data", *parts)


def res_data_path(*parts: str) -> str:
    """Resolve path to a file under source/data/. Use for map and entity JSON."""
    return _res_data(*parts)


# ---------------------------------------------------------------------------
# State machine base classes
# ---------------------------------------------------------------------------
class State:
    """Base class for game states (menu, level, victory, lose).

    Attributes:
        start_time: When this state was entered.
        current_time: Current game time (ms).
        done: True when state should transition.
        next: Name of next state to transition to.
        persist: Data to pass to next state.
    """

    def __init__(self) -> None:
        """Initialize state with default values."""
        self.start_time: float = 0.0
        self.current_time: float = 0.0
        self.done: bool = False
        self.next: str | None = None
        self.persist: dict[str, Any] = {}

    @abstractmethod
    def startup(self, current_time: float, persist: dict[str, Any]) -> None:
        """Called when entering this state.

        Args:
            current_time: Current game time in ms.
            persist: Data from previous state.
        """
        pass

    def cleanup(self) -> dict[str, Any]:
        """Called when leaving this state. Reset done and return persist data."""
        self.done = False
        return self.persist

    @abstractmethod
    def update(
        self,
        surface: pg.Surface,
        current_time: float,
        mouse_pos: tuple[int, int] | None,
        mouse_click: list[bool],
    ) -> None:
        """Update and draw this state.

        Args:
            surface: Screen to draw on.
            current_time: Current game time in ms.
            mouse_pos: Mouse position or None.
            mouse_click: [left_click, right_click].
        """
        pass


class Control:
    """Main game controller: event loop, state transitions, and timing.

    Attributes:
        screen: Pygame display surface.
        done: True when game should exit.
        clock: FPS limiter.
        fps: Target frames per second.
        state_dict: Map of state name -> State instance.
        state_name: Current state name.
        state: Current State instance.
    """

    def __init__(self) -> None:
        """Initialize controller with default state."""
        self.screen: pg.Surface = pg.display.get_surface()
        self.done: bool = False
        self.clock: pg.time.Clock = pg.time.Clock()
        self.fps: int = 60
        self.keys: tuple = pg.key.get_pressed()
        self.mouse_pos: tuple[int, int] | None = None
        # [left click, right click]
        self.mouse_click: list[bool] = [False, False]
        self.current_time: float = 0.0
        self.state_dict: dict[str, State] = {}
        self.state_name: str | None = None
        self.state: State | None = None
        self.game_info: dict[str, Any] = {
            c.CURRENT_TIME: 0.0,
            c.LEVEL_NUM: c.START_LEVEL_NUM,
        }

    def setup_states(
        self,
        state_dict: dict[str, State],
        start_state: str,
    ) -> None:
        """Register states and set the initial state.

        Args:
            state_dict: Map of state name -> State instance.
            start_state: Name of initial state.
        """
        self.state_dict = state_dict
        self.state_name = start_state
        self.state = self.state_dict[self.state_name]
        self.state.startup(self.current_time, self.game_info)

    def update(self) -> None:
        """Update current state; flip to next if done."""
        self.current_time = pg.time.get_ticks()
        if self.state is not None and self.state.done:
            self.flip_state()
        if self.state is not None:
            self.state.update(
                self.screen,
                self.current_time,
                self.mouse_pos,
                self.mouse_click,
            )
        self.mouse_pos = None
        self.mouse_click[0] = False
        self.mouse_click[1] = False

    def flip_state(self) -> None:
        """Transition to next state; pass persist data."""
        if self.state is None or self.state_name is None:
            return
        next_name = self.state.next or self.state_name
        if next_name not in self.state_dict:
            raise RuntimeError(
                f"Unknown next state '{next_name}' from '{self.state_name}'. "
                f"Known states: {sorted(self.state_dict)}"
            )
        self.state_name = next_name
        persist = self.state.cleanup()
        self.state = self.state_dict[self.state_name]
        self.state.startup(self.current_time, persist)

    def event_loop(self) -> None:
        """Process pygame events: quit, keys, mouse."""
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.done = True
            elif event.type == pg.KEYDOWN:
                self.keys = pg.key.get_pressed()
            elif event.type == pg.KEYUP:
                self.keys = pg.key.get_pressed()
            elif event.type == pg.MOUSEBUTTONDOWN:
                self.mouse_pos = pg.mouse.get_pos()
                pressed = pg.mouse.get_pressed()
                self.mouse_click[0] = bool(pressed[0])
                self.mouse_click[1] = bool(pressed[2])

    def main(self) -> None:
        """Main game loop: events, update, render, tick."""
        while not self.done:
            self.event_loop()
            self.update()
            pg.display.update()
            self.clock.tick(self.fps)
        print("game over")


# ---------------------------------------------------------------------------
# Image utilities
# ---------------------------------------------------------------------------
def get_image(
    sheet: pg.Surface,
    x: int,
    y: int,
    width: int,
    height: int,
    colorkey: tuple[int, int, int] | None = c.BLACK,
    scale: float = 1.0,
) -> pg.Surface:
    """Extract a sub-rect from a sprite sheet and optionally scale it.

    Prefers per-pixel alpha when the source already has an alpha channel
    (PNG frames). Falls back to colorkey transparency for opaque sheets.

    Some plant sheets (PotatoMine, Squash, etc.) are RGBA but still use an
    *opaque* white matte. For those, pass ``colorkey=WHITE`` so white pixels
    are punched out even on SRCALPHA surfaces. Black colorkey is never
    applied to alpha sources (would erase outlines/eyes).

    Args:
        sheet: Source sprite sheet surface.
        x: Left of source rect.
        y: Top of source rect.
        width: Width of source rect.
        height: Height of source rect.
        colorkey: Color to treat as transparent.
        scale: Scale factor (1.0 = no scaling).

    Returns:
        New surface with the extracted and scaled image.
    """
    width = max(1, int(width))
    height = max(1, int(height))
    # convert_alpha() frames are SRCALPHA; keep that path so black art
    # pixels (eyes, outlines) are not punched out by a BLACK colorkey.
    use_alpha = bool(sheet.get_flags() & pg.SRCALPHA)

    if use_alpha:
        image = pg.Surface((width, height), pg.SRCALPHA)
        image.blit(sheet, (0, 0), (x, y, width, height))
        # Opaque white mattes in RGBA assets (PotatoMine, etc.)
        if colorkey == c.WHITE:
            image = _punch_colorkey_alpha(image, colorkey)
    else:
        image = pg.Surface((width, height)).convert()
        if colorkey is not None:
            image.fill(colorkey)
        image.blit(sheet, (0, 0), (x, y, width, height))
        if colorkey is not None:
            image.set_colorkey(colorkey)

    if scale != 1.0:
        new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
        image = pg.transform.scale(image, new_size)
        if use_alpha and colorkey == c.WHITE:
            image = _punch_colorkey_alpha(image, colorkey)
        elif not use_alpha and colorkey is not None:
            image.set_colorkey(colorkey)

    return image


def _punch_colorkey_alpha(
    image: pg.Surface, colorkey: tuple[int, int, int]
) -> pg.Surface:
    """Set alpha=0 on near-colorkey RGB pixels (keeps SRCALPHA)."""
    # Tolerance covers near-white PNG matte noise without eating plant colors.
    threshold = 12
    key_r, key_g, key_b = colorkey
    rgb = pg.surfarray.pixels3d(image)
    alpha = pg.surfarray.pixels_alpha(image)
    mask = (
        (abs(rgb[:, :, 0].astype(int) - key_r) <= threshold)
        & (abs(rgb[:, :, 1].astype(int) - key_g) <= threshold)
        & (abs(rgb[:, :, 2].astype(int) - key_b) <= threshold)
    )
    alpha[mask] = 0
    del rgb
    del alpha
    return image


def load_image_frames(
    directory: str,
    image_name: str,
    colorkey: tuple[int, int, int],
    accept: tuple[str, ...],
) -> list[pg.Surface]:
    """Load animation frames from a directory (e.g. Peashooter_0.png, Peashooter_1.png).

    Args:
        directory: Path to folder containing frame images.
        image_name: Base name (e.g. "Peashooter"); frames are "{image_name}_0", etc.
        colorkey: Color to treat as transparent.
        accept: Tuple of accepted extensions (e.g. ('.png', '.jpg')).

    Returns:
        List of surfaces in frame order.
    """
    frame_list: list[pg.Surface] = []
    tmp: dict[int, pg.Surface] = {}
    prefix = image_name + "_"
    for pic in os.listdir(directory):
        if pic.startswith("."):
            continue
        name, ext = os.path.splitext(pic)
        if ext.lower() not in accept or not name.startswith(prefix):
            continue
        try:
            index = int(name[len(prefix) :])
        except ValueError:
            continue
        img = pg.image.load(os.path.join(directory, pic))
        if img.get_alpha():
            img = img.convert_alpha()
        else:
            img = img.convert()
            img.set_colorkey(colorkey)
        tmp[index] = img

    for i in sorted(tmp):
        frame_list.append(tmp[i])
    return frame_list


def load_all_gfx(
    directory: str,
    colorkey: tuple[int, int, int] = c.WHITE,
    accept: tuple[str, ...] = (".png", ".jpg", ".bmp", ".gif"),
) -> dict[str, pg.Surface | list[pg.Surface]]:
    """Recursively load all graphics from resources/graphics into a dict.

    Handles nested structure: graphics/Bullets, graphics/Plants, graphics/Zombies, etc.
    Each key is the image/folder name; value is a Surface or list of frames.

    Args:
        directory: Path to resources/graphics.
        colorkey: Default transparent color.
        accept: Accepted image extensions.

    Returns:
        Dict mapping names to loaded surfaces or frame lists.
    """
    graphics: dict[str, pg.Surface | list[pg.Surface]] = {}
    for name1 in os.listdir(directory):
        if name1.startswith("."):
            continue
        dir1 = os.path.join(directory, name1)
        if os.path.isdir(dir1):
            for name2 in os.listdir(dir1):
                if name2.startswith("."):
                    continue
                dir2 = os.path.join(dir1, name2)
                if os.path.isdir(dir2):
                    # e.g. Zombies/ConeheadZombie/
                    loaded_flat = False
                    for name3 in os.listdir(dir2):
                        if name3.startswith("."):
                            continue
                        dir3 = os.path.join(dir2, name3)
                        if os.path.isdir(dir3):
                            # e.g. ConeheadZombieAttack/
                            image_name, _ = os.path.splitext(name3)
                            graphics[image_name] = load_image_frames(
                                dir3, image_name, colorkey, accept
                            )
                        elif not loaded_flat:
                            # Pics directly under e.g. Plants/Peashooter/
                            _, ext = os.path.splitext(name3)
                            if ext.lower() not in accept:
                                continue
                            image_name, _ = os.path.splitext(name2)
                            graphics[image_name] = load_image_frames(
                                dir2, image_name, colorkey, accept
                            )
                            loaded_flat = True
                else:
                    # Single image under e.g. Screen/
                    name, ext = os.path.splitext(name2)
                    if ext.lower() in accept:
                        img = pg.image.load(dir2)
                        if img.get_alpha():
                            img = img.convert_alpha()
                        else:
                            img = img.convert()
                            img.set_colorkey(colorkey)
                        graphics[name] = img
    return graphics


def load_zombie_image_rect() -> dict:
    """Load zombie sprite rect definitions from zombie.json."""
    return _load_entity_rect("zombie.json", c.ZOMBIE_IMAGE_RECT)


def load_plant_image_rect() -> dict:
    """Load plant sprite rect definitions from plant.json."""
    return _load_entity_rect("plant.json", c.PLANT_IMAGE_RECT)


def _load_entity_rect(filename: str, key: str) -> dict:
    """Load an entity JSON file and return the named rect dictionary."""
    file_path = _res_data("entity", filename)
    try:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError as exc:
        raise RuntimeError(f"Missing entity data file: {file_path}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON in entity data file: {file_path}") from exc
    if key not in data:
        raise RuntimeError(f"Key '{key}' not found in {file_path}")
    return data[key]


# ---------------------------------------------------------------------------
# Pygame init and global resources (loaded at import)
# ---------------------------------------------------------------------------
def bootstrap_display() -> tuple[
    pg.Surface,
    dict[str, pg.Surface | list[pg.Surface]],
    dict,
    dict,
]:
    """Initialize pygame display and load graphics/entity data.

    Safe to call once; subsequent callers should use the module globals.
    Set PVZ_SKIP_DISPLAY=1 to skip window creation (for non-game tooling).
    """
    if os.environ.get("PVZ_SKIP_DISPLAY") == "1":
        raise RuntimeError("Display bootstrap skipped (PVZ_SKIP_DISPLAY=1)")

    if not pg.get_init():
        pg.init()
    pg.display.set_caption(c.ORIGINAL_CAPTION)
    screen = pg.display.set_mode(c.SCREEN_SIZE)
    gfx = load_all_gfx(_RESOURCES_GRAPHICS)
    zombie_rect = load_zombie_image_rect()
    plant_rect = load_plant_image_rect()
    return screen, gfx, zombie_rect, plant_rect


SCREEN: pg.Surface
GFX: dict[str, pg.Surface | list[pg.Surface]]
ZOMBIE_RECT: dict
PLANT_RECT: dict

SCREEN, GFX, ZOMBIE_RECT, PLANT_RECT = bootstrap_display()
