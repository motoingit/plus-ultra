"""Cross-platform interactive TUI installer for PLUS-ULTRA (Linux & Win11).

Provides:
- Interactive TUI menu with arrow-key navigation and spacebar toggles.
- Customization: Autostart on OS login, theme selection, shortcuts, demo data.
- Non-interactive fallback for automated scripting and CI.
- Builds PyInstaller binary if missing and installs to standard paths.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src" / "plus_ultra"
RESOURCES_DIR = SRC_DIR / "resources"

# ANSI Terminal Styling
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"
INVERT = "\033[7m"
CLEAR = "\033[2J\033[H"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"

THEMES = [
    ("cyan", "Cyber Cyan (Default)"),
    ("emerald", "Emerald Matrix"),
    ("purple", "Neon Violet"),
    ("amber", "Sunset Amber"),
]

MENU_ITEMS = [
    ("Launch on System Startup (OS Login)", "autostart"),
    ("Create Desktop & App Menu Shortcuts", "shortcuts"),
    ("Start Minimized to System Tray", "start_minimized"),
    ("Pre-populate Workspace with Demo Data", "seed_demo"),
]


def enable_windows_ansi() -> None:
    """Enable ANSI escape sequence interpretation on Windows consoles."""
    if sys.platform != "win32":
        return
    with contextlib.suppress(Exception):
        import ctypes

        k32 = ctypes.windll.kernel32
        h_out = k32.GetStdHandle(-11)
        mode = ctypes.c_ulong()
        k32.GetConsoleMode(h_out, ctypes.byref(mode))
        mode.value |= 0x0004
        k32.SetConsoleMode(h_out, mode)


def read_key() -> str:
    """Read a single interactive keystroke cross-platform."""
    if sys.platform == "win32":
        import msvcrt

        ch = msvcrt.getch()
        if ch in (b"\x00", b"\xe0"):
            return {
                b"H": "UP", b"P": "DOWN", b"M": "RIGHT", b"K": "LEFT",
            }.get(msvcrt.getch(), "")
        key_map = {
            b"\r": "ENTER", b"\n": "ENTER", b" ": "SPACE",
            b"\x1b": "QUIT", b"q": "QUIT", b"Q": "QUIT", b"\x03": "QUIT",
            b"k": "UP", b"j": "DOWN", b"h": "LEFT", b"l": "RIGHT",
        }
        return key_map.get(ch, ch.decode("utf-8", errors="ignore"))

    import select
    import termios
    import tty

    fd = sys.stdin.fileno()
    old_term = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd, termios.TCSANOW)
        raw = os.read(fd, 32)
        if raw == b"\x1b":
            r, _, _ = select.select([fd], [], [], 0.05)
            if r:
                raw += os.read(fd, 32)
        if raw.startswith((b"\x1b[A", b"\x1bOA")):
            return "UP"
        if raw.startswith((b"\x1b[B", b"\x1bOB")):
            return "DOWN"
        if raw.startswith((b"\x1b[C", b"\x1bOC")):
            return "RIGHT"
        if raw.startswith((b"\x1b[D", b"\x1bOD")):
            return "LEFT"
        key_map = {
            b"\r": "ENTER", b"\n": "ENTER", b" ": "SPACE",
            b"\x1b": "QUIT", b"q": "QUIT", b"Q": "QUIT",
            b"\x03": "QUIT", b"\x04": "QUIT",
            b"k": "UP", b"K": "UP", b"j": "DOWN", b"J": "DOWN",
            b"h": "LEFT", b"H": "LEFT", b"l": "RIGHT", b"L": "RIGHT",
        }
        return key_map.get(raw, raw.decode("utf-8", errors="ignore"))
    finally:
        termios.tcsetattr(fd, termios.TCSANOW, old_term)


class InstallOptions:
    """User installation preferences."""

    def __init__(self) -> None:
        self.autostart: bool = True
        self.shortcuts: bool = True
        self.start_minimized: bool = False
        self.seed_demo: bool = True
        self.theme_idx: int = 0

    @property
    def theme_key(self) -> str:
        return THEMES[self.theme_idx][0]

    @property
    def theme_label(self) -> str:
        return THEMES[self.theme_idx][1]


def run_interactive_menu(opt: InstallOptions) -> bool:
    """Display interactive TUI menu using arrow keys and checkboxes."""
    enable_windows_ansi()
    sel_idx = 0
    total_items = len(MENU_ITEMS) + 3

    sys.stdout.write(HIDE_CURSOR)
    sys.stdout.flush()

    border_top = f"{CYAN}{BOLD}╔" + "═" * 46 + f"╗{RESET}"
    border_bot = f"{CYAN}{BOLD}╚" + "═" * 46 + f"╝{RESET}"
    div = f"{DIM}" + "─" * 48 + f"{RESET}"

    try:
        while True:
            os_name = "Win11" if sys.platform == "win32" else "Linux"
            t1 = "PLUS-ULTRA Desktop Assistant"
            t2 = f"Setup & Customizer ({os_name})"
            out = [
                CLEAR,
                border_top,
                f"{CYAN}{BOLD}║{t1:^46}║{RESET}",
                f"{CYAN}{BOLD}║{t2:^46}║{RESET}",
                border_bot + "\n",
                f"{DIM}[↑/↓] move, [Space] toggle, [Enter] select:{RESET}",
                "",
            ]

            for i, (label, attr) in enumerate(MENU_ITEMS):
                val = getattr(opt, attr)
                ptr = f"{CYAN}❯{RESET}" if sel_idx == i else " "
                box = f"{GREEN}[x]{RESET}" if val else "[ ]"
                txt = f"{BOLD}{label}{RESET}" if sel_idx == i else label
                out.append(f" {ptr} {box} {txt}")

            t_ptr = f"{CYAN}❯{RESET}" if sel_idx == 4 else " "
            t_col = f"{CYAN}{opt.theme_label}{RESET}"
            t_txt = f"{BOLD}Theme:{RESET} < {t_col} > {DIM}(←/→){RESET}"
            out.append(f" {t_ptr}  *  {t_txt}\n")

            out.append(div)
            b1 = f"{GREEN}[>> Install PLUS-ULTRA <<]{RESET}"
            b2 = f"{YELLOW}[   Cancel & Exit      ]{RESET}"
            p1 = f"{CYAN}❯{RESET} {INVERT}" if sel_idx == 5 else "  "
            s1 = f"{RESET}" if sel_idx == 5 else ""
            p2 = f"{CYAN}❯{RESET} {INVERT}" if sel_idx == 6 else "  "
            s2 = f"{RESET}" if sel_idx == 6 else ""

            out.append(f" {p1}{b1}{s1}")
            out.append(f" {p2}{b2}{s2}\n")
            out.append(
                f"{DIM}[↑/↓/j/k] Move  [Space] Toggle  "
                f"[Enter] Select  [q] Quit{RESET}"
            )

            sys.stdout.write("\n".join(out) + "\n")
            sys.stdout.flush()

            key = read_key()
            if key == "UP":
                sel_idx = (sel_idx - 1) % total_items
            elif key == "DOWN":
                sel_idx = (sel_idx + 1) % total_items
            elif key in ("LEFT", "h") and sel_idx == 4:
                opt.theme_idx = (opt.theme_idx - 1) % len(THEMES)
            elif key in ("RIGHT", "l") and sel_idx == 4:
                opt.theme_idx = (opt.theme_idx + 1) % len(THEMES)
            elif key == "ENTER" and sel_idx == 5:
                return True
            elif key == "ENTER" and sel_idx == 6:
                return False
            elif key in ("SPACE", "ENTER"):
                if 0 <= sel_idx < len(MENU_ITEMS):
                    attr = MENU_ITEMS[sel_idx][1]
                    setattr(opt, attr, not getattr(opt, attr))
                elif sel_idx == 4:
                    opt.theme_idx = (opt.theme_idx + 1) % len(THEMES)
            elif key == "QUIT":
                return False
    finally:
        sys.stdout.write(SHOW_CURSOR)
        sys.stdout.flush()


def build_binary_if_missing(exe_path: Path) -> None:
    """Build standalone executable via PyInstaller if not yet compiled."""
    if exe_path.is_file():
        return
    print("==> Standalone executable not found in dist/. Building binary...")
    spec_file = PROJECT_ROOT / "plus-ultra.spec"
    with contextlib.suppress(Exception):
        subprocess.run(
            ["uv", "run", "pyinstaller", str(spec_file), "--noconfirm"],
            cwd=PROJECT_ROOT, check=True,
        )


def save_user_preferences(cfg_dir: Path, opt: InstallOptions) -> None:
    """Persist chosen installer preferences to user-settings.json."""
    cfg_dir.mkdir(parents=True, exist_ok=True)
    settings_file = cfg_dir / "user-settings.json"
    data: dict[str, object] = {
        "settings_version": 2,
        "start_with_system": opt.autostart,
        "start_minimized": opt.start_minimized,
        "theme": opt.theme_key,
    }
    if settings_file.is_file():
        with contextlib.suppress(Exception):
            existing = json.loads(settings_file.read_text(encoding="utf-8"))
            if isinstance(existing, dict):
                existing.update(data)
                data = existing
    settings_file.write_text(
        json.dumps(data, indent=2) + "\n", encoding="utf-8"
    )
    with contextlib.suppress(OSError):
        settings_file.chmod(0o600)


def setup_database(db_path: Path, seed_demo: bool) -> None:
    """Initialize SQLite schema and conditionally seed demo data."""
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
    with contextlib.suppress(Exception):
        from plus_ultra.database import (
            get_connection,
            init_db,
            seed_demo_workspace_data,
            wipe_database,
        )

        db_path.parent.mkdir(parents=True, exist_ok=True)
        if not seed_demo and db_path.is_file():
            conn = get_connection(db_path)
            try:
                wipe_database(conn)
            finally:
                conn.close()

        init_db(db_path)
        if seed_demo:
            conn = get_connection(db_path)
            try:
                seed_demo_workspace_data(conn)
            finally:
                conn.close()


def _write_desktop_file(
    path: Path, cmd: str, autostart: bool = False
) -> None:
    """Write standard FreeDesktop .desktop application launcher."""
    path.parent.mkdir(parents=True, exist_ok=True)
    extra = (
        "X-GNOME-Autostart-enabled=true\n"
        if autostart
        else "Categories=Utility;ProjectManagement;\nStartupNotify=false\n"
    )
    content = (
        "[Desktop Entry]\nType=Application\nVersion=1.0\nName=PLUS-ULTRA\n"
        f"Comment=Floating desktop assistant\nExec={cmd}\n"
        f"Icon=plus-ultra\nTerminal=false\n{extra}"
    )
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


def install_linux(opt: InstallOptions) -> None:
    """Install application on Linux with XDG integration."""
    dist_exe = PROJECT_ROOT / "dist" / "plus-ultra"
    build_binary_if_missing(dist_exe)

    # 1. Install binary
    bin_dir = Path.home() / ".local" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    target_exe = bin_dir / "plus-ultra"
    if dist_exe.is_file():
        shutil.copy2(dist_exe, target_exe)
        target_exe.chmod(0o755)
        print(f"[OK] Installed executable: {target_exe}")
        exec_cmd = str(target_exe)
    else:
        exec_cmd = f"{sys.executable} -m plus_ultra.main"

    # 2. Install icon
    icon_dir = (
        Path.home() / ".local" / "share" / "icons"
        / "hicolor" / "256x256" / "apps"
    )
    icon_dir.mkdir(parents=True, exist_ok=True)
    target_icon = icon_dir / "plus-ultra.png"
    icon_src = RESOURCES_DIR / "icons" / "fallback.png"
    if icon_src.is_file():
        shutil.copy2(icon_src, target_icon)
        print(f"[OK] Installed icon: {target_icon}")

    # 3. Desktop shortcut / launcher
    if opt.shortcuts:
        app_file = (
            Path.home() / ".local" / "share" / "applications"
            / "plus-ultra.desktop"
        )
        _write_desktop_file(app_file, exec_cmd, autostart=False)
        print(f"[OK] Created application launcher: {app_file}")

    # 4. Autostart
    auto_file = (
        Path.home() / ".config" / "autostart" / "plus-ultra.desktop"
    )
    if opt.autostart:
        _write_desktop_file(auto_file, exec_cmd, autostart=True)
        print(f"[OK] Enabled autostart: {auto_file}")
    elif auto_file.is_file():
        auto_file.unlink()

    # 5. Preferences & Database
    cfg_dir = Path.home() / ".config" / "plus-ultra"
    save_user_preferences(cfg_dir, opt)
    db_path = (
        Path.home() / ".local" / "share" / "plus-ultra" / "plus-ultra.sqlite3"
    )
    setup_database(db_path, opt.seed_demo)

    print(f"\n{GREEN}{BOLD}Installation completed on Linux!{RESET}")
    print(f"  Theme: {opt.theme_label}")
    print(f"  Autostart on Login: {'Yes' if opt.autostart else 'No'}")
    print(f"  Executable: {target_exe}")
    print("  Launch with: plus-ultra (or via your application menu)")


def install_windows(opt: InstallOptions) -> None:
    """Install application on Windows 11 with shortcuts and autostart."""
    dist_exe = PROJECT_ROOT / "dist" / "plus-ultra.exe"
    build_binary_if_missing(dist_exe)

    local_appdata = Path(
        os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")
    )
    install_dir = local_appdata / "Programs" / "plus-ultra"
    install_dir.mkdir(parents=True, exist_ok=True)

    target_exe = install_dir / "plus-ultra.exe"
    if dist_exe.is_file():
        shutil.copy2(dist_exe, target_exe)
        print(f"[OK] Installed executable: {target_exe}")

    target_icon = install_dir / "app.ico"
    icon_src = RESOURCES_DIR / "icons" / "app.ico"
    if icon_src.is_file():
        shutil.copy2(icon_src, target_icon)

    # Shortcuts
    if opt.shortcuts:
        ps_cmd = (
            "$Wsh = New-Object -ComObject WScript.Shell;\n"
            "$d = [Environment]::GetFolderPath('Desktop');\n"
            "$m = [Environment]::GetFolderPath('Programs');\n"
            f"$s1 = $Wsh.CreateShortcut((Join-Path $d 'PLUS-ULTRA.lnk'));\n"
            f"$s1.TargetPath = '{target_exe}';\n"
            f"$s1.WorkingDirectory = '{install_dir}';\n"
            f"$s1.IconLocation = '{target_icon}';\n$s1.Save();\n"
            f"$s2 = $Wsh.CreateShortcut((Join-Path $m 'PLUS-ULTRA.lnk'));\n"
            f"$s2.TargetPath = '{target_exe}';\n"
            f"$s2.WorkingDirectory = '{install_dir}';\n"
            f"$s2.IconLocation = '{target_icon}';\n$s2.Save();"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            check=False,
            capture_output=True,
        )
        print("[OK] Created Desktop and Start Menu shortcuts.")

    # Autostart via Registry
    with contextlib.suppress(Exception):
        import winreg

        reg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        if opt.autostart:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_SET_VALUE
            ) as key:
                winreg.SetValueEx(
                    key, "PLUS-ULTRA", 0, winreg.REG_SZ, f'"{target_exe}"'
                )
            print("[OK] Registered Windows Startup Run key.")
        else:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_SET_VALUE
            ) as key:
                winreg.DeleteValue(key, "PLUS-ULTRA")

    # Preferences & Database
    roaming = Path(
        os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")
    )
    save_user_preferences(roaming / "plus-ultra", opt)
    db_p = local_appdata / "plus-ultra" / "plus-ultra.sqlite3"
    setup_database(db_p, opt.seed_demo)

    print(f"\n{GREEN}{BOLD}Installation completed on Windows 11!{RESET}")
    print(f"  Theme: {opt.theme_label}")
    print(f"  Autostart on Login: {'Yes' if opt.autostart else 'No'}")
    print(f"  Executable: {target_exe}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="PLUS-ULTRA Desktop Assistant Installer"
    )
    parser.add_argument(
        "--non-interactive", "-y", action="store_true",
        help="Run non-interactively with defaults",
    )
    parser.add_argument(
        "--no-autostart", action="store_true",
        help="Disable launch on OS startup",
    )
    parser.add_argument(
        "--theme", choices=["cyan", "emerald", "purple", "amber"],
        default="cyan", help="Theme palette accent",
    )
    parser.add_argument(
        "--no-demo", action="store_true",
        help="Do not seed demo workspace data",
    )
    parser.add_argument(
        "--minimized", action="store_true",
        help="Start minimized to tray",
    )
    args = parser.parse_args()

    opt = InstallOptions()
    if args.no_autostart:
        opt.autostart = False
    if args.no_demo:
        opt.seed_demo = False
    if args.minimized:
        opt.start_minimized = True
    theme_keys = [t[0] for t in THEMES]
    if args.theme in theme_keys:
        opt.theme_idx = theme_keys.index(args.theme)

    is_interactive = (
        sys.stdin.isatty() and sys.stdout.isatty() and not args.non_interactive
    )

    if is_interactive:
        confirmed = run_interactive_menu(opt)
        if not confirmed:
            print("\nInstallation cancelled by user.")
            sys.exit(0)
    else:
        print("==> Running installation with configured options.")

    print(f"\nInstalling PLUS-ULTRA with theme '{opt.theme_label}'...")
    if sys.platform == "win32":
        install_windows(opt)
    else:
        install_linux(opt)


if __name__ == "__main__":
    main()
