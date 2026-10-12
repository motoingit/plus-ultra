---
trigger: model_decision
description: "Consult when planning, creating, or reorganizing the project's directory and file structure."
---

# General Project Structure

Keep this separation as the application grows. Create a file or directory only in the phase of `.agents/initial-plan.md` that needs it.

## Layout

```
plus-ultra/
├── AGENTS.md                  # project instructions (single source of truth)
├── GEMINI.md                  # optional, project root; must not contradict AGENTS.md
├── plan.md                    # phased build plan
├── pyproject.toml
├── README.md
├── .agents/
│   ├── rules/                 # specialized Antigravity rules
│   ├── skills/                # one folder per skill, each with SKILL.md
│   └── workflows/
├── .my/                       # the user's private notes; agents read, never rewrite
├── src/plus_ultra/            # application source (see .agents/initial-plan.md for modules)
└── tests/                     # pytest tests
```

## Rules

- Keep application source code in `src/plus_ultra/`.
- Keep project instructions in `AGENTS.md` at the project root.
- If `GEMINI.md` is used, keep it at the project root. Antigravity gives it precedence over `AGENTS.md`, so it must not contradict it.
- Keep specialized Antigravity rules in `.agents/rules/`.
- Keep tests in `tests/`, mirroring module names (`repository.py` is tested by `test_repository.py`).
- Keep editor-specific configuration in `.vscode/`.
- Keep documentation in appropriately named Markdown files, such as `README.md`.
- Do not use standard-library module names for files or packages (`code`, `platform`, `queue`, `logging`, `signal`). They shadow the standard library.
- Do not edit anything in `.my/` unless the user asks.
- Do not create directories or files unless the project actually needs them.
