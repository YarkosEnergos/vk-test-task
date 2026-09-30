from collections.abc import Sequence

from green_button.domain.models import BoundingBox, Button, PackageName, Point


def make_button(x: int, y: int, width: int, height: int) -> Button:
    return Button(BoundingBox(x, y, width, height))


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0
        self.sleeps: list[float] = []

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


class FakeDevice:
    def __init__(
        self,
        clock: FakeClock,
        screenshots: Sequence[bytes] = (b"screenshot",),
        *,
        installed: bool = True,
        screenshot_duration: float = 0.0,
    ) -> None:
        self._clock = clock
        self._screenshots = list(screenshots)
        self._installed = installed
        self._screenshot_duration = screenshot_duration
        self.screenshots_taken = 0
        self.calls: list[str] = []

    def connect(self) -> None:
        self.calls.append("connect")

    def is_installed(self, package: PackageName) -> bool:
        self.calls.append(f"is_installed {package}")
        return self._installed

    def wake_up(self) -> None:
        self.calls.append("wake_up")

    def stop_app(self, package: PackageName) -> None:
        self.calls.append(f"stop_app {package}")

    def launch_app(self, package: PackageName) -> None:
        self.calls.append(f"launch_app {package}")

    def take_screenshot(self) -> bytes:
        self.calls.append("take_screenshot")
        self._clock.now += self._screenshot_duration
        screenshot = self._screenshots[min(self.screenshots_taken, len(self._screenshots) - 1)]
        self.screenshots_taken += 1
        return screenshot

    def tap(self, point: Point) -> None:
        self.calls.append(f"tap {point.x} {point.y}")


class ScriptedDetector:
    def __init__(self, *results: list[Button]) -> None:
        self._results = list(results) or [[]]
        self.calls = 0

    def detect(self, screenshot: bytes) -> list[Button]:
        result = self._results[min(self.calls, len(self._results) - 1)]
        self.calls += 1
        return result
