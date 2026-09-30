import shlex
from collections.abc import Sequence

from green_button.domain.errors import DeviceError


class AdbError(DeviceError):
    pass


class AdbNotFoundError(AdbError):
    pass


class AdbTimeoutError(AdbError):
    pass


class AdbCommandError(AdbError):
    def __init__(self, command: Sequence[str], returncode: int, output: str) -> None:
        super().__init__(f"`{shlex.join(command)}` failed with exit code {returncode}: {output or 'no output'}")
        self.command = tuple(command)
        self.returncode = returncode
        self.output = output
