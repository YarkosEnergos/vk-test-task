from green_button.application.tap_green_button import TapGreenButtonUseCase
from green_button.domain.models import PackageName
from green_button.infrastructure.vision.green_button_detector import OpenCvGreenButtonDetector
from tests.fakes import FakeClock, FakeDevice
from tests.screens import BLUE, GREEN, RED, Screen

PACKAGE = PackageName("com.example.app")


def test_taps_green_button_once_app_screen_is_rendered() -> None:
    splash = Screen().text("Loading...", 220, 640, "#757575").png()
    app_screen = (
        Screen()
        .rectangle(0, 0, 720, 160, "#3F51B5")
        .button(80, 400, 560, 140, RED, "Cancel")
        .button(80, 700, 560, 140, GREEN, "Continue")
        .png()
    )
    clock = FakeClock()
    device = FakeDevice(clock, [splash, splash, app_screen], screenshot_duration=0.3)

    result = TapGreenButtonUseCase(device, OpenCvGreenButtonDetector(), clock).execute(PACKAGE)

    assert result.tapped
    assert result.attempts == 3
    assert device.calls[-1] == "tap 360 770"


def test_reports_absence_of_green_button() -> None:
    screen = Screen().button(80, 400, 560, 140, RED, "Cancel").button(80, 700, 560, 140, BLUE, "Ok").png()
    clock = FakeClock()
    device = FakeDevice(clock, [screen], screenshot_duration=0.3)

    result = TapGreenButtonUseCase(device, OpenCvGreenButtonDetector(), clock).execute(PACKAGE, timeout=10.0)

    assert not result.tapped
    assert result.elapsed >= 10.0
    assert not any(call.startswith("tap") for call in device.calls)
