# SingleSnakeGame（疯狂贪吃蛇）

Cocos2d-JS (cocos2d-html5) single-player snake / Slither-style browser game.

## Run

```bash
cd SingleSnakeGame
python3 -m http.server 8090
```

Open http://localhost:8090/ — must be served over HTTP (not `file://`).

## Controls

Click the game once so the canvas has focus, then:

1. `Arrow Up` / `Arrow Down` / `Arrow Left` / `Arrow Right` — steer
2. Hold `A` (or `Space`) — boost (needs enough length, same as the on-screen button)
3. On-screen joystick still works for steering


## Engine

`frameworks/cocos2d-html5/` is vendored from
[HappyLittleGame-SoccerGame](https://github.com/brandyxie100/HappyLittleGame-SoccerGame/tree/main/frameworks/cocos2d-html5)
(Cocos2d-JS v3.11). Do not modify the engine for routine game work.

## Agent skill

Cursor agents: see [`.cursor/skills/singlesnakegame/SKILL.md`](../.cursor/skills/singlesnakegame/SKILL.md)
for architecture, runbook, and optimisation hotspots.
