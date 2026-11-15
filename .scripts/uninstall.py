"""Cross-platform uninstallation utility for PLUS-ULTRA (Linux & Win11).

Provides:
- Interactive TUI menu to select components to remove.
- Option to purge or preserve user database, configuration, and logs.
- Removes binary, desktop launchers, autostart entries, and icons.
- Non-interactive CLI fallback with --purge flag.
"""

from __future__ import annotations

import argparse
import contextlib
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

# ANSI Terminal Styling
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"
INVERT = "\033[7m"
CLEAR = "\033[2J\033[H"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"

MENU_ITEMS = [
    ("Remove Application Executable & Icons", "remove_binary"),
    ("Remove Desktop & App Menu Shortcuts", "remove_shortcuts"),
    ("Remove Autostart on OS Login", "remove_autostart"),
    ("Purge User Data (Database, Settings, Logs)", "purge_data"),
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
                b"H": "UP",
                b"P": "DOWN",
                b"M": "RIGHT",
                b"K": "LEFT",
            }.get(msvcrt.getch(), "")
        key_map = {
            b"\r": "ENTER",
            b"\n": "ENTER",
            b" ": "SPACE",
            b"\x1b": "QUIT",
            b"q": "QUIT",
            b"Q": "QUIT",
            b"\x03": "QUIT",
            b"k": "UP",
            b"j": "DOWN",
            b"h": "LEFT",
            b"l": "RIGHT",
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
            b"\r": "ENTER",
            b"\n": "ENTER",
            b" ": "SPACE",
            b"\x1b": "QUIT",
            b"q": "QUIT",
            b"Q": "QUIT",
            b"\x03": "QUIT",
            b"\x04": "QUIT",
            b"k": "UP",
            b"K": "UP",
            b"j": "DOWN",
            b"J": "DOWN",
            b"h": "LEFT",
            b"H": "LEFT",
            b"l": "RIGHT",
            b"L": "RIGHT",
        }
        return key_map.get(raw, raw.decode("utf-8", errors="ignore"))
    finally:
        termios.tcsetattr(fd, termios.TCSANOW, old_term)


class UninstallOptions:
    """User uninstallation preferences."""

    def __init__(self) -> None:
        self.remove_binary: bool = True
        self.remove_shortcuts: bool = True
        self.remove_autostart: bool = True
        self.purge_data: bool = False


def run_interactive_menu(opt: UninstallOptions) -> bool:
    """Display interactive TUI menu for uninstallation."""
    enable_windows_ansi()
    sel_idx = 0
    total_items = len(MENU_ITEMS) + 2

    sys.stdout.write(HIDE_CURSOR)
    sys.stdout.flush()

    border_top = f"{RED}{BOLD}╔" + "═" * 46 + f"╗{RESET}"
    border_bot = f"{RED}{BOLD}╚" + "═" * 46 + f"╝{RESET}"
    div = f"{DIM}" + "─" * 48 + f"{RESET}"

    try:
        while True:
            os_name = "Win11" if sys.platform == "win32" else "Linux"
            t1 = "PLUS-ULTRA Desktop Assistant"
            t2 = f"Uninstallation & Cleanup ({os_name})"
            out = [
                CLEAR,
                border_top,
                f"{RED}{BOLD}║{t1:^46}║{RESET}",
                f"{RED}{BOLD}║{t2:^46}║{RESET}",
                border_bot + "\n",
                f"{DIM}[↑/↓] move, [Space] toggle, [Enter] select:{RESET}",
                "",
            ]

            for i, (label, attr) in enumerate(MENU_ITEMS):
                val = getattr(opt, attr)
                ptr = f"{CYAN}❯{RESET}" if sel_idx == i else " "
                if attr == "purge_data":
                    box = f"{RED}[x]{RESET}" if val else "[ ]"
                    col = f"{RED}{BOLD}" if val else ""
                    txt = f"{col}{label}{RESET}"
                else:
                    box = f"{GREEN}[x]{RESET}" if val else "[ ]"
                    txt = f"{BOLD}{label}{RESET}" if sel_idx == i else label
                out.append(f" {ptr} {box} {txt}")

            out.append("\n" + div)
            b1 = f"{RED}[>> Complete Uninstallation <<]{RESET}"
            b2 = f"{YELLOW}[   Cancel & Keep Installed  ]{RESET}"
            p1 = f"{CYAN}❯{RESET} {INVERT}" if sel_idx == 4 else "  "
            s1 = f"{RESET}" if sel_idx == 4 else ""
            p2 = f"{CYAN}❯{RESET} {INVERT}" if sel_idx == 5 else "  "
            s2 = f"{RESET}" if sel_idx == 5 else ""

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
            elif key == "ENTER" and sel_idx == 4:
                return True
            elif key == "ENTER" and sel_idx == 5:
                return False
            elif key in ("SPACE", "ENTER"):
                if 0 <= sel_idx < len(MENU_ITEMS):
                    attr = MENU_ITEMS[sel_idx][1]
                    setattr(opt, attr, not getattr(opt, attr))
            elif key == "QUIT":
                return False
    finally:
        sys.stdout.write(SHOW_CURSOR)
        sys.stdout.flush()


