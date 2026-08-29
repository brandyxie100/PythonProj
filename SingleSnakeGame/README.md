# SingleSnakeGame（疯狂贪吃蛇）

Cocos2d-JS (cocos2d-html5) single-player snake / Slither-style browser game.

## Run

```bash
cd SingleSnakeGame
python3 -m http.server 8090
```

Open http://localhost:8090/ — must be served over HTTP (not `file://`).

## Controls

| Action | Keyboard Key | Alternative |
|---|---|---|
| **Move Up** | `Arrow Up` | `W` |
| **Move Down** | `Arrow Down` | `S` |
| **Move Left** | `Arrow Left` | |
| **Move Right** | `Arrow Right` | `D` |
| **Acceleration / Sprint** | `A` | `Space` / Boost Button |


## Engine

`frameworks/cocos2d-html5/` is vendored from
[HappyLittleGame-SoccerGame](https://github.com/brandyxie100/HappyLittleGame-SoccerGame/tree/main/frameworks/cocos2d-html5)
(Cocos2d-JS v3.11). Do not modify the engine for routine game work.

## Agent skill

Cursor agents: see [`.cursor/skills/singlesnakegame/SKILL.md`](../.cursor/skills/singlesnakegame/SKILL.md)
for architecture, runbook, and optimisation hotspots.
