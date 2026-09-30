from dataclasses import dataclass

import cv2
import numpy as np
from cv2.typing import MatLike

from green_button.domain.errors import InvalidScreenshotError
from green_button.domain.models import BoundingBox, Button


@dataclass(frozen=True, slots=True)
class DetectionSettings:
    hue_range: tuple[int, int] = (35, 85)
    min_saturation: int = 80
    min_value: int = 60
    min_area_ratio: float = 0.002
    max_area_ratio: float = 0.5
    min_side_ratio: float = 0.03
    max_aspect_ratio: float = 12.0
    min_extent: float = 0.7
    min_solidity: float = 0.9
    min_fill_ratio: float = 0.7
    closing_kernel_size: int = 5


class OpenCvGreenButtonDetector:
    def __init__(self, settings: DetectionSettings | None = None) -> None:
        self._settings = settings or DetectionSettings()
        size = self._settings.closing_kernel_size
        self._kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size))

    def detect(self, screenshot: bytes) -> list[Button]:
        green = self._green_mask(_decode(screenshot))
        regions = cv2.morphologyEx(green, cv2.MORPH_CLOSE, self._kernel)
        contours, _ = cv2.findContours(regions, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        buttons = (self._to_button(contour, green) for contour in contours)
        return [button for button in buttons if button is not None]

    def _green_mask(self, image: MatLike) -> MatLike:
        settings = self._settings
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        lower = np.array([settings.hue_range[0], settings.min_saturation, settings.min_value], dtype=np.uint8)
        upper = np.array([settings.hue_range[1], 255, 255], dtype=np.uint8)
        return cv2.inRange(hsv, lower, upper)

    def _to_button(self, contour: MatLike, green: MatLike) -> Button | None:
        bounds = BoundingBox(*cv2.boundingRect(contour))
        if self._is_button_shaped(contour, bounds, green.shape) and self._is_filled(contour, bounds, green):
            return Button(bounds)
        return None

    def _is_button_shaped(self, contour: MatLike, bounds: BoundingBox, screen_shape: tuple[int, ...]) -> bool:
        settings = self._settings
        screen_height, screen_width = screen_shape[:2]
        screen_area = screen_width * screen_height
        area = cv2.contourArea(contour)
        hull_area = cv2.contourArea(cv2.convexHull(contour))
        short_side, long_side = sorted((bounds.width, bounds.height))
        return (
            settings.min_area_ratio * screen_area <= area <= settings.max_area_ratio * screen_area
            and short_side >= settings.min_side_ratio * min(screen_width, screen_height)
            and long_side <= settings.max_aspect_ratio * short_side
            and bounds.width < screen_width
            and area >= settings.min_extent * bounds.area
            and area >= settings.min_solidity * hull_area
        )

    def _is_filled(self, contour: MatLike, bounds: BoundingBox, green: MatLike) -> bool:
        shape = np.zeros((bounds.height, bounds.width), dtype=np.uint8)
        cv2.drawContours(shape, [contour], -1, 255, thickness=cv2.FILLED, offset=(-bounds.x, -bounds.y))
        inside = shape > 0
        window = green[bounds.y : bounds.y + bounds.height, bounds.x : bounds.x + bounds.width]
        fill_ratio = int(np.count_nonzero(window[inside])) / max(int(np.count_nonzero(inside)), 1)
        return fill_ratio >= self._settings.min_fill_ratio


def _decode(screenshot: bytes) -> MatLike:
    buffer = np.frombuffer(screenshot, dtype=np.uint8)
    image = cv2.imdecode(buffer, cv2.IMREAD_COLOR) if buffer.size else None
    if image is None:
        raise InvalidScreenshotError("screenshot cannot be decoded as an image")
    return image
