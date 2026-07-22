"""Detailed multi-part weapon rendering for melee and throw modes.

Each weapon is drawn from real-world structure (haft + head, blade +
guard + grip, etc.) rather than a single thick line.
"""

from __future__ import annotations

import math
from typing import Sequence

import pygame

Point = tuple[float, float]
Color = tuple[int, int, int]

# Material palette shared across weapons.
WOOD = (138, 96, 52)
WOOD_DARK = (96, 64, 34)
WOOD_LIGHT = (176, 128, 72)
STEEL = (210, 218, 230)
STEEL_EDGE = (245, 248, 255)
STEEL_DARK = (120, 130, 145)
BRASS = (196, 156, 70)
LEATHER = (92, 62, 38)
IRON = (88, 94, 104)
ARROW_SHAFT = (188, 150, 92)
ARROW_FEATHER = (210, 70, 55)


def _i(p: Point) -> tuple[int, int]:
    """Round a point to integer pixel coordinates."""
    return int(round(p[0])), int(round(p[1]))


def _along(origin: Point, angle: float, dist: float) -> Point:
    """Point ``dist`` pixels from ``origin`` along ``angle``."""
    return origin[0] + math.cos(angle) * dist, origin[1] + math.sin(angle) * dist


def _perp(angle: float, dist: float) -> Point:
    """Offset vector perpendicular to ``angle``."""
    return math.cos(angle + math.pi / 2) * dist, math.sin(angle + math.pi / 2) * dist


def _offset(p: Point, ox: float, oy: float) -> Point:
    return p[0] + ox, p[1] + oy


def _poly(surf: pygame.Surface, color: Color, points: Sequence[Point]) -> None:
    """Filled polygon helper."""
    if len(points) < 3:
        return
    pygame.draw.polygon(surf, color, [_i(p) for p in points])


def _line(
    surf: pygame.Surface,
    color: Color,
    a: Point,
    b: Point,
    width: int,
) -> None:
    pygame.draw.line(surf, color, _i(a), _i(b), max(1, width))


def draw_weapon(
    surf: pygame.Surface,
    weapon_key: str,
    grip: Point,
    tip: Point,
    *,
    scale: float = 1.0,
) -> None:
    """Draw a multi-part weapon oriented from ``grip`` toward ``tip``.

    Args:
        surf: Target surface.
        weapon_key: Melee or throw-weapon id.
        grip: Hand / rear end of the weapon.
        tip: Front / striking end of the weapon.
        scale: Uniform size multiplier (embedded weapons use < 1).
    """
    dx = tip[0] - grip[0]
    dy = tip[1] - grip[1]
    length = math.hypot(dx, dy)
    if length < 1.0:
        return
    angle = math.atan2(dy, dx)
    drawer = _DRAWERS.get(weapon_key, _draw_generic_shaft)
    drawer(surf, grip, tip, angle, length, scale)


# ── Melee weapons ───────────────────────────────────────────────────


def _draw_sword(
    surf: pygame.Surface,
    grip: Point,
    tip: Point,
    angle: float,
    length: float,
    scale: float,
) -> None:
    """Longsword: grip, pommel, crossguard, tapering blade."""
    s = scale
    guard = _along(grip, angle, length * 0.22)
    blade_base = guard
    # Pommel
    pommel = _along(grip, angle, -4.0 * s)
    pygame.draw.circle(surf, BRASS, _i(pommel), max(2, int(4 * s)))
    # Grip wrap
    _line(surf, LEATHER, grip, guard, max(2, int(5 * s)))
    # Crossguard
    px, py = _perp(angle, 11 * s)
    _line(surf, STEEL_DARK, _offset(guard, -px, -py), _offset(guard, px, py), max(2, int(3 * s)))
    # Blade (tapering polygon)
    half_w = 5.5 * s
    mid = _along(blade_base, angle, length * 0.55)
    px2, py2 = _perp(angle, half_w)
    px3, py3 = _perp(angle, half_w * 0.35)
    _poly(
        surf,
        STEEL,
        [
            _offset(blade_base, -px2, -py2),
            _offset(blade_base, px2, py2),
            _offset(mid, px3, py3),
            tip,
            _offset(mid, -px3, -py3),
        ],
    )
    # Fuller / highlight down the spine
    _line(surf, STEEL_EDGE, blade_base, tip, max(1, int(1 * s)))


