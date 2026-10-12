
---
name: finish-project-security
description: Run the final Gitleaks secret scan when the user explicitly says they are finishing a project or asks for a final security check. Scans current repository files and Git history. Never run automatically on ordinary edits or task completion.
---

# Finish Project Security Check

Only run this check when the user explicitly invokes `/finish-project-security` or directly requests the final security scan.

## Procedure

1. Confirm the workspace root is a Git repository.
2. Run the scanner from the repository root:
   `bash .agents/skills/finish-project-security/scripts/scan-leaked-credentials.sh`

3. Wait for the command to finish and report its actual result.
4. If the exit code is 0, report that both scans completed without detected secrets. Do not claim this proves that no secrets exist.
5. If the exit code is 1, report that potential secrets were detected. Show the reported file paths and line numbers when available, but never print secret values.
6. If the exit code is 2, 124, or another nonzero error, report the check as incomplete or failed. Never describe an incomplete scan as clean.
7. Do not automatically delete files, rewrite Git history, or revoke credentials. Ask before making consequential changes.
8. Do not create unredacted scan reports or paste secret values into chat.
9. Do not continue to publishing or deployment when findings remain unresolved; tell the user what needs review.
