---
description: Finish a development session by reviewing changes, running appropriate validation, scanning for secrets, and reporting release readiness.
---

# Finish Project

Use this workflow only when I explicitly invoke `/finish-project`.

## Step 1: Review the working tree

- Run `git status --short --branch`.
- Review staged and unstaged changes using safe, read-only Git commands.
- Identify untracked files that belong to the project.
- Never discard, reset, clean, or overwrite my existing work.
- Do not stage, commit, push, publish, or deploy anything without my explicit permission.

## Step 2: Review the changes

- Check for obvious bugs, unfinished code, debugging statements, accidental generated files, and unrelated modifications.
- Check that secrets, credentials, private keys, local configuration, and sensitive data have not been added.
- Do not print secret values in the chat.
- Report concerns and distinguish confirmed problems from possible issues.

## Step 3: Run project validation

- Discover the appropriate test, lint, type-check, and build commands from the project documentation and configuration.
- Run relevant checks that can reasonably finish within the available time.
- Do not install dependencies or make destructive changes without permission.
- Report each check as passed, failed, skipped, or incomplete.
- Never claim that a check passed if it was not run successfully.

## Step 4: use the skill `.agents/skills/finish-project-security`

## Step 5: Report the final status

Summarize:
- Changes reviewed.
- Tests, lint, and build results.
- Secret-scan result.
- Remaining bugs, risks, or incomplete checks.
- Files that may need attention before release.

If secrets are detected or important validation fails, clearly state that the project is not ready for release.

## Step 6: Wait for permission

Do not commit, push, publish, deploy, delete files, or make consequential fixes automatically.

Explain the recommended next steps and wait for my approval before performing those actions.