from __future__ import annotations

import argparse
import math
import re
import subprocess
import sys
import time
from dataclasses import dataclass


HMS_PATTERN = re.compile(r"^(?P<hours>\d+):(?P<minutes>[0-5]\d):(?P<seconds>[0-5]\d)$")
MS_PATTERN = re.compile(r"^(?P<minutes>\d+):(?P<seconds>[0-5]\d)$")

# Short pause between synthesized keystrokes so the focused app does not drop
# characters while a --message is typed.
KEYSTROKE_DELAY_SECONDS = 0.02


@dataclass(frozen=True)
class Config:
    seconds: float
    count: int
    interval_seconds: float
    dry_run: bool
    message: str | None


def parse_time(value: str) -> float:
    """
    Parse one of:
    - plain seconds, e.g. "23" or "0.5"
    - MM:SS, e.g. "02:30" or "90:00"
    - HH:MM:SS, e.g. "00:23:00" or "01:30:15"

    Returns seconds.
    """
    hms_match = HMS_PATTERN.fullmatch(value)
    if hms_match:
        hours = int(hms_match.group("hours"))
        minutes = int(hms_match.group("minutes"))
        seconds = int(hms_match.group("seconds"))
        return float(hours * 3600 + minutes * 60 + seconds)

    ms_match = MS_PATTERN.fullmatch(value)
    if ms_match:
        minutes = int(ms_match.group("minutes"))
        seconds = int(ms_match.group("seconds"))
        return float(minutes * 60 + seconds)

    try:
        seconds_as_float = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "time must be seconds, like '23' or '0.5', "
            "MM:SS, like '02:30', or HH:MM:SS, like '01:30:15'"
        ) from exc

    if seconds_as_float < 0:
        raise argparse.ArgumentTypeError("time must be non-negative")

    return seconds_as_float


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid integer value: {value!r}") from exc

    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be at least 1")

    return parsed


def non_negative_float(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid float value: {value!r}") from exc

    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be non-negative")

    return parsed


def parse_args() -> Config:
    parser = argparse.ArgumentParser(
        prog="enter-presser",
        description="Press Enter/Return in the currently focused macOS application after a delay.",
    )
    parser.add_argument(
        "time",
        type=parse_time,
        metavar="SECONDS_OR_MM:SS_OR_HH:MM:SS",
        help="Delay before pressing Enter. Accepts seconds, e.g. 23, MM:SS, e.g. 02:30, or HH:MM:SS, e.g. 01:30:00.",
    )
    parser.add_argument(
        "-m",
        "--message",
        default=None,
        metavar="TEXT",
        help="Type TEXT into the focused app before pressing Enter.",
    )
    parser.add_argument(
        "--count",
        default=1,
        type=positive_int,
        help="Number of Enter key presses. Default: 1",
    )
    parser.add_argument(
        "--interval",
        default=0.5,
        type=non_negative_float,
        metavar="SECONDS",
        help="Seconds between presses when --count is greater than 1. Default: 0.5",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Wait, then print what would happen without typing or pressing Enter.",
    )

    args = parser.parse_args()

    return Config(
        seconds=args.time,
        count=args.count,
        interval_seconds=args.interval,
        dry_run=args.dry_run,
        message=args.message,
    )


def format_duration(seconds: float) -> str:
    total_seconds = int(seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds_part = divmod(remainder, 60)

    if hours:
        return f"{hours}h {minutes}m {seconds_part}s"
    if minutes:
        return f"{minutes}m {seconds_part}s"
    return f"{seconds:g}s"


def format_countdown(seconds: int) -> str:
    """
    Format a whole number of seconds for the live countdown, collapsing the
    units as the deadline approaches:

    - 1 hour or more -> HH:MM:SS
    - under 1 hour   -> MM:SS
    - under 1 minute -> seconds
    """
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds_part = divmod(remainder, 60)

    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds_part:02d}"
    if minutes:
        return f"{minutes:02d}:{seconds_part:02d}"
    return str(seconds_part)


def countdown(total_seconds: float) -> None:
    """
    Wait for total_seconds, showing a once-per-second countdown that rewrites a
    single line in place. Falls back to a plain wait when stdout is not an
    interactive terminal (e.g. when output is piped or redirected).
    """
    deadline = time.monotonic() + total_seconds

    if not sys.stdout.isatty():
        time.sleep(max(0.0, total_seconds))
        return

    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break

        whole_seconds = math.ceil(remaining)
        # "\033[K" erases anything left over from a previously longer line so
        # the display stays clean as HH:MM:SS collapses to MM:SS to seconds.
        sys.stdout.write(
            f"\rEnter will be pressed in {format_countdown(whole_seconds)}\033[K"
        )
        sys.stdout.flush()

        # Sleep just long enough to land on the next whole-second boundary.
        time.sleep(remaining - (whole_seconds - 1))

    # Clear the countdown line before the result message is printed.
    sys.stdout.write("\r\033[K")
    sys.stdout.flush()


def type_message(
    message: str, keystroke_delay_seconds: float = KEYSTROKE_DELAY_SECONDS
) -> None:
    """
    Type message into the focused application one character at a time, pausing
    keystroke_delay_seconds between keystrokes so the target app does not drop
    characters.

    The message is passed to osascript as a run-handler argument rather than
    interpolated into the script, so any quotes or backslashes in it are sent
    verbatim and need no escaping.
    """
    script_lines = (
        "on run argv",
        "set theMessage to item 1 of argv",
        'tell application "System Events"',
        "repeat with charIndex from 1 to (count of characters of theMessage)",
        "keystroke (character charIndex of theMessage)",
        f"delay {keystroke_delay_seconds}",
        "end repeat",
        "end tell",
        "end run",
    )

    command = ["osascript"]
    for line in script_lines:
        command.extend(("-e", line))
    command.extend(("--", message))

    subprocess.run(command, check=True)


def press_enter_once() -> None:
    subprocess.run(
        ["osascript", "-e", 'tell application "System Events" to key code 36'],
        check=True,
    )


def press_enter(count: int, interval_seconds: float) -> None:
    for index in range(count):
        press_enter_once()

        if index < count - 1:
            time.sleep(interval_seconds)


def main() -> None:
    config = parse_args()

    print(f"Waiting {format_duration(config.seconds)}.")
    print("Focus the target input box now. Press Ctrl+C to cancel.")

    try:
        countdown(config.seconds)

        if config.dry_run:
            if config.message is not None:
                print(
                    f"Dry run: would type {config.message!r}, "
                    f"then press Enter {config.count} time(s)."
                )
            else:
                print(f"Dry run: would press Enter {config.count} time(s).")
            return

        if config.message is not None:
            type_message(config.message)

        press_enter(config.count, config.interval_seconds)

        if config.message is not None:
            print(f"Typed the message and pressed Enter {config.count} time(s).")
        else:
            print(f"Pressed Enter {config.count} time(s).")

    except KeyboardInterrupt:
        print("\nCancelled.")
    except subprocess.CalledProcessError as exc:
        raise SystemExit(
            "Failed to send keystrokes using macOS System Events. "
            "Make sure your terminal has Accessibility permission in "
            "System Settings -> Privacy & Security -> Accessibility."
        ) from exc


if __name__ == "__main__":
    main()