def _draw_broadsword(
    surf: pygame.Surface,
    grip: Point,
    tip: Point,
    angle: float,
    length: float,
    scale: float,
) -> None:
    """Broadsword: wider leaf blade, fuller, sturdy crossguard."""
    s = scale
    guard = _along(grip, angle, length * 0.2)
    # Grip + pommel
    pommel = _along(grip, angle, -5.0 * s)
    pygame.draw.circle(surf, BRASS, _i(pommel), max(2, int(5 * s)))
    _line(surf, LEATHER, grip, guard, max(2, int(6 * s)))
    # Wide crossguard with slight curve tips
    px, py = _perp(angle, 14 * s)
    g1 = _offset(guard, -px, -py)
    g2 = _offset(guard, px, py)
    _line(surf, STEEL_DARK, g1, g2, max(2, int(4 * s)))
    pygame.draw.circle(surf, STEEL_DARK, _i(g1), max(2, int(3 * s)))
    pygame.draw.circle(surf, STEEL_DARK, _i(g2), max(2, int(3 * s)))
    # Broad blade
    half = 8.0 * s
    mid = _along(guard, angle, length * 0.5)
    near_tip = _along(guard, angle, length * 0.82)
    pxa, pya = _perp(angle, half)
    pxb, pyb = _perp(angle, half * 0.85)
    pxc, pyc = _perp(angle, half * 0.35)
    _poly(
        surf,
        STEEL,
        [
            _offset(guard, -pxa, -pya),
            _offset(guard, pxa, pya),
            _offset(mid, pxb, pyb),
            _offset(near_tip, pxc, pyc),
            tip,
            _offset(near_tip, -pxc, -pyc),
            _offset(mid, -pxb, -pyb),
        ],
    )
    _line(surf, STEEL_EDGE, guard, tip, max(1, int(2 * s)))


def _draw_axe(
    surf: pygame.Surface,
    grip: Point,
    tip: Point,
    angle: float,
    length: float,
    scale: float,
) -> None:
    """Axe: wooden haft + crescent metal head (two primary components)."""
    s = scale
    # 1) Haft — wooden shaft from grip to near tip.
    head_mount = _along(grip, angle, length * 0.78)
    _line(surf, WOOD_DARK, grip, head_mount, max(3, int(7 * s)))
    _line(surf, WOOD, grip, head_mount, max(2, int(5 * s)))
    # Leather wrap near the grip
    wrap_end = _along(grip, angle, length * 0.22)
    _line(surf, LEATHER, grip, wrap_end, max(2, int(7 * s)))
    # 2) Head — crescent blade on the striking side + poll on the back.
    px, py = _perp(angle, 1.0)
    blade_out = 16.0 * s
    blade_back = 7.0 * s
    # Striking face (crescent / wedge)
    a = _along(head_mount, angle, 2 * s)
    b = _offset(a, px * blade_out, py * blade_out)
    c_pt = _along(b, angle, 10 * s)
    d = _along(a, angle, 14 * s)
    e = _offset(d, px * (blade_out * 0.55), py * (blade_out * 0.55))
    _poly(surf, STEEL_DARK, [a, b, c_pt, e, d])
    _poly(surf, STEEL, [a, b, e, d])
    # Cutting edge highlight
    _line(surf, STEEL_EDGE, b, c_pt, max(1, int(2 * s)))
    # Poll (blunt back of the head)
    poll = _offset(a, -px * blade_back, -py * blade_back)
    poll2 = _offset(d, -px * blade_back * 0.7, -py * blade_back * 0.7)
    _poly(surf, IRON, [a, poll, poll2, d])
    # Eye binding where head meets haft
    pygame.draw.circle(surf, IRON, _i(head_mount), max(2, int(4 * s)))
    # Tip of haft protruding slightly through the eye
    butt = _along(head_mount, angle, 6 * s)
    _line(surf, WOOD_LIGHT, head_mount, butt, max(1, int(3 * s)))


