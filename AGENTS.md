# Agent guidance for PythonProj

This repository is a **multi-game collection**: Python/pygame games, a few browser
games, and legacy Cocos2d-JS projects. Agents should combine **repo-specific
knowledge** (domain skills, environment config) with **process methodology**
(Superpowers) without letting either layer fight the other.

---

## One-time setup: Superpowers (per developer machine)

Superpowers is a **Cursor plugin**, not files in this repo. Install it once on
your machine:

```text
/add-plugin superpowers
```

Or search **“superpowers”** in Cursor’s plugin marketplace (by Jesse Vincent /
[obra/superpowers](https://github.com/obra/superpowers)).

Verify in a new Agent chat:

```text
Do you have superpowers? List skills relevant to this repo.
```

Optional: disable Superpowers telemetry (brainstorming visual companion beacon):

```bash
export SUPERPOWERS_DISABLE_TELEMETRY=1
```

Add that to your shell profile if you want it permanent.

**Do not** copy the Superpowers repo into `.cursor/skills/` — use the plugin so
updates stay automatic.

---

## Skill precedence (read this first)

When instructions conflict, follow this order:

| Priority | Source | Examples |
|----------|--------|----------|
| 1 | **Your direct instruction** in chat | “Skip TDD for this tweak” |
| 2 | **This `AGENTS.md`** | Precedence, repo conventions |
| 3 | **Repo domain skills** (`.cursor/skills/*/SKILL.md`) | `singlesnakegame` |
| 4 | **Superpowers process skills** (plugin) | `brainstorming`, `systematic-debugging`, `test-driven-development` |
| 5 | **Global Cursor skills** | `env-setup`, `walkthrough-artifacts`, `code-review` |
| 6 | Default agent behaviour | — |

### How layers combine

- **Superpowers** answers *how* to work (spec → plan → implement → verify).
- **Domain skills** answer *what this codebase is* (entry points, pitfalls,
  optimisation hotspots).
- **`env-setup`** answers *how to boot the dev environment* (venv, Xvfb, ports).
- **`walkthrough-artifacts`** answers *what proof to show* when claiming “done”.
- **`code-review` / CodeRabbit** answers *how to review PRs* — prefer these over
  Superpowers `requesting-code-review` unless the user asks for both.

---

## When to use Superpowers skills

| Situation | Superpowers skill | Also load |
|-----------|-------------------|-----------|
| New feature or non-trivial refactor | `brainstorming` → `writing-plans` | Relevant domain skill |
| Bug with unclear root cause | `systematic-debugging` | Domain skill if game-specific |
| Implementing logic in a game **with existing pytest** | `test-driven-development` | Domain skill |
| Long multi-step implementation | `executing-plans` or `subagent-driven-development` | Domain skill |
| Branch/PR wrap-up after planned work | `finishing-a-development-branch` | — |

### When to use a **light** workflow (skip heavy Superpowers)

- Environment setup, vendoring engines, dependency installs → **`env-setup`**
- “Get X running” bootstrap → **`env-setup`** + domain skill
- README / comment-only edits
- Visual-only tweaks in legacy games with no test harness
- Single-file typo or config value change

For these, **do not** force a full design doc or multi-page implementation plan.

---

## Repo domain skills

Skills live under `.cursor/skills/`. Add a new folder + `SKILL.md` when a game
or subsystem needs persistent agent context.

| Skill | Path | Use when |
|-------|------|----------|
| SingleSnakeGame | `.cursor/skills/singlesnakegame/SKILL.md` | Cocos2d-JS snake game, `frameworks/cocos2d-html5/`, performance, local serve |

See `.cursor/skills/README.md` for the template to add more.

---

## Repository map (quick orientation)

### Python / pygame games (shared `.venv`)

Run after `source .venv/bin/activate` and `DISPLAY=:99` for headless GUI capture:

| Game | Entry | Tests |
|------|-------|-------|
| BlumgiMerge | `BlumgiMerge/main.py` | `pytest` in dir |
| GamePlantsVsZombies | `GamePlantsVsZombies/main.py` | `pytest` in dir |
| jump | `jump/main.py` | `pytest` in dir |
| python-game-angry-birds | `python-game-angry-birds/src/main.py` | `PYTHONPATH=src pytest` |
| ragdoll-hit | `ragdoll-hit/main.py` | `pytest` in dir |
| stickman_battle | `stickman_battle/main.py` | `pytest` in dir |
| Tank1990 | `Tank1990/main.py` | — |
| TankStars | `TankStars/main.py` | `pytest` in dir |
| FlyCode/flappybird | `FlyCode/flappybird/bird.py` | — |

### Browser games

| Game | Serve | URL |
|------|-------|-----|
| SingleSnakeGame | `cd SingleSnakeGame && python3 -m http.server 8090` | http://localhost:8090/ |
| pocket_zoo | `cd pocket_zoo && python3 serve.py` | http://localhost:8080/ |

Cloud Agent terminals for web games are defined in `.cursor/environment.json`
(`singlesnake`, `pocket-zoo`).

### Environment bootstrap

- Config: `.cursor/environment.json`
- Install script: `.cursor/install.sh` (venv, pygame/pymunk, Xvfb, SDL libs)
- For env questions or changes: use the **`env-setup`** skill

---

## Testing expectations

Not every game has pytest. Match effort to the project:

| Project type | Expectation |
|--------------|-------------|
| Games with `tests/` and pytest | Run tests; use TDD when adding non-trivial logic |
| Legacy games without tests | Manual/browser verification + walkthrough artifacts |
| Env / engine vendoring | Build or install script succeeds; smoke-run the app |

**Always** for non-trivial Cloud Agent changes: produce **walkthrough artifacts**
(screenshots/video) per the `walkthrough-artifacts` skill.

GUI pygame games: `DISPLAY=:99 SDL_VIDEODRIVER=x11 SDL_AUDIODRIVER=dummy`.

---

## Code review

For “review my changes / PR / diff” requests:

1. Use the **`code-review`** skill and CodeRabbit reviewer agent.
2. Do **not** duplicate the same pass with Superpowers `requesting-code-review`
   unless the user explicitly wants both.

---

## Git and PR conventions (Cloud Agents)

- Feature branches: `cursor/<descriptive-name>-1be4`
- Push with `git push -u origin <branch>`
- Open/update PRs via the ManagePullRequest tool
- Commit logical units separately; write complete-sentence messages

---

## Adding a new domain skill

1. Create `.cursor/skills/<name>/SKILL.md` with YAML frontmatter (`name`,
   `description` with trigger phrases).
2. Include: quick start, architecture table, verification checklist,
   optimisation hotspots (if applicable).
3. Register it in `.cursor/skills/README.md` and the table above in this file.
4. `.gitignore` already tracks `.cursor/skills/**` — no gitignore change needed.

Follow Superpowers `writing-skills` guidance for skill structure when creating
new skills.

---

## Example agent flows

### “Optimise SingleSnakeGame food spawning”

1. Superpowers: `brainstorming` (short — scoped optimisation)
2. Domain: `.cursor/skills/singlesnakegame/SKILL.md`
3. Superpowers: `writing-plans` (if change touches multiple files)
4. Implement; measure with FPS overlay
5. Walkthrough: screenshot or short video of gameplay
6. PR

### “Set up / fix Cloud Agent environment”

1. **`env-setup`** skill (not full Superpowers design workflow)
2. Edit `.cursor/environment.json` / `install.sh` as needed
3. Trigger draft build if validating install
4. Document in PR

### “Fix pygame game won’t start in headless VM”

1. `systematic-debugging` if cause is unknown
2. `env-setup` for Xvfb / SDL / `SDL_VIDEODRIVER=x11`
3. Smoke-run + screenshot artifact
