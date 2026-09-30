import logging
import shlex
import subprocess

from green_button.infrastructure.adb.errors import (
    AdbCommandError,
    AdbNotFoundError,
    AdbTimeoutError,
)

logger = logging.getLogger(__name__)

DEFAULT_COMMAND_TIMEOUT = 20.0


class AdbClient:
    def __init__(
        self,
        executable: str,
        serial: str | None = None,
        command_timeout: float = DEFAULT_COMMAND_TIMEOUT,
    ) -> None:
        self._executable = executable
        self._serial = serial
        self._command_timeout = command_timeout

    def start_server(self) -> None:
        self._execute([self._executable, "start-server"], capture_output=False)

    def run(self, *args: str) -> bytes:
        return self._execute([self._executable, *self._target_args(), *args], capture_output=True)

    def shell(self, *args: str) -> str:
        return self.run("shell", shlex.join(args)).decode("utf-8", errors="replace")

    def exec_out(self, *args: str) -> bytes:
        return self.run("exec-out", shlex.join(args))

    def _target_args(self) -> list[str]:
        return ["-s", self._serial] if self._serial else []

    def _execute(self, command: list[str], *, capture_output: bool) -> bytes:
        logger.debug("Running %s", shlex.join(command))
        stream = subprocess.PIPE if capture_output else subprocess.DEVNULL
        try:
            completed = subprocess.run(
                command,
                stdin=subprocess.DEVNULL,
                stdout=stream,
                stderr=stream,
                timeout=self._command_timeout,
                check=False,
            )
        except OSError as exc:
            raise AdbNotFoundError(f"cannot run adb executable {self._executable!r}: {exc.strerror or exc}") from exc
        except subprocess.TimeoutExpired as exc:
            raise AdbTimeoutError(f"`{shlex.join(command)}` timed out after {self._command_timeout:g} s") from exc
        if completed.returncode != 0:
            raise AdbCommandError(command, completed.returncode, _collect_output(completed))
        return completed.stdout or b""


def _collect_output(completed: subprocess.CompletedProcess[bytes]) -> str:
    streams = (completed.stderr, completed.stdout)
    parts = (stream.decode("utf-8", errors="replace").strip() for stream in streams if stream)
    return " | ".join(part for part in parts if part)