def _draw_hammer(
    surf: pygame.Surface,
    grip: Point,
    tip: Point,
    angle: float,
    length: float,
    scale: float,
) -> None:
    """War hammer: wooden haft + blocky metal head with peen."""
    s = scale
    mount = _along(grip, angle, length * 0.8)
    _line(surf, WOOD_DARK, grip, mount, max(3, int(7 * s)))
    _line(surf, WOOD, grip, mount, max(2, int(5 * s)))
    wrap = _along(grip, angle, length * 0.2)
    _line(surf, LEATHER, grip, wrap, max(2, int(7 * s)))
    px, py = _perp(angle, 1.0)
    # Rectangular striking face
    face_w, face_h = 10 * s, 8 * s
    corners = [
        _offset(_along(mount, angle, -face_h), -px * face_w, -py * face_w),
        _offset(_along(mount, angle, -face_h), px * face_w, py * face_w),
        _offset(_along(mount, angle, face_h), px * face_w, py * face_w),
        _offset(_along(mount, angle, face_h), -px * face_w, -py * face_w),
    ]
    _poly(surf, IRON, corners)
    _poly(
        surf,
        STEEL_DARK,
        [
            corners[1],
            corners[2],
            _offset(corners[2], px * 3 * s, py * 3 * s),
            _offset(corners[1], px * 3 * s, py * 3 * s),
        ],
    )
    # Peen spike opposite the face
    peen = _offset(mount, -px * 14 * s, -py * 14 * s)
    _poly(
        surf,
        STEEL,
        [
            _offset(mount, -px * 3 * s, -py * 3 * s),
            _offset(_along(mount, angle, 4 * s), -px * 3 * s, -py * 3 * s),
            peen,
            _offset(_along(mount, angle, -4 * s), -px * 3 * s, -py * 3 * s),
        ],
    )


def _draw_pickaxe(
    surf: pygame.Surface,
    grip: Point,
    tip: Point,
    angle: float,
    length: float,
    scale: float,
) -> None:
    """Pickaxe: haft + dual-pointed pick head."""
    s = scale
    mount = _along(grip, angle, length * 0.78)
    _line(surf, WOOD_DARK, grip, mount, max(3, int(6 * s)))
    _line(surf, WOOD, grip, mount, max(2, int(4 * s)))
    wrap = _along(grip, angle, length * 0.18)
    _line(surf, LEATHER, grip, wrap, max(2, int(6 * s)))
    px, py = _perp(angle, 1.0)
    # Two curved picks
    for sign in (-1, 1):
        tip_p = _offset(
            _along(mount, angle, sign * 4 * s),
            px * sign * 18 * s,
            py * sign * 18 * s,
        )
        base_a = _offset(mount, px * sign * 3 * s, py * sign * 3 * s)
        base_b = _along(mount, angle, sign * 6 * s)
        _poly(surf, STEEL_DARK, [mount, base_a, tip_p, base_b])
        _line(surf, STEEL, base_a, tip_p, max(1, int(2 * s)))
    pygame.draw.circle(surf, IRON, _i(mount), max(2, int(4 * s)))


def _draw_stick(
    surf: pygame.Surface,
    grip: Point,
    tip: Point,
    angle: float,
    length: float,
    scale: float,
) -> None:
    """Wooden staff/club with grain banding and a thicker tip."""
    s = scale
    _line(surf, WOOD_DARK, grip, tip, max(3, int(7 * s)))
    _line(surf, WOOD, grip, tip, max(2, int(5 * s)))
    # Knot / tip bulb
    pygame.draw.circle(surf, WOOD_LIGHT, _i(tip), max(2, int(6 * s)))
    # Grain bands
    for t in (0.25, 0.5, 0.75):
        p = _along(grip, angle, length * t)
        px, py = _perp(angle, 3.5 * s)
        _line(surf, WOOD_DARK, _offset(p, -px, -py), _offset(p, px, py), 1)


