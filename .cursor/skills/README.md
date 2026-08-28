# Repo domain skills

Skills in this folder teach agents **project-specific** knowledge: how to run a
game, where the architecture lives, and what to optimise. They complement
**Superpowers** (process methodology installed as a Cursor plugin) and global
skills like `env-setup` and `walkthrough-artifacts`.

## Precedence

See [AGENTS.md](../../AGENTS.md) at the repo root for the full precedence order.

Short version: **your instruction → AGENTS.md → domain skills here → Superpowers
→ global Cursor skills**.

## Installed skills

| Skill | Folder | Triggers on |
|-------|--------|-------------|
| SingleSnakeGame | `singlesnakegame/` | `SingleSnakeGame/`, Cocos2d-JS, snake game performance |

## Add a new skill

1. Create `your-skill-name/SKILL.md`.
2. YAML frontmatter:

   ```yaml
   ---
   name: your-skill-name
   description: >-
     One paragraph: what this covers and when an agent should load it.
     Include path keywords and task types (run, debug, optimise, etc.).
   ---
   ```

3. Sections to include:
   - Quick start (exact commands)
   - Architecture / key files table
   - Verification checklist
   - Optimisation or maintenance notes (if relevant)
   - “Leave alone” list (vendored engines, generated files)

4. Add a row to the table above and to `AGENTS.md`.

For skill authoring quality, follow Superpowers `writing-skills` (from the
plugin) when available.

## Superpowers (not stored here)

Install once per machine:

```text
/add-plugin superpowers
```

Do **not** vendor `github.com/obra/superpowers` into this directory.
