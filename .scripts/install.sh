#!/usr/bin/env bash
# ==============================================================================
# PLUS-ULTRA Linux Desktop Installer (Interactive TUI & Automated CLI)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

if command -v uv >/dev/null 2>&1; then
    exec uv run python "$SCRIPT_DIR/install.py" "$@"
elif command -v python3 >/dev/null 2>&1; then
    exec python3 "$SCRIPT_DIR/install.py" "$@"
else
    echo "Error: Neither uv nor python3 found in PATH." >&2
    exit 1
fi
