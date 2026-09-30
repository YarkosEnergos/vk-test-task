import logging
import re

from green_button.domain.errors import (
    AppLaunchError,
    DeviceUnavailableError,
    InvalidScreenshotError,
)
from green_button.domain.models import PackageName, Point
from green_button.infrastructure.adb.client import AdbClient
from green_button.infrastructure.adb.errors import AdbCommandError

logger = logging.getLogger(__name__)

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_LAUNCHER_INTENT = ("-a", "android.intent.action.MAIN", "-c", "android.intent.category.LAUNCHER")
_AM_START_FAILURE = re.compile(r"^\s*(Error|Exception|java\.lang\.\w+)", re.MULTILINE)
_MONKEY_FAILURE = re.compile(r"No activities found|monkey aborted")
_WAKE_UP_COMMANDS = (
    ("input", "keyevent", "KEYCODE_WAKEUP"),
    ("wm", "dismiss-keyguard"),
)


class AdbDevice:
    def __init__(self, client: AdbClient) -> None:
        self._client = client

    def connect(self) -> None:
        self._client.start_server()
        try:
            state = self._client.run("get-state").decode("utf-8", errors="replace").strip()
        except AdbCommandError as exc:
            raise DeviceUnavailableError(f"device is not available: {exc.output}") from exc
        if state != "device":
            raise DeviceUnavailableError(f"device is in {state!r} state, expected 'device'")

    def is_installed(self, package: PackageName) -> bool:
        output = self._client.shell("pm", "list", "packages", package.value)
        return f"package:{package}" in output.split()

    def wake_up(self) -> None:
        for command in _WAKE_UP_COMMANDS:
            try:
                self._client.shell(*command)
            except AdbCommandError as exc:
                logger.debug("Ignoring failed wake-up step: %s", exc)

    def stop_app(self, package: PackageName) -> None:
        self._client.shell("am", "force-stop", package.value)

    def launch_app(self, package: PackageName) -> None:
        component = self._resolve_launcher_activity(package)
        if component is None:
            self._launch_with_monkey(package)
        else:
            self._start_activity(component)

    def take_screenshot(self) -> bytes:
        data = self._client.exec_out("screencap", "-p")
        if not data.startswith(_PNG_SIGNATURE):
            preview = data[:200].decode("utf-8", errors="replace").strip()
            raise InvalidScreenshotError(f"device returned a non-PNG screenshot: {preview or 'empty output'}")
        return data

    def tap(self, point: Point) -> None:
        self._client.shell("input", "tap", str(point.x), str(point.y))

    def _resolve_launcher_activity(self, package: PackageName) -> str | None:
        try:
            output = self._client.shell(
                "cmd", "package", "resolve-activity", "--brief", *_LAUNCHER_INTENT, package.value
            )
        except AdbCommandError as exc:
            logger.debug("Cannot resolve launcher activity: %s", exc)
            return None
        lines = output.strip().splitlines()
        component = lines[-1].strip() if lines else ""
        return component if component.startswith(f"{package}/") else None

    def _start_activity(self, component: str) -> None:
        output = self._client.shell("am", "start", "-W", *_LAUNCHER_INTENT, "-n", component)
        if _AM_START_FAILURE.search(output):
            raise AppLaunchError(f"failed to start {component}: {output.strip()}")

    def _launch_with_monkey(self, package: PackageName) -> None:
        output = self._client.shell("monkey", "-p", package.value, "-c", "android.intent.category.LAUNCHER", "1")
        if _MONKEY_FAILURE.search(output):
            raise AppLaunchError(f"{package} has no launchable activity: {output.strip()}")
