from green_button.application.tap_green_button import TapGreenButtonUseCase
from green_button.infrastructure.adb.client import AdbClient
from green_button.infrastructure.adb.device import AdbDevice
from green_button.infrastructure.adb.locator import locate_adb
from green_button.infrastructure.clock import SystemClock
from green_button.infrastructure.vision.green_button_detector import OpenCvGreenButtonDetector


def build_use_case(adb_path: str | None = None, serial: str | None = None) -> TapGreenButtonUseCase:
    client = AdbClient(locate_adb(adb_path), serial=serial)
    return TapGreenButtonUseCase(
        device=AdbDevice(client),
        detector=OpenCvGreenButtonDetector(),
        clock=SystemClock(),
    )
