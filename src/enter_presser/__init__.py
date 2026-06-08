from __future__ import annotations

import argparse
import re
import time
from dataclasses import dataclass

from pynput.keyboard import Controller, Key


TIME_PATTERN = re.compile(r"^(?P<hours>\d+):(?P<minutes>[0-5]\d):(?P<seconds>[0-5]\d)$")


@dataclass(frozen=True)
class Config:
    seconds: float
    raw_time: str
    count: int
    interval_seconds: float
    dry_run: bool


def parse_time(value: str) -> float:
    """
    Parse either:
    - plain minutes, e.g. "23" or "0.5"
    - HH:MM:SS, e.g. "00:23:00" or "01:30:15"

    Returns seconds.
    """
    match = TIME_PATTERN.fullmatch(value)

    if match:
        hours = int(match.group("hours"))
        minutes = int(match.group("minutes"))
        seconds = int(match.group("seconds"))
        return float(hours * 3600 + minutes * 60 + seconds)

    try:
        minutes_as_float = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "time must be either minutes, like '23' or '0.5', "
            "or HH:MM:SS, like '00:23:00'"
        ) from exc

    if minutes_as_float < 0:
        raise argparse.ArgumentTypeError("time must be non-negative")

    return minutes_as_float * 60


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
        description="Press Enter/Return in the currently focused application after a delay.",
    )
    parser.add_argument(
        "-t",
        "--time",
        required=True,
        type=parse_time,
        metavar="MINUTES_OR_HH:MM:SS",
        help="Delay before pressing Enter. Accepts minutes, e.g. 23, or HH:MM:SS, e.g. 00:23:00.",
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
        help="Wait, then print what would happen without pressing Enter.",
    )
    args = parser.parse_args()
    return Config(
        seconds=args.time,
        raw_time=str(args.time),
        count=args.count,
        interval_seconds=args.interval,
        dry_run=args.dry_run,
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


def press_enter(count: int, interval_seconds: float) -> None:
    keyboard = Controller()
    for index in range(count):
        keyboard.press(Key.enter)
        keyboard.release(Key.enter)
        if index < count - 1:
            time.sleep(interval_seconds)


def main() -> None:
    config = parse_args()

    print(f"Waiting {format_duration(config.seconds)}.")
    print("Focus the target input box now. Press Ctrl+C to cancel.")

    try:
        time.sleep(config.seconds)
        if config.dry_run:
            print(f"Dry run: would press Enter {config.count} time(s).")
            return
        press_enter(config.count, config.interval_seconds)
        print(f"Pressed Enter {config.count} time(s).")
    except KeyboardInterrupt:
        print("\nCancelled.")


if __name__ == "__main__":
    main()
