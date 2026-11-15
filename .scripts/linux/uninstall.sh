#!/usr/bin/env bash
# ==============================================================================
# PLUS-ULTRA Linux Desktop Uninstaller (Launcher)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_ROOT="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$SCRIPTS_ROOT")"

cd "$PROJECT_ROOT"

if command -v uv >/dev/null 2>&1; then
    exec uv run python "$SCRIPTS_ROOT/uninstall.py" "$@"
elif command -v python3 >/dev/null 2>&1; then
    exec python3 "$SCRIPTS_ROOT/uninstall.py" "$@"
else
    echo "Error: Neither uv nor python3 found in PATH." >&2
    exit 1
fi

