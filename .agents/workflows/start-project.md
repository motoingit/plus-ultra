---
description: Start a development session by understanding the repository, instructions, Git status, and current priorities
---

# Start Project

Use this workflow when I explicitly invoke `/start-project`.

## Step 1: Understand the repository

- Identify the project root, language, framework, package manager, and overall structure.
- Read the root `GEMINI.md` or `AGENTS.md`, applicable rules, and relevant skill instructions.
- Inspect the README and project-specific setup documentation if present.
- Identify the test, lint, build, and formatting commands from the repository's configuration.

## Step 2: Check Git status

- Run `git status --short --branch`.
- Identify modified, staged, untracked, and ignored files where relevant.
- Never discard, overwrite, reset, or clean existing user changes.
- Do not print credentials or sensitive file contents.

## Step 3: Understand the current state

- Identify the apparent current state of the project.
- Check relevant recent commits when useful.
- Identify incomplete work, failing tests, TODOs, or obvious blockers relevant to the requested task.
- Distinguish confirmed facts from assumptions.

## Step 4: Ask for the task

If I have not yet explained what I want to work on, ask me for the goal.

If my task is already clear, do not ask me to repeat it.

## Step 5: Report readiness

Summarize:
- Project type and architecture.
- Git working-tree status.
- Relevant test and build commands.
- Important blockers or risks.
- Your understanding of the requested task.

Do not modify application files, install packages, or make architectural changes just to inspect the project. Wait for my task if it is not yet specified.