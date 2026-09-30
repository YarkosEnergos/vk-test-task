import pytest

from green_button.application.tap_green_button import TapGreenButtonUseCase, TapResult
from green_button.domain.errors import AppNotInstalledError
from green_button.domain.models import PackageName
from tests.fakes import FakeClock, FakeDevice, ScriptedDetector, make_button

PACKAGE = PackageName("com.example.app")


def test_launches_app_and_taps_center_of_found_button() -> None:
    clock = FakeClock()
    device = FakeDevice(clock)
    button = make_button(100, 200, 300, 100)

    result = TapGreenButtonUseCase(device, ScriptedDetector([button]), clock).execute(PACKAGE)

    assert result == TapResult(button=button, attempts=1, elapsed=0.0)
    assert result.tapped
    assert device.calls == [
        "connect",
        "is_installed com.example.app",
        "wake_up",
        "stop_app com.example.app",
        "launch_app com.example.app",
        "take_screenshot",
        "tap 250 250",
    ]


def test_keeps_polling_until_button_appears() -> None:
    clock = FakeClock()
    device = FakeDevice(clock, screenshot_duration=0.25)
    button = make_button(0, 0, 100, 100)
    detector = ScriptedDetector([], [], [button])

    result = TapGreenButtonUseCase(device, detector, clock, poll_interval=0.5).execute(PACKAGE)

    assert result == TapResult(button=button, attempts=3, elapsed=1.75)
    assert clock.sleeps == [0.5, 0.5]
    assert device.calls[-1] == "tap 50 50"


def test_reports_not_found_after_timeout_without_tapping() -> None:
    clock = FakeClock()
    device = FakeDevice(clock)

    result = TapGreenButtonUseCase(device, ScriptedDetector([]), clock, poll_interval=0.5).execute(PACKAGE, timeout=2.0)

    assert result == TapResult(button=None, attempts=5, elapsed=2.0)
    assert not result.tapped
    assert not any(call.startswith("tap") for call in device.calls)


def test_does_not_sleep_past_deadline_and_checks_screen_at_deadline() -> None:
    clock = FakeClock()
    device = FakeDevice(clock)

    result = TapGreenButtonUseCase(device, ScriptedDetector([]), clock, poll_interval=0.375).execute(
        PACKAGE, timeout=1.0
    )

    assert clock.sleeps == [0.375, 0.375, 0.25]
    assert result.attempts == 4
    assert result.elapsed == 1.0


def test_finishes_attempt_started_before_deadline() -> None:
    clock = FakeClock()
    device = FakeDevice(clock, screenshot_duration=0.75)

    result = TapGreenButtonUseCase(device, ScriptedDetector([]), clock, poll_interval=0.5).execute(PACKAGE, timeout=1.0)

    assert clock.sleeps == [0.25]
    assert result == TapResult(button=None, attempts=2, elapsed=1.75)


def test_taps_largest_of_several_buttons() -> None:
    clock = FakeClock()
    device = FakeDevice(clock)
    detector = ScriptedDetector([make_button(0, 0, 100, 100), make_button(0, 500, 600, 200)])

    result = TapGreenButtonUseCase(device, detector, clock).execute(PACKAGE)

    assert result.button == make_button(0, 500, 600, 200)
    assert device.calls[-1] == "tap 300 600"


def test_raises_when_app_is_not_installed() -> None:
    clock = FakeClock()
    device = FakeDevice(clock, installed=False)

    with pytest.raises(AppNotInstalledError, match=r"com\.example\.app"):
        TapGreenButtonUseCase(device, ScriptedDetector(), clock).execute(PACKAGE)

    assert device.calls == ["connect", "is_installed com.example.app"]


def test_does_not_stop_app_when_restart_is_disabled() -> None:
    clock = FakeClock()
    device = FakeDevice(clock)

    TapGreenButtonUseCase(device, ScriptedDetector([make_button(0, 0, 10, 10)]), clock).execute(PACKAGE, restart=False)

    assert "stop_app com.example.app" not in device.calls
    assert "launch_app com.example.app" in device.calls
