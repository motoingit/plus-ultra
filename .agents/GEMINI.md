
# Project Description

- `PLUS-ULTRA` is our project build to give a user-facing floating desktop assistant that starts with the user's
  session, displays a compact top-center visual presence, manages reminders and
  recurring scripts, manage processes in os (OS-CONCEPT), File management(DBMS-CONCEPT).

# Project Rules & Guidelines

- **Privacy Constraint**: Never read, search, list, or modify any files or directories inside `.my/`. This folder is strictly reserved for the user.
- **Initialization and Techstack**: Load [init-and-techstack.md](./rules/init-and-techstack.md) before the first implementation task and never scan this file after that.
- **Decision Making**: Always consult [ask-before-assuming.md](./rules/ask-before-assuming.md) when multiple technical approaches or designs are viable.
- **Coding Conventions**: Follow [coding-style.md](./rules/coding-style.md) for naming conventions, type hints, and PEP 8 compliance.
- **Project Structure Idea**: Follow [genral-project-structure.md](./rules/genral-project-structure.md) as the codebase expands.

# Python and Linux conventions

- Target the Linux desktop and use Python 3.12+ unless the project explicitly changes
  its support policy.
- Use `uv` for environment creation, dependency management, locking, and running
  project commands. Keep dependency declarations in `pyproject.toml` and commit
  `uv.lock` once the project is initialized.
- Prefer the standard library for platform-neutral code. Isolate Linux-specific
  integration behind small, testable adapters.
- Keep long-running work off the UI thread and make shutdown/cancellation explicit.

# Validation

- Run targeted tests first, then the project test suite when practical.
- Before considering a change complete, run the configured formatter, linter, and
  type checker if they exist.
- Document manual Linux desktop checks for startup behavior, display placement,
  notifications, permissions, and graceful shutdown.

# Documentation

After every phase, update the relevant `docs/*.md` files as follows:
- Especially `README.md`, to reflect implemented changes on top apis, database schema and 3 layer achitecture  details
- Keep updating `api.md` with new API's and modification.
- Keep updating `progress-log.md` with what is going to implemented next, what was implemented in this phase, what were the issues and its status, and Important points.
Note: Keep documentation concise, uniform and accurate.