def _remove_path(path: Path, desc: str) -> None:
    """Safely remove a file or directory tree with logging."""
    if not path.exists():
        return
    try:
        if path.is_file() or path.is_symlink():
            path.unlink()
            print(f"[OK] Removed {desc}: {path}")
        elif path.is_dir():
            shutil.rmtree(path)
            print(f"[OK] Removed {desc} directory: {path}")
    except OSError as exc:
        print(f"[WARN] Could not remove {path}: {exc}", file=sys.stderr)


def stop_running_instances() -> None:
    """Terminate any running PLUS-ULTRA processes before uninstalling."""
    if sys.platform == "win32":
        with contextlib.suppress(Exception):
            subprocess.run(
                ["taskkill", "/IM", "plus-ultra.exe", "/T", "/F"],
                check=False,
                capture_output=True,
            )
            print("[OK] Stopped running PLUS-ULTRA processes.")
        return

    pids: list[int] = []
    lock_file = (
        Path.home() / ".local" / "state" / "plus-ultra" / "plus-ultra.lock"
    )
    if lock_file.is_file():
        with contextlib.suppress(Exception):
            raw = lock_file.read_text(encoding="utf-8").strip()
            if raw.isdigit() and int(raw) != os.getpid():
                pids.append(int(raw))

    with contextlib.suppress(Exception):
        for entry in os.listdir("/proc"):
            if not entry.isdigit() or int(entry) == os.getpid():
                continue
            cmd_file = Path(f"/proc/{entry}/cmdline")
            if cmd_file.is_file():
                cmd = cmd_file.read_bytes().decode(errors="ignore")
                if "bin/plus-ultra" in cmd or "plus_ultra.main" in cmd:
                    pid = int(entry)
                    if pid not in pids:
                        pids.append(pid)

    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
            for _ in range(20):
                time.sleep(0.05)
                try:
                    os.kill(pid, 0)
                except OSError:
                    break
            else:
                with contextlib.suppress(OSError):
                    os.kill(pid, signal.SIGKILL)
            print(f"[OK] Closed running PLUS-ULTRA process (PID: {pid}).")
        except OSError:
            pass


