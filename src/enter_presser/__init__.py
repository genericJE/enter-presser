from __future__ import annotations

import argparse
import time
from dataclasses import dataclass

from pynput.keyboard import Controller, Key


@dataclass(frozen=True)
class Config:
    minutes: float
    count: int
    interval_seconds: float
    dry_run: bool


def non_negative_float(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid float value: {value!r}") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be non-negative")
    return parsed


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid integer value: {value!r}") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be at least 1")
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
        type=non_negative_float,
        metavar="MINUTES",
        help="Delay before pressing Enter, in minutes. Example: -t 23",
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
        minutes=args.time,
        count=args.count,
        interval_seconds=args.interval,
        dry_run=args.dry_run,
    )


def press_enter(count: int, interval_seconds: float) -> None:
    keyboard = Controller()
    for index in range(count):
        keyboard.press(Key.enter)
        keyboard.release(Key.enter)
        if index < count - 1:
            time.sleep(interval_seconds)


def main() -> None:
    config = parse_args()
    delay_seconds = config.minutes * 60

    print(f"Waiting {config.minutes:g} minute(s).")
    print("Focus the target input box now. Press Ctrl+C to cancel.")

    try:
        time.sleep(delay_seconds)
        if config.dry_run:
            print(f"Dry run: would press Enter {config.count} time(s).")
            return
        press_enter(config.count, config.interval_seconds)
        print(f"Pressed Enter {config.count} time(s).")
    except KeyboardInterrupt:
        print("\nCancelled.")


if __name__ == "__main__":
    main()
