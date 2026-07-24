"""Twenty Midway Atoll missions — waves, bosses, and scroll pacing."""

from __future__ import annotations

from dataclasses import dataclass

import config as cfg


@dataclass(frozen=True)
class WaveSpec:
    """One spawn wave inside a mission."""

    delay: float  # seconds after mission start
    kind: str
    count: int
    formation: str  # "line" | "v" | "swarm" | "row"
    hp: int
    score: int
    vy: float = 90.0
    fire_cd: float = 1.2


@dataclass(frozen=True)
class MissionSpec:
    """Full mission definition."""

    number: int
    title: str
    briefing: str
    scroll_speed: float
    waves: tuple[WaveSpec, ...]
    boss_name: str | None
    clear_time: float  # soft time before boss / victory if waves clear


def _score(kind: str) -> int:
    return {
        "fighter": cfg.SCORE_FIGHTER,
        "interceptor": cfg.SCORE_INTERCEPTOR,
        "bomber": cfg.SCORE_BOMBER,
        "dive": cfg.SCORE_DIVE,
        "gunboat": cfg.SCORE_GUNBOAT,
    }[kind]


def _hp(kind: str, mission: int) -> int:
    base = {"fighter": 2, "interceptor": 2, "bomber": 6, "dive": 3, "gunboat": 8}[kind]
    return base + mission // 4


def _mission(
    number: int,
    title: str,
    briefing: str,
    waves: list[tuple],
    boss: str | None,
    scroll: float | None = None,
) -> MissionSpec:
    """Helper to build MissionSpec from compact wave tuples.

    Wave tuple: (delay, kind, count, formation[, fire_cd])
    """
    specs: list[WaveSpec] = []
    for wave in waves:
        delay, kind, count, formation = wave[:4]
        fire_cd = wave[4] if len(wave) > 4 else max(0.45, 1.3 - number * 0.03)
        specs.append(
            WaveSpec(
                delay=delay,
                kind=kind,
                count=count,
                formation=formation,
                hp=_hp(kind, number),
                score=_score(kind),
                vy=70 + number * 3 + (20 if kind == "interceptor" else 0),
                fire_cd=fire_cd,
            )
        )
    clear = (specs[-1].delay + 12.0) if specs else 20.0
    return MissionSpec(
        number=number,
        title=title,
        briefing=briefing,
        scroll_speed=scroll or (cfg.OCEAN_SCROLL_BASE + number * 3),
        waves=tuple(specs),
        boss_name=boss,
        clear_time=clear,
    )