def uninstall_linux(opt: UninstallOptions) -> None:
    """Uninstall application and remove files on Linux."""
    stop_running_instances()
    home = Path.home()

    # 1. Binary
    if opt.remove_binary:
        _remove_path(home / ".local" / "bin" / "plus-ultra", "executable")
        icon_path = (
            home
            / ".local"
            / "share"
            / "icons"
            / "hicolor"
            / "256x256"
            / "apps"
            / "plus-ultra.png"
        )
        _remove_path(icon_path, "application icon")

    # 2. Desktop Launcher
    if opt.remove_shortcuts:
        desktop_file = (
            home / ".local" / "share" / "applications" / "plus-ultra.desktop"
        )
        _remove_path(desktop_file, "application launcher")

    # 3. Autostart
    if opt.remove_autostart:
        autostart_file = home / ".config" / "autostart" / "plus-ultra.desktop"
        _remove_path(autostart_file, "autostart desktop entry")

    # 4. User Data Purge
    if opt.purge_data:
        _remove_path(home / ".config" / "plus-ultra", "user settings")
        _remove_path(home / ".local" / "share" / "plus-ultra", "database")
        _remove_path(home / ".local" / "state" / "plus-ultra", "state & logs")
    else:
        print(f"\n{DIM}Note: User database and settings preserved at:{RESET}")
        print(f"  Database: {home / '.local' / 'share' / 'plus-ultra'}")
        print(f"  Settings: {home / '.config' / 'plus-ultra'}")

    print(f"\n{GREEN}{BOLD}PLUS-ULTRA uninstalled on Linux!{RESET}")


def uninstall_windows(opt: UninstallOptions) -> None:
    """Uninstall application and remove files on Windows 11."""
    stop_running_instances()
    local_appdata = Path(
        os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")
    )
    roaming = Path(
        os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")
    )

    # 1. Program folder & Binary
    if opt.remove_binary:
        install_dir = local_appdata / "Programs" / "plus-ultra"
        _remove_path(install_dir, "installation folder")

    # 2. Shortcuts
    if opt.remove_shortcuts:
        ps_cmd = (
            "$d = [Environment]::GetFolderPath('Desktop');\n"
            "$m = [Environment]::GetFolderPath('Programs');\n"
            "Remove-Item -Path (Join-Path $d 'PLUS-ULTRA.lnk') "
            "-Force -ErrorAction SilentlyContinue;\n"
            "Remove-Item -Path (Join-Path $m 'PLUS-ULTRA.lnk') "
            "-Force -ErrorAction SilentlyContinue;"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            check=False,
            capture_output=True,
        )
        print("[OK] Removed Desktop and Start Menu shortcuts.")

    # 3. Autostart Run Key
    if opt.remove_autostart:
        with contextlib.suppress(Exception):
            import winreg

            reg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_SET_VALUE
            ) as key:
                winreg.DeleteValue(key, "PLUS-ULTRA")
            print("[OK] Removed Windows Startup Run key.")

    # 4. User Data Purge
    if opt.purge_data:
        _remove_path(local_appdata / "plus-ultra", "database and state")
        _remove_path(roaming / "plus-ultra", "user settings")
    else:
        print(f"\n{DIM}Note: User database and settings preserved at:{RESET}")
        print(f"  Database: {local_appdata / 'plus-ultra'}")
        print(f"  Settings: {roaming / 'plus-ultra'}")

    print(f"\n{GREEN}{BOLD}PLUS-ULTRA uninstalled on Windows 11!{RESET}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="PLUS-ULTRA Desktop Assistant Uninstaller"
    )
    parser.add_argument(
        "--non-interactive",
        "-y",
        action="store_true",
        help="Run non-interactively",
    )
    parser.add_argument(
        "--purge",
        action="store_true",
        help="Purge all persistent user data, SQLite database, and settings",
    )
    parser.add_argument(
        "--keep-data",
        action="store_true",
        help="Preserve user database and settings (default)",
    )
    args = parser.parse_args()

    opt = UninstallOptions()
    if args.purge:
        opt.purge_data = True
    elif args.keep_data:
        opt.purge_data = False

    is_interactive = (
        sys.stdin.isatty() and sys.stdout.isatty() and not args.non_interactive
    )

    if is_interactive:
        confirmed = run_interactive_menu(opt)
        if not confirmed:
            print("\nUninstallation cancelled by user.")
            sys.exit(0)
    else:
        print("==> Running uninstallation with configured options.")

    print(f"\n{RED}Proceeding with PLUS-ULTRA uninstallation...{RESET}")
    if sys.platform == "win32":
        uninstall_windows(opt)
    else:
        uninstall_linux(opt)


if __name__ == "__main__":
    main()
