#!/usr/bin/env bash
# ==============================================================================
# PLUS-ULTRA Linux Desktop Installer
# Installs standalone binary to ~/.local/bin and creates an XDG .desktop launcher
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DIST_EXE="$PROJECT_ROOT/dist/plus-ultra"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"

echo "=========================================="
echo "  PLUS-ULTRA Linux Desktop Installer      "
echo "=========================================="

# 1. Build binary if missing
if [ ! -f "$DIST_EXE" ]; then
    echo "==> Executable not found at dist/plus-ultra. Building via PyInstaller..."
    cd "$PROJECT_ROOT"
    uv run pyinstaller plus-ultra.spec --noconfirm
fi

# 2. Install executable
mkdir -p "$BIN_DIR"
cp "$DIST_EXE" "$BIN_DIR/plus-ultra"
chmod +x "$BIN_DIR/plus-ultra"
echo "[OK] Installed executable to $BIN_DIR/plus-ultra"

# 3. Install icon
mkdir -p "$ICON_DIR"
if [ -f "$PROJECT_ROOT/src/plus_ultra/resources/icons/fallback.png" ]; then
    cp "$PROJECT_ROOT/src/plus_ultra/resources/icons/fallback.png" "$ICON_DIR/plus-ultra.png"
    echo "[OK] Installed application icon to $ICON_DIR/plus-ultra.png"
fi

# 4. Create XDG .desktop application launcher
mkdir -p "$DESKTOP_DIR"
cat <<EOF > "$DESKTOP_DIR/plus-ultra.desktop"
[Desktop Entry]
Type=Application
Version=1.0
Name=PLUS-ULTRA
Comment=Floating desktop assistant
Exec=$BIN_DIR/plus-ultra
Icon=plus-ultra
Terminal=false
Categories=Utility;ProjectManagement;
StartupNotify=false
EOF
chmod +x "$DESKTOP_DIR/plus-ultra.desktop"
echo "[OK] Created application launcher at $DESKTOP_DIR/plus-ultra.desktop"

echo ""
echo "Installation complete!"
echo "You can launch PLUS-ULTRA from your application menu or run 'plus-ultra'."
echo "Persistent storage:"
echo "  Database: ~/.local/share/plus-ultra/plus-ultra.sqlite3"
echo "  Settings: ~/.config/plus-ultra/user-settings.json"
