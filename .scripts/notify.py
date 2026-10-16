"""Desktop notification testing utility for PLUS-ULTRA.

Dispatches instant desktop notifications via notify-send, or delays dispatch
by X minutes/seconds as specified by CLI arguments.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Ensure 'src' is in sys.path when executed directly
_src_dir = Path(__file__).resolve().parents[1] / "src"
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from plus_ultra.desktop import send_desktop_notification  # noqa: E402


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments for notification script."""
    parser = argparse.ArgumentParser(
        description=(
            "Dispatch a desktop notification immediately or after a delay."
        )
    )
    parser.add_argument(
        "delay_minutes",
        nargs="?",
        type=float,
        default=None,
        help="Delay in minutes before popping up alert (e.g. 1, 2, 0.5).",
    )
    parser.add_argument(
        "--minutes",
        "-m",
        type=float,
        default=None,
        help="Explicit delay in minutes (overrides positional delay).",
    )
    parser.add_argument(
        "--seconds",
        "-s",
        type=float,
        default=None,
        help="Explicit delay in seconds (useful for fast testing, e.g. -s 10).",
    )
    parser.add_argument(
        "--title",
        "-t",
        default="PLUS-ULTRA Desktop Alert",
        help="Notification summary title.",
    )
    parser.add_argument(
        "--message",
        default="Test notification successfully dispatched from PLUS-ULTRA.",
        help="Notification body text.",
    )
    parser.add_argument(
        "--urgency",
        "-u",
        choices=["low", "normal", "critical"],
        default="normal",
        help="Desktop notification urgency level.",
    )
    return parser.parse_args(args)


def wait_with_progress(total_seconds: float) -> None:
    """Sleep for specified duration while printing progress to console."""
    remaining = int(total_seconds)
    print(f"Waiting {total_seconds:.1f}s before sending notification...")
    try:
        while remaining > 0:
            mins, secs = divmod(remaining, 60)
            time_str = f"{mins:02d}:{secs:02d}"
            print(f"\rDispatching in {time_str}... ", end="", flush=True)
            sleep_step = min(1.0, total_seconds)
            time.sleep(sleep_step)
            remaining -= 1
        print("\rDispatching now!               ")
    except KeyboardInterrupt:
        print("\nNotification cancelled by user.")
        raise


def dispatch_notification(
    title: str,
    message: str,
    delay_seconds: float = 0.0,
    urgency: str = "normal",
) -> bool:
    """Optionally wait, then fire desktop notification via notify-send."""
    if delay_seconds > 0:
        wait_with_progress(delay_seconds)

    success = send_desktop_notification(
        title=title,
        message=message,
        urgency=urgency,
    )
    return success


def main(argv: list[str] | None = None) -> int:
    """CLI script entrypoint."""
    args = parse_args(argv)

    # Determine delay in seconds
    delay_sec = 0.0
    if args.seconds is not None:
        delay_sec = max(0.0, args.seconds)
    elif args.minutes is not None:
        delay_sec = max(0.0, args.minutes * 60.0)
    elif args.delay_minutes is not None:
        delay_sec = max(0.0, args.delay_minutes * 60.0)

    try:
        success = dispatch_notification(
            title=args.title,
            message=args.message,
            delay_seconds=delay_sec,
            urgency=args.urgency,
        )
        if success:
            print(f"Notification sent successfully: '{args.title}'")
            return 0
        print("Failed to dispatch notification (notify-send may be missing).")
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
