import logging
from dataclasses import dataclass

from green_button.application.ports import ButtonDetector, Clock, Device
from green_button.domain.errors import AppNotInstalledError
from green_button.domain.models import Button, PackageName
from green_button.domain.selection import select_target

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 10.0
DEFAULT_POLL_INTERVAL = 0.5


@dataclass(frozen=True, slots=True)
class TapResult:
    button: Button | None
    attempts: int
    elapsed: float

    @property
    def tapped(self) -> bool:
        return self.button is not None


class TapGreenButtonUseCase:
    def __init__(
        self,
        device: Device,
        detector: ButtonDetector,
        clock: Clock,
        poll_interval: float = DEFAULT_POLL_INTERVAL,
    ) -> None:
        self._device = device
        self._detector = detector
        self._clock = clock
        self._poll_interval = poll_interval

    def execute(
        self,
        package: PackageName,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        restart: bool = True,
    ) -> TapResult:
        self._device.connect()
        if not self._device.is_installed(package):
            raise AppNotInstalledError(str(package))
        self._device.wake_up()
        if restart:
            self._device.stop_app(package)
        self._device.launch_app(package)
        logger.info("Launched %s, waiting up to %g s for a green button", package, timeout)

        result = self._wait_for_button(timeout)
        if result.button is not None:
            self._device.tap(result.button.center)
            logger.info("Tapped %s", result.button)
        return result

    def _wait_for_button(self, timeout: float) -> TapResult:
        started = self._clock.monotonic()
        deadline = started + timeout
        attempts = 0
        while True:
            attempts += 1
            candidates = self._detector.detect(self._device.take_screenshot())
            button = select_target(candidates)
            now = self._clock.monotonic()
            logger.debug(
                "Attempt %d at %.2f s: %d candidate(s) %s",
                attempts,
                now - started,
                len(candidates),
                candidates,
            )
            if button is not None or now >= deadline:
                return TapResult(button=button, attempts=attempts, elapsed=now - started)
            self._clock.sleep(min(self._poll_interval, deadline - now))
