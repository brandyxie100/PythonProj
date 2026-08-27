---
name: singlesnakegame
description: >-
  Run, debug, and optimise SingleSnakeGame — a Cocos2d-JS (cocos2d-html5 v3.11)
  single-player snake / Slither-style browser game. Use when working on
  SingleSnakeGame/, its engine under frameworks/cocos2d-html5/, gameplay
  performance, AI robots, food spawning, UI, or local-serve setup.
---

# SingleSnakeGame

## Quick start

```bash
cd SingleSnakeGame
python3 -m http.server 8090
# open http://localhost:8090/
```

Must be served over HTTP (not `file://`) so Cocos can XHR-load `project.json`,
`res/resource-zh.json`, and Cocos Studio JSON/plist assets.

Design resolution: **1334×750** landscape, `FIXED_HEIGHT`. Target FPS: **30**
(`project.json` → `frameRate`).

## Engine provenance

`frameworks/cocos2d-html5/` is the Cocos2d-JS HTML5 runtime (reports
`Cocos2d-JS v3.11` at boot). It was vendored from:

https://github.com/brandyxie100/HappyLittleGame-SoccerGame/tree/main/frameworks/cocos2d-html5

Do **not** "upgrade" this engine casually — cocos2d-html5 is deprecated and not
API-compatible with Cocos Creator. Treat the engine as frozen; optimise game
code under `src/` instead.

`project.json` modules: `cocos2d`, `extensions` (needed for `ccs.load` /
Cocos Studio UI).

## Architecture

| Layer | Role | Key paths |
|-------|------|-----------|
| Boot | `index.html` → `CCBoot.js` → `main.js` → preload `resGroup.Main` → `LoginScene` | `index.html`, `main.js`, `project.json` |
| Login / loading | Loading animation; local auto-login seeds `NetProxy.Login` so the match can start without a host H5 SDK | `src/scene/login/LoginScene.js` |
| In-browser "server" | Webpack bundle of `gameServer/` logic; drives AI, food, collisions, room timer | `src/server/bundle.js` (`serverLogic`), source under `gameServer/` |
| Net façade | Client ↔ local server packets | `src/network/NetProxy.js`, `NetManager.js`, `PDataDef.js` |
| Gameplay scene | Map, snakes, food, camera follow | `src/scene/main/*`, `src/player/Snake.js`, `PlayerManager.js` |
| UI | HUD, joystick, boost, ranking | `src/scene/main/MainUILayer.js`, `src/gui/**` |
| Data / assets | Config JSON, sprite plists, locale | `res/`, `src/resource.js`, `src/data/*` |

Flow: `LoginScene` → `NetProxy.Login` → `ON_START_GAME_EVENT` →
`NetProxy.startServer` → `serverLogic.runServer()` → `MainGameScene`.

Standalone stubs (host SDK): `window.playGame`, `window.closeOutSound` in
`index.html`. Real embeds may replace them.

## Optimisation hotspots (future work)

Prioritise measured work; confirm with FPS overlay (`showFPS: true` in
`project.json`) and Chrome Performance / Memory panels.

1. **Snake rendering** — `src/player/Snake.js` (~1k LOC). Segment sprites,
   trail, skins. Candidates: object pools, fewer draw calls, cull off-screen
   segments, simplify when many AI snakes are active.
2. **Food layer** — `src/scene/main/FoodLayer.js`, `Food.js`. High spawn rates
   from `res/game_config*.json` (`n_food_per_sec`, `m_food_max_num`). Pool
   nodes; avoid per-frame texture work.
3. **AI / server tick** — `gameServer/` (controllers, collision/quadtree,
   `SnakeService`, `FoodService`). Bundle is `src/server/bundle.js`; rebuild
   via `gameServer/webpack.config.js` after editing server sources.
4. **UI / Cocos Studio** — `ccs.load` JSON under `res/scene/`. Heavy UI trees
   and `uiWidget is not widget type` warnings. Cache loaded nodes; avoid
   reloading on every restart.
5. **Audio** — autoplay is blocked without a user gesture; gate
   `MusicManager` until first tap. Not a perf issue, but reduces console noise.
6. **Config tuning** — `res/game_config.json` vs `res/game_config_newGuy.json`
   (chosen by `historyScore < new_guy_length`). Safer to tune difficulty /
   spawn rates here than in engine code.

## Web-only caveats

- `cc.view.setOrientation` is **native-only**; `main.js` guards it.
- Opening via `file://` fails resource loads — always use a static server.
- `SingleSnakeGame/gameServer/` Node layout is the **source** for the
  in-browser bundle, not a separate process you must start for local play.

## Verification checklist

- [ ] `http://localhost:8090/frameworks/cocos2d-html5/CCBoot.js` → 200
- [ ] Console shows `Cocos2d-JS v3.11`, then `MainGameScene: onEnter`
- [ ] Canvas shows snake, food orbs, joystick, timer, mini-map
- [ ] Dragging the joystick / clicking boost moves or accelerates the snake

## Related files to leave alone unless migrating engines

- `frameworks/cocos2d-html5/**` (vendored engine)
- `CMakeLists.txt`, `build.xml` (native cocos2d-x paths; optional / incomplete)
