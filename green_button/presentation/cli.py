import argparse
import logging
import math
import sys
from collections.abc import Callable, Sequence
from enum import IntEnum

from green_button.application.tap_green_button import (
    DEFAULT_TIMEOUT,
    TapGreenButtonUseCase,
    TapResult,
)
from green_button.bootstrap import build_use_case
from green_button.domain.errors import GreenButtonError, InvalidPackageNameError
from green_button.domain.models import PackageName

type UseCaseFactory = Callable[[str | None, str | None], TapGreenButtonUseCase]


class ExitCode(IntEnum):
    TAPPED = 0
    NOT_FOUND = 1
    FAILURE = 3
    INTERRUPTED = 130


def main(argv: Sequence[str] | None = None, use_case_factory: UseCaseFactory = build_use_case) -> int:
    args = _build_parser().parse_args(argv)
    _configure_logging(args.verbose)
    try:
        use_case = use_case_factory(args.adb_path, args.serial)
        result = use_case.execute(args.package, timeout=args.timeout, restart=args.restart)
    except GreenButtonError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return ExitCode.FAILURE
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        return ExitCode.INTERRUPTED
    print(_describe(result, args.package, args.timeout))
    return ExitCode.TAPPED if result.tapped else ExitCode.NOT_FOUND


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="green-button",
        description="Launch an Android app over adb, find a green button on its screen and tap it.",
    )
    parser.add_argument("package", type=_package_name, help="application package name, e.g. com.example.app")
    parser.add_argument(
        "-t",
        "--timeout",
        type=_positive_float,
        default=DEFAULT_TIMEOUT,
        help="seconds to wait for the green button after launch (default: %(default)g)",
    )
    parser.add_argument(
        "-s",
        "--serial",
        help="serial of the target device (default: $ANDROID_SERIAL or the only connected device)",
    )
    parser.add_argument(
        "--adb-path",
        help="path to the adb executable (default: looked up in PATH, $ANDROID_HOME, $ANDROID_SDK_ROOT)",
    )
    parser.add_argument(
        "--no-restart",
        dest="restart",
        action="store_false",
        help="do not force-stop the app before launching it",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="print debug logs to stderr")
    return parser


def _package_name(value: str) -> PackageName:
    try:
        return PackageName(value)
    except InvalidPackageNameError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def _positive_float(value: str) -> float:
    try:
        number = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a number: {value!r}") from None
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError(f"must be a positive number: {value!r}")
    return number


def _configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.WARNING,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        stream=sys.stderr,
    )


def _describe(result: TapResult, package: PackageName, timeout: float) -> str:
    if result.button is None:
        return f"Green button not found in {package} within {timeout:g} s ({result.attempts} screenshot(s) checked)."
    bounds = result.button.bounds
    center = result.button.center
    return (
        f"Green button found in {package} at ({center.x}, {center.y}), "
        f"size {bounds.width}x{bounds.height}, after {result.elapsed:.1f} s. Tapped."
    )