MISSIONS: tuple[MissionSpec, ...] = (
    _mission(
        1,
        "Dawn Patrol",
        "First contact over the Midway lagoon. Intercept light Zero scouts.",
        [
            (1.0, "fighter", 3, "line"),
            (6.0, "fighter", 4, "v"),
            (12.0, "fighter", 5, "swarm"),
        ],
        None,
    ),
    _mission(
        2,
        "Reef Skirmish",
        "Enemy flights hug the eastern reef. Stay low and strike.",
        [
            (1.0, "fighter", 4, "line"),
            (5.0, "dive", 2, "line"),
            (10.0, "fighter", 6, "v"),
            (16.0, "dive", 3, "swarm"),
        ],
        None,
    ),
    _mission(
        3,
        "Carrier Shadow",
        "Bombers inbound on Task Force Midway. Break their formation.",
        [
            (1.5, "fighter", 4, "v"),
            (6.0, "bomber", 2, "line"),
            (12.0, "fighter", 5, "swarm"),
            (18.0, "bomber", 2, "row"),
        ],
        "Scout Wing Leader",
    ),
    _mission(
        4,
        "Sandbar Ambush",
        "Interceptors dive from the sun. Watch your six.",
        [
            (1.0, "interceptor", 3, "line"),
            (6.0, "fighter", 5, "v"),
            (11.0, "interceptor", 4, "swarm"),
            (17.0, "dive", 3, "line"),
        ],
        None,
    ),
    _mission(
        5,
        "Lagoon Crossfire",
        "Coastal gunboats join the air war. Clear both lanes.",
        [
            (1.0, "gunboat", 2, "row"),
            (5.0, "fighter", 5, "line"),
            (10.0, "gunboat", 2, "line"),
            (14.0, "bomber", 2, "v"),
            (20.0, "interceptor", 4, "swarm"),
        ],
        None,
    ),
    _mission(
        6,
        "Iron Rain",
        "A heavy flight screens a flying fortress. Survive the barrage.",
        [
            (1.0, "fighter", 6, "swarm"),
            (7.0, "bomber", 3, "line"),
            (13.0, "interceptor", 4, "v"),
            (19.0, "dive", 4, "swarm"),
        ],
        "Flying Fortress Akagi-Shadow",
    ),
    _mission(
        7,
        "Coral Gauntlet",
        "Tight channels between islets — no room for error.",
        [
            (1.0, "dive", 4, "line"),
            (6.0, "fighter", 6, "v"),
            (11.0, "interceptor", 5, "swarm"),
            (17.0, "gunboat", 3, "row"),
        ],
        None,
        scroll=cfg.OCEAN_SCROLL_BASE + 40,
    ),
    _mission(
        8,
        "Night Haze",
        "Low visibility. Enemy tracers light the sky.",
        [
            (1.0, "interceptor", 4, "line"),
            (6.0, "bomber", 2, "line"),
            (11.0, "fighter", 8, "swarm"),
            (18.0, "interceptor", 5, "v"),
        ],
        None,
    ),
    _mission(
        9,
        "Double Front",
        "Simultaneous bomber and gunboat assault on the fleet.",
        [
            (1.0, "bomber", 3, "row"),
            (5.0, "gunboat", 3, "line"),
            (10.0, "fighter", 6, "v"),
            (15.0, "dive", 4, "swarm"),
            (22.0, "bomber", 3, "line"),
        ],
        "Battleship Escort Wing",
    ),
    _mission(
        10,
        "Midway Siege I",
        "Halfway through the campaign. The sky fills with Zeroes.",
        [
            (1.0, "fighter", 8, "swarm"),
            (6.0, "interceptor", 6, "v"),
            (12.0, "bomber", 3, "line"),
            (18.0, "dive", 5, "swarm"),
            (24.0, "fighter", 8, "line"),
        ],
        None,
    ),
    _mission(
        11,
        "Propeller Storm",
        "Elite interceptors hunt in packs.",
        [
            (1.0, "interceptor", 6, "swarm"),
            (7.0, "interceptor", 6, "v"),
            (13.0, "fighter", 8, "line"),
            (19.0, "dive", 5, "swarm"),
        ],
        None,
    ),
    _mission(
        12,
        "Fortress Descent",
        "A reinforced aerial battleship descends on the atoll.",
        [
            (1.0, "bomber", 3, "line"),
            (6.0, "fighter", 7, "swarm"),
            (12.0, "gunboat", 3, "row"),
            (17.0, "interceptor", 6, "v"),
        ],
        "Aerial Battleship Kaga-Echo",
    ),
    _mission(
        13,
        "Sunward Dive",
        "Dive bombers attack from high altitude.",
        [
            (1.0, "dive", 6, "line"),
            (6.0, "dive", 6, "swarm"),
            (12.0, "fighter", 8, "v"),
            (18.0, "bomber", 3, "line"),
        ],
        None,
    ),
    _mission(
        14,
        "Broken Formation",
        "Disorganized but dense enemy traffic — opportunity and danger.",
        [
            (1.0, "fighter", 10, "swarm"),
            (8.0, "interceptor", 6, "line"),
            (14.0, "bomber", 4, "row"),
            (20.0, "gunboat", 4, "line"),
        ],
        None,
    ),
    _mission(
        15,
        "Fleet Defense",
        "Protect the carriers. Nothing reaches the southern edge.",
        [
            (1.0, "bomber", 4, "line"),
            (6.0, "bomber", 3, "v"),
            (11.0, "interceptor", 7, "swarm"),
            (17.0, "dive", 6, "line"),
            (23.0, "fighter", 10, "swarm"),
        ],
        "Carrier Raider Soryu-Phantom",
    ),
    _mission(
        16,
        "Atoll Inferno",
        "Smoke over Midway. Push through the fire corridor.",
        [
            (1.0, "fighter", 10, "swarm"),
            (6.0, "gunboat", 4, "row"),
            (11.0, "dive", 7, "v"),
            (17.0, "interceptor", 8, "swarm"),
        ],
        None,
        scroll=cfg.OCEAN_SCROLL_BASE + 55,
    ),
    _mission(
        17,
        "Last Light",
        "Sunset sorties — the enemy commits reserves.",
        [
            (1.0, "interceptor", 8, "v"),
            (7.0, "bomber", 4, "line"),
            (13.0, "fighter", 12, "swarm"),
            (20.0, "dive", 6, "line"),
        ],
        None,
    ),
    _mission(
        18,
        "Steel Horizon",
        "A wall of bombers escorted by aces.",
        [
            (1.0, "bomber", 5, "row"),
            (6.0, "interceptor", 8, "swarm"),
            (12.0, "bomber", 4, "line"),
            (18.0, "fighter", 10, "v"),
            (24.0, "gunboat", 4, "line"),
        ],
        "Sky Dreadnought Hiryu-Wraith",
    ),
    _mission(
        19,
        "Final Approach",
        "Break the outer screen before the command fortress.",
        [
            (1.0, "fighter", 12, "swarm"),
            (6.0, "interceptor", 8, "v"),
            (11.0, "dive", 8, "swarm"),
            (16.0, "bomber", 5, "line"),
            (22.0, "gunboat", 5, "row"),
            (28.0, "interceptor", 10, "swarm"),
        ],
        None,
    ),
    _mission(
        20,
        "Midway Decided",
        "Intercept the flagship raid. The Pacific hangs in the balance.",
        [
            (1.0, "fighter", 10, "swarm"),
            (5.0, "bomber", 4, "line"),
            (10.0, "interceptor", 10, "v"),
            (15.0, "dive", 8, "swarm"),
            (20.0, "gunboat", 4, "row"),
            (25.0, "bomber", 5, "line"),
            (30.0, "fighter", 12, "swarm"),
        ],
        "Combined Fleet Flagship — Midway Eclipse",
        scroll=cfg.OCEAN_SCROLL_BASE + 70,
    ),
)

assert len(MISSIONS) == cfg.TOTAL_MISSIONS
