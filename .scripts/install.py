"""Cross-platform installation and desktop setup utility for PLUS-ULTRA.

Supports:
- Windows: Installs to %LOCALAPPDATA%\\Programs\\plus-ultra with Start Menu & Desktop shortcuts.
- Linux: Installs to ~/.local/bin with XDG .desktop application launcher and icons.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src" / "plus_ultra"
RESOURCES_DIR = SRC_DIR / "resources"


def build_binary_if_missing(exe_path: Path) -> None:
    """Build standalone executable via PyInstaller if not yet compiled."""
    if exe_path.is_file():
        return

    print("==> Standalone executable not found in dist/. Building via PyInstaller...")
    spec_file = PROJECT_ROOT / "plus-ultra.spec"
    cmd = ["uv", "run", "pyinstaller", str(spec_file), "--noconfirm"]
    try:
        subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)
        print("==> Build completed successfully.")
    except Exception as exc:
        print(f"Error during PyInstaller build: {exc}", file=sys.stderr)
        sys.exit(1)


def install_windows() -> None:
    """Install application on Windows for current user."""
    dist_exe = PROJECT_ROOT / "dist" / "plus-ultra.exe"
    build_binary_if_missing(dist_exe)

    local_appdata = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    install_dir = local_appdata / "Programs" / "plus-ultra"
    install_dir.mkdir(parents=True, exist_ok=True)

    target_exe = install_dir / "plus-ultra.exe"
    shutil.copy2(dist_exe, target_exe)
    print(f"[OK] Installed executable: {target_exe}")

    icon_src = RESOURCES_DIR / "icons" / "app.ico"
    target_icon = install_dir / "app.ico"
    if icon_src.is_file():
        shutil.copy2(icon_src, target_icon)

    # Create Windows Shortcuts via PowerShell / WScript.Shell
    ps_cmd = f"""
    $WshShell = New-Object -ComObject WScript.Shell;
    $Desktop = [Environment]::GetFolderPath('Desktop');
    $StartMenu = [Environment]::GetFolderPath('Programs');
    
    $s1 = $WshShell.CreateShortcut((Join-Path $Desktop 'PLUS-ULTRA.lnk'));
    $s1.TargetPath = '{target_exe}';
    $s1.WorkingDirectory = '{install_dir}';
    $s1.IconLocation = '{target_icon}';
    $s1.Save();
    
    $s2 = $WshShell.CreateShortcut((Join-Path $StartMenu 'PLUS-ULTRA.lnk'));
    $s2.TargetPath = '{target_exe}';
    $s2.WorkingDirectory = '{install_dir}';
    $s2.IconLocation = '{target_icon}';
    $s2.Save();
    """
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
            check=False,
            capture_output=True,
        )
        print("[OK] Created Desktop and Start Menu shortcuts.")
    except Exception as exc:
        print(f"[!] Note: Could not register shortcuts via PowerShell: {exc}")

    print("\nPLUS-ULTRA is ready to run on Windows!")
    print(f"  Executable: {target_exe}")
    print(f"  Persistent Database: {local_appdata}\\plus-ultra\\plus-ultra.sqlite3")
    print(f"  Persistent Settings: {Path.home() / 'AppData' / 'Roaming' / 'plus-ultra' / 'user-settings.json'}")


def install_linux() -> None:
    """Install application on Linux following FreeDesktop XDG specifications."""
    dist_exe = PROJECT_ROOT / "dist" / "plus-ultra"
    build_binary_if_missing(dist_exe)

    # 1. Install binary to ~/.local/bin
    bin_dir = Path.home() / ".local" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    target_exe = bin_dir / "plus-ultra"
    shutil.copy2(dist_exe, target_exe)
    target_exe.chmod(0o755)
    print(f"[OK] Installed executable: {target_exe}")

    # 2. Install icon to ~/.local/share/icons/hicolor/256x256/apps/
    icon_dir = Path.home() / ".local" / "share" / "icons" / "hicolor" / "256x256" / "apps"
    icon_dir.mkdir(parents=True, exist_ok=True)
    icon_src = RESOURCES_DIR / "icons" / "fallback.png"
    target_icon = icon_dir / "plus-ultra.png"
    if icon_src.is_file():
        shutil.copy2(icon_src, target_icon)
        print(f"[OK] Installed application icon: {target_icon}")

    # 3. Create XDG .desktop launcher
    desktop_dir = Path.home() / ".local" / "share" / "applications"
    desktop_dir.mkdir(parents=True, exist_ok=True)
    desktop_file = desktop_dir / "plus-ultra.desktop"

    entry = f"""[Desktop Entry]
Type=Application
Version=1.0
Name=PLUS-ULTRA
Comment=Floating desktop assistant
Exec={target_exe}
Icon=plus-ultra
Terminal=false
Categories=Utility;ProjectManagement;
StartupNotify=false
"""
    desktop_file.write_text(entry, encoding="utf-8")
    desktop_file.chmod(0o755)
    print(f"[OK] Created application launcher: {desktop_file}")

    print("\nPLUS-ULTRA is ready to run on Linux!")
    print(f"  Executable: {target_exe}")
    print(f"  Persistent Database: ~/.local/share/plus-ultra/plus-ultra.sqlite3")
    print(f"  Persistent Settings: ~/.config/plus-ultra/user-settings.json")


def main() -> None:
    print("=" * 50)
    print("  PLUS-ULTRA Cross-Platform Production Installer  ")
    print("=" * 50)

    if sys.platform == "win32":
        install_windows()
    elif sys.platform.startswith("linux"):
        install_linux()
    else:
        print(f"Unsupported operating system platform: {sys.platform}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
