import argparse
import re
import sys
import time

import adb
from detector import find_green_button

PACKAGE_PATTERN = re.compile(r"[A-Za-z]\w*(\.[A-Za-z]\w*)+")
DEFAULT_TIMEOUT = 10.0
POLL_INTERVAL = 0.5


def package_name(value: str) -> str:
    if not PACKAGE_PATTERN.fullmatch(value):
        raise argparse.ArgumentTypeError(f"invalid package name: {value!r}")
    return value


def wait_for_green_button(timeout: float) -> tuple[int, int] | None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if point := find_green_button(adb.take_screenshot()):
            return point
        time.sleep(POLL_INTERVAL)
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Launch an Android app over adb and tap a green button on its screen")
    parser.add_argument("package", type=package_name, help="application package name, e.g. com.example.app")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="seconds to wait for the button")
    args = parser.parse_args()

    try:
        adb.launch_app(args.package)
        point = wait_for_green_button(args.timeout)
        if point is None:
            print(f"Green button not found in {args.package} within {args.timeout:g} s")
            return 1
        adb.tap(*point)
    except adb.AdbError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print(f"Green button tapped at {point}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
