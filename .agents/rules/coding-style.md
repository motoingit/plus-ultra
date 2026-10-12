---
trigger: model_decision
description: "Apply when writing, editing, or reviewing any Python code: naming, PEP 8, type annotations, ruff, logging, and modular design."
---

# Coding Style

## Naming Conventions

- Functions, methods, variables, and modules: use `snake_case`.
- Constants: use `UPPER_SNAKE_CASE`, such as `REMINDER_POLL_MS`.
- Classes: use `PascalCase`, such as `TaskService`.

## Guidelines

- Follow PEP 8 consistently. `ruff check` and `ruff format` are the arbiters; their configuration lives in `pyproject.toml`.
- Prefer focused modules and explicit interfaces.
- Use type annotations for public functions and meaningful data structures.
- Use `pathlib.Path` for paths and the `logging` module instead of `print` (except CLI output).
- Keep I/O, subprocess calls, and platform-specific behavior at clear boundaries.
- Comments explain why, not what. Add a short comment wherever an OS or DBMS concept is being applied (for example, why a transaction or a lock is used).
- Preserve existing conventions when modifying code unless asked to change them.
- Avoid unnecessary renaming that could break compatibility.
