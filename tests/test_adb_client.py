import subprocess
from typing import Any

import pytest

from green_button.infrastructure.adb.client import AdbClient
from green_button.infrastructure.adb.errors import AdbCommandError, AdbNotFoundError, AdbTimeoutError


class FakeRun:
    def __init__(
        self,
        *,
        returncode: int = 0,
        stdout: bytes = b"",
        stderr: bytes = b"",
        error: Exception | None = None,
    ) -> None:
        self._returncode = returncode
        self._stdout = stdout
        self._stderr = stderr
        self._error = error
        self.command: list[str] = []
        self.options: dict[str, Any] = {}

    def __call__(self, command: list[str], **options: Any) -> subprocess.CompletedProcess[bytes]:
        self.command = command
        self.options = options
        if self._error is not None:
            raise self._error
        captured = options["stdout"] == subprocess.PIPE
        return subprocess.CompletedProcess(
            command,
            self._returncode,
            self._stdout if captured else None,
            self._stderr if captured else None,
        )


def install(monkeypatch: pytest.MonkeyPatch, fake: FakeRun) -> FakeRun:
    monkeypatch.setattr(subprocess, "run", fake)
    return fake


def test_run_targets_device_by_serial(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = install(monkeypatch, FakeRun(stdout=b"device\n"))

    output = AdbClient("adb", serial="emulator-5554", command_timeout=5).run("get-state")

    assert output == b"device\n"
    assert fake.command == ["adb", "-s", "emulator-5554", "get-state"]
    assert fake.options["timeout"] == 5
    assert fake.options["stdin"] == subprocess.DEVNULL


def test_shell_passes_quoted_command_and_decodes_output(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = install(monkeypatch, FakeRun(stdout=b"a b\n"))

    output = AdbClient("adb").shell("echo", "a b")

    assert output == "a b\n"
    assert fake.command == ["adb", "shell", "echo 'a b'"]


def test_exec_out_returns_raw_bytes(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = install(monkeypatch, FakeRun(stdout=b"\x89PNG\r\n\x1a\n"))

    output = AdbClient("adb").exec_out("screencap", "-p")

    assert output == b"\x89PNG\r\n\x1a\n"
    assert fake.command == ["adb", "exec-out", "screencap -p"]


def test_start_server_discards_output_and_ignores_serial(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = install(monkeypatch, FakeRun())

    AdbClient("adb", serial="emulator-5554").start_server()

    assert fake.command == ["adb", "start-server"]
    assert fake.options["stdout"] == subprocess.DEVNULL
    assert fake.options["stderr"] == subprocess.DEVNULL


def test_non_zero_exit_code_raises_command_error(monkeypatch: pytest.MonkeyPatch) -> None:
    install(monkeypatch, FakeRun(returncode=1, stderr=b"adb: no devices/emulators found\n"))

    with pytest.raises(AdbCommandError, match="exit code 1") as error:
        AdbClient("adb").run("get-state")

    assert error.value.returncode == 1
    assert error.value.output == "adb: no devices/emulators found"


def test_missing_executable_raises_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    install(monkeypatch, FakeRun(error=FileNotFoundError(2, "No such file or directory")))

    with pytest.raises(AdbNotFoundError, match="/opt/adb"):
        AdbClient("/opt/adb").run("get-state")


def test_hanging_command_raises_timeout_error(monkeypatch: pytest.MonkeyPatch) -> None:
    install(monkeypatch, FakeRun(error=subprocess.TimeoutExpired(["adb"], 20)))

    with pytest.raises(AdbTimeoutError, match="timed out"):
        AdbClient("adb").run("get-state")