# ── Throw weapons ───────────────────────────────────────────────────


def _draw_spear(
    surf: pygame.Surface,
    grip: Point,
    tip: Point,
    angle: float,
    length: float,
    scale: float,
) -> None:
    """Spear: long wooden shaft + leaf-shaped spearhead + socket."""
    s = scale
    head_base = _along(grip, angle, length * 0.72)
    _line(surf, WOOD_DARK, grip, head_base, max(2, int(5 * s)))
    _line(surf, WOOD, grip, head_base, max(2, int(3 * s)))
    # Binding / socket
    _line(surf, IRON, _along(head_base, angle, -6 * s), head_base, max(2, int(5 * s)))
    # Leaf blade
    px, py = _perp(angle, 6 * s)
    mid = _along(head_base, angle, length * 0.14)
    _poly(
        surf,
        STEEL,
        [
            head_base,
            _offset(mid, -px, -py),
            tip,
            _offset(mid, px, py),
        ],
    )
    _line(surf, STEEL_EDGE, head_base, tip, max(1, int(1 * s)))


def _draw_javelin(
    surf: pygame.Surface,
    grip: Point,
    tip: Point,
    angle: float,
    length: float,
    scale: float,
) -> None:
    """Javelin: slender shaft + small piercing head + rear balance."""
    s = scale
    head_base = _along(grip, angle, length * 0.82)
    _line(surf, WOOD, grip, head_base, max(1, int(3 * s)))
    # Rear fletch / counterweight ring
    rear = _along(grip, angle, length * 0.08)
    pygame.draw.circle(surf, IRON, _i(rear), max(2, int(3 * s)))
    # Slim point
    px, py = _perp(angle, 3.5 * s)
    _poly(surf, STEEL, [head_base, _offset(head_base, -px, -py), tip, _offset(head_base, px, py)])


def _draw_trident(
    surf: pygame.Surface,
    grip: Point,
    tip: Point,
    angle: float,
    length: float,
    scale: float,
) -> None:
    """Trident: shaft + three-pronged fork head with crossbar."""
    s = scale
    head_base = _along(grip, angle, length * 0.62)
    _line(surf, WOOD_DARK, grip, head_base, max(2, int(5 * s)))
    _line(surf, WOOD, grip, head_base, max(2, int(3 * s)))
    # Socket + crossbar
    _line(surf, IRON, _along(head_base, angle, -5 * s), head_base, max(2, int(5 * s)))
    px, py = _perp(angle, 12 * s)
    _line(surf, STEEL_DARK, _offset(head_base, -px, -py), _offset(head_base, px, py), max(2, int(3 * s)))
    # Three prongs
    for frac, length_mul in ((-1.0, 0.85), (0.0, 1.0), (1.0, 0.85)):
        base = _offset(head_base, px * frac * 0.85, py * frac * 0.85)
        end = _along(base, angle, length * 0.32 * length_mul)
        _line(surf, STEEL, base, end, max(2, int(3 * s)))
        # Barbed tip
        bpx, bpy = _perp(angle, 4 * s)
        _line(surf, STEEL_EDGE, end, _offset(_along(end, angle, -5 * s), -bpx, -bpy), 2)
        _line(surf, STEEL_EDGE, end, _offset(_along(end, angle, -5 * s), bpx, bpy), 2)


