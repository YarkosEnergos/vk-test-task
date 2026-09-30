import os
import shutil
from pathlib import Path

from green_button.infrastructure.adb.errors import AdbNotFoundError

_SDK_ROOT_VARIABLES = ("ANDROID_HOME", "ANDROID_SDK_ROOT")
_EXECUTABLE_NAME = "adb.exe" if os.name == "nt" else "adb"


def locate_adb(explicit_path: str | None = None) -> str:
    if explicit_path:
        return explicit_path
    if found := shutil.which("adb"):
        return found
    for variable in _SDK_ROOT_VARIABLES:
        sdk_root = os.environ.get(variable)
        if sdk_root and (candidate := Path(sdk_root) / "platform-tools" / _EXECUTABLE_NAME).is_file():
            return str(candidate)
    raise AdbNotFoundError(
        "adb executable not found in PATH, $ANDROID_HOME or $ANDROID_SDK_ROOT; "
        "install Android SDK Platform-Tools or specify the path to adb explicitly"
    )
