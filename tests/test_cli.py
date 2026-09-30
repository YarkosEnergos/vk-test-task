import pytest

from green_button.application.tap_green_button import TapGreenButtonUseCase
from green_button.infrastructure.adb.errors import AdbNotFoundError
from green_button.presentation.cli import ExitCode, main
from tests.fakes import FakeClock, FakeDevice, ScriptedDetector, make_button


class Environment:
    def __init__(self, detector: ScriptedDetector, *, installed: bool = True) -> None:
        self.clock = FakeClock()
        self.device = FakeDevice(self.clock, installed=installed)
        self.detector = detector
        self.factory_calls: list[tuple[str | None, str | None]] = []

    def factory(self, adb_path: str | None, serial: str | None) -> TapGreenButtonUseCase:
        self.factory_calls.append((adb_path, serial))
        return TapGreenButtonUseCase(self.device, self.detector, self.clock)


def test_reports_tapped_button(capsys: pytest.CaptureFixture[str]) -> None:
    environment = Environment(ScriptedDetector([make_button(100, 200, 300, 100)]))

    exit_code = main(["com.example.app"], environment.factory)

    assert exit_code == ExitCode.TAPPED
    assert capsys.readouterr().out == (
        "Green button found in com.example.app at (250, 250), size 300x100, after 0.0 s. Tapped.\n"
    )
    assert environment.device.calls[-1] == "tap 250 250"


def test_reports_missing_button(capsys: pytest.CaptureFixture[str]) -> None:
    environment = Environment(ScriptedDetector([]))

    exit_code = main(["com.example.app", "--timeout", "1"], environment.factory)

    assert exit_code == ExitCode.NOT_FOUND
    assert capsys.readouterr().out == (
        "Green button not found in com.example.app within 1 s (3 screenshot(s) checked).\n"
    )


def test_forwards_options() -> None:
    environment = Environment(ScriptedDetector([make_button(0, 0, 10, 10)]))

    main(
        ["com.example.app", "--serial", "emulator-5554", "--adb-path", "/opt/adb", "--no-restart"],
        environment.factory,
    )

    assert environment.factory_calls == [("/opt/adb", "emulator-5554")]
    assert "stop_app com.example.app" not in environment.device.calls


def test_reports_device_errors(capsys: pytest.CaptureFixture[str]) -> None:
    environment = Environment(ScriptedDetector(), installed=False)

    exit_code = main(["com.example.app"], environment.factory)

    assert exit_code == ExitCode.FAILURE
    assert capsys.readouterr().err == "Error: package com.example.app is not installed on the device\n"


def test_reports_missing_adb(capsys: pytest.CaptureFixture[str]) -> None:
    def factory(adb_path: str | None, serial: str | None) -> TapGreenButtonUseCase:
        raise AdbNotFoundError("adb executable not found")

    assert main(["com.example.app"], factory) == ExitCode.FAILURE
    assert "adb executable not found" in capsys.readouterr().err


@pytest.mark.parametrize(
    "argv",
    [
        ["not a package"],
        ["com.example.app", "--timeout", "0"],
        ["com.example.app", "--timeout", "-1"],
        ["com.example.app", "--timeout", "nan"],
        ["com.example.app", "--timeout", "soon"],
        [],
    ],
)
def test_rejects_invalid_arguments(argv: list[str], capsys: pytest.CaptureFixture[str]) -> None:
    environment = Environment(ScriptedDetector())

    with pytest.raises(SystemExit) as exit_info:
        main(argv, environment.factory)

    assert exit_info.value.code == 2
    assert "usage:" in capsys.readouterr().err
    assert environment.factory_calls == []


def test_exit_codes_are_stable() -> None:
    assert {code.name: int(code) for code in ExitCode} == {
        "TAPPED": 0,
        "NOT_FOUND": 1,
        "FAILURE": 3,
        "INTERRUPTED": 130,
    }