def _draw_bow(
    surf: pygame.Surface,
    grip: Point,
    tip: Point,
    angle: float,
    length: float,
    scale: float,
) -> None:
    """Bow: curved stave + string, with a nocked arrow along the aim line."""
    s = scale
    # Treat grip→tip as aim direction; bow stave sits across the grip.
    px, py = _perp(angle, 1.0)
    half = max(16.0, length * 0.55) * s
    # Approximate an arc with a thick polyline (top limb / bottom limb).
    top = _offset(grip, px * half, py * half)
    bot = _offset(grip, -px * half, -py * half)
    belly = _along(grip, angle, -10 * s)  # curve of the bow away from target
    # Stave
    mid_top = (
        (top[0] + belly[0]) * 0.5 + px * 2 * s,
        (top[1] + belly[1]) * 0.5 + py * 2 * s,
    )
    mid_bot = (
        (bot[0] + belly[0]) * 0.5 - px * 2 * s,
        (bot[1] + belly[1]) * 0.5 - py * 2 * s,
    )
    _line(surf, WOOD_DARK, top, mid_top, max(2, int(4 * s)))
    _line(surf, WOOD_DARK, mid_top, belly, max(2, int(4 * s)))
    _line(surf, WOOD_DARK, belly, mid_bot, max(2, int(4 * s)))
    _line(surf, WOOD_DARK, mid_bot, bot, max(2, int(4 * s)))
    _line(surf, WOOD, top, mid_top, max(1, int(2 * s)))
    _line(surf, WOOD, mid_bot, bot, max(1, int(2 * s)))
    # String
    _line(surf, STEEL_EDGE, top, bot, max(1, int(1 * s)))
    # Nocked arrow along aim
    arrow_nock = _along(grip, angle, -6 * s)
    arrow_tip = tip
    _line(surf, ARROW_SHAFT, arrow_nock, arrow_tip, max(1, int(2 * s)))
    # Arrowhead
    apx, apy = _perp(angle, 4 * s)
    head_base = _along(arrow_tip, angle, -8 * s)
    _poly(
        surf,
        STEEL,
        [arrow_tip, _offset(head_base, -apx, -apy), _offset(head_base, apx, apy)],
    )
    # Fletching
    fletch = _along(arrow_nock, angle, 8 * s)
    for sign in (-1, 1):
        fp = _offset(fletch, apx * sign * 0.9, apy * sign * 0.9)
        _line(surf, ARROW_FEATHER, arrow_nock, fp, max(1, int(2 * s)))


def _draw_arrow_only(
    surf: pygame.Surface,
    grip: Point,
    tip: Point,
    angle: float,
    length: float,
    scale: float,
) -> None:
    """Flying arrow (projectile form of the bow weapon)."""
    s = scale
    _line(surf, ARROW_SHAFT, grip, tip, max(1, int(2 * s)))
    px, py = _perp(angle, 4.5 * s)
    head_base = _along(tip, angle, -9 * s)
    _poly(surf, STEEL, [tip, _offset(head_base, -px, -py), _offset(head_base, px, py)])
    # Fletching at the rear
    for sign in (-1, 1):
        fp = _offset(_along(grip, angle, 10 * s), px * sign, py * sign)
        _line(surf, ARROW_FEATHER, grip, fp, max(1, int(2 * s)))


def _draw_generic_shaft(
    surf: pygame.Surface,
    grip: Point,
    tip: Point,
    angle: float,
    length: float,
    scale: float,
) -> None:
    """Fallback simple shaft."""
    del angle, length
    _line(surf, STEEL, grip, tip, max(2, int(4 * scale)))


_DRAWERS = {
    "sword": _draw_sword,
    "broadsword": _draw_broadsword,
    "axe": _draw_axe,
    "hammer": _draw_hammer,
    "pickaxe": _draw_pickaxe,
    "stick": _draw_stick,
    "spear": _draw_spear,
    "javelin": _draw_javelin,
    "trident": _draw_trident,
    "bow": _draw_bow,
    "arrow": _draw_arrow_only,
}


def draw_projectile_weapon(
    surf: pygame.Surface,
    weapon_key: str,
    grip: Point,
    tip: Point,
) -> None:
    """Draw a weapon in flight (bow becomes an arrow)."""
    key = "arrow" if weapon_key == "bow" else weapon_key
    draw_weapon(surf, key, grip, tip, scale=1.0)


def draw_panel_icon(
    surf: pygame.Surface,
    weapon_key: str,
    center: Point,
    size: float = 22.0,
) -> None:
    """Mini weapon icon for the left-side selector panel."""
    half = size * 0.5
    # Horizontal icon for readability in the panel.
    grip = (center[0] - half, center[1])
    tip = (center[0] + half, center[1])
    key = weapon_key
    draw_weapon(surf, key, grip, tip, scale=0.55)
