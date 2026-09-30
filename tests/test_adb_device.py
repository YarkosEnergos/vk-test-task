import pytest

from green_button.domain.errors import AppLaunchError, DeviceUnavailableError, InvalidScreenshotError
from green_button.domain.models import PackageName, Point
from green_button.infrastructure.adb.client import AdbClient
from green_button.infrastructure.adb.device import AdbDevice
from green_button.infrastructure.adb.errors import AdbCommandError

PACKAGE = PackageName("com.example.app")
PNG = b"\x89PNG\r\n\x1a\nrest-of-image"
RESOLVE = (
    "shell cmd package resolve-activity --brief "
    "-a android.intent.action.MAIN -c android.intent.category.LAUNCHER com.example.app"
)
AM_START = (
    "shell am start -W -a android.intent.action.MAIN -c android.intent.category.LAUNCHER "
    "-n com.example.app/.MainActivity"
)
MONKEY = "shell monkey -p com.example.app -c android.intent.category.LAUNCHER 1"
RESOLVED = "priority=0 preferredOrder=0 match=0x108000 specificIndex=-1 isDefault=true\ncom.example.app/.MainActivity\n"

type Response = str | bytes | Exception


class FakeAdbClient(AdbClient):
    def __init__(self, responses: dict[str, Response] | None = None) -> None:
        super().__init__("adb")
        self._responses = responses or {}
        self.commands: list[str] = []

    def start_server(self) -> None:
        self.commands.append("start-server")

    def run(self, *args: str) -> bytes:
        command = " ".join(args)
        self.commands.append(command)
        response = self._responses.get(command, b"")
        if isinstance(response, Exception):
            raise response
        return response.encode() if isinstance(response, str) else response


def command_error(output: str) -> AdbCommandError:
    return AdbCommandError(["adb"], 1, output)


def test_connect_starts_server_and_checks_device_state() -> None:
    client = FakeAdbClient({"get-state": "device\n"})

    AdbDevice(client).connect()

    assert client.commands == ["start-server", "get-state"]


def test_connect_reports_missing_device() -> None:
    client = FakeAdbClient({"get-state": command_error("adb: no devices/emulators found")})

    with pytest.raises(DeviceUnavailableError, match="no devices/emulators found"):
        AdbDevice(client).connect()


def test_connect_rejects_device_in_wrong_state() -> None:
    with pytest.raises(DeviceUnavailableError, match="recovery"):
        AdbDevice(FakeAdbClient({"get-state": "recovery\n"})).connect()


@pytest.mark.parametrize(("package", "installed"), [("com.example.app", True), ("com.example", False)])
def test_is_installed_matches_exact_package_name(package: str, installed: bool) -> None:
    listing = "package:com.example.app\r\npackage:com.example.app.debug\r\n"
    client = FakeAdbClient({f"shell pm list packages {package}": listing})

    assert AdbDevice(client).is_installed(PackageName(package)) is installed


def test_launch_starts_resolved_launcher_activity() -> None:
    output = "Starting: Intent { cmp=com.example.app/.MainActivity }\nStatus: ok\nLaunchState: COLD\nComplete\n"
    client = FakeAdbClient({RESOLVE: RESOLVED, AM_START: output})

    AdbDevice(client).launch_app(PACKAGE)

    assert client.commands == [RESOLVE, AM_START]


def test_launch_is_not_confused_by_error_in_activity_name() -> None:
    component = "com.example.app/.ErrorScreenActivity"
    am_start = AM_START.replace("com.example.app/.MainActivity", component)
    output = f"Starting: Intent {{ cmp={component} }}\nStatus: ok\nActivity: {component}\nComplete\n"
    client = FakeAdbClient({RESOLVE: f"priority=0\n{component}\n", am_start: output})

    AdbDevice(client).launch_app(PACKAGE)

    assert client.commands == [RESOLVE, am_start]


def test_launch_reports_am_start_error() -> None:
    output = "Starting: Intent { ... }\nError: Activity class {com.example.app/.MainActivity} does not exist.\n"
    client = FakeAdbClient({RESOLVE: RESOLVED, AM_START: output})

    with pytest.raises(AppLaunchError, match="does not exist"):
        AdbDevice(client).launch_app(PACKAGE)


@pytest.mark.parametrize(
    "resolve_response",
    ["No activity found\n", command_error("/system/bin/sh: cmd: not found")],
    ids=["no-activity", "old-android"],
)
def test_launch_falls_back_to_monkey(resolve_response: Response) -> None:
    client = FakeAdbClient({RESOLVE: resolve_response, MONKEY: "Events injected: 1\n"})

    AdbDevice(client).launch_app(PACKAGE)

    assert client.commands == [RESOLVE, MONKEY]


def test_launch_reports_app_without_launcher_activity() -> None:
    client = FakeAdbClient({RESOLVE: "No activity found\n", MONKEY: "** No activities found to run, monkey aborted.\n"})

    with pytest.raises(AppLaunchError, match="no launchable activity"):
        AdbDevice(client).launch_app(PACKAGE)


def test_wake_up_ignores_unsupported_commands() -> None:
    client = FakeAdbClient({"shell wm dismiss-keyguard": command_error("Unknown command")})

    AdbDevice(client).wake_up()

    assert client.commands == ["shell input keyevent KEYCODE_WAKEUP", "shell wm dismiss-keyguard"]


def test_stop_app_force_stops_package() -> None:
    client = FakeAdbClient()

    AdbDevice(client).stop_app(PACKAGE)

    assert client.commands == ["shell am force-stop com.example.app"]


def test_take_screenshot_returns_png() -> None:
    client = FakeAdbClient({"exec-out screencap -p": PNG})

    assert AdbDevice(client).take_screenshot() == PNG


@pytest.mark.parametrize(
    ("output", "message"),
    [(b"", "empty output"), (b"error: display is off", "display is off")],
)
def test_take_screenshot_rejects_non_png_output(output: bytes, message: str) -> None:
    client = FakeAdbClient({"exec-out screencap -p": output})

    with pytest.raises(InvalidScreenshotError, match=message):
        AdbDevice(client).take_screenshot()


def test_tap_sends_input_event() -> None:
    client = FakeAdbClient()

    AdbDevice(client).tap(Point(360, 1065))

    assert client.commands == ["shell input tap 360 1065"]
