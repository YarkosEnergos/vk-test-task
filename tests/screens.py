from collections.abc import Sequence
from typing import Self

import cv2
import numpy as np

WIDTH = 720
HEIGHT = 1280

WHITE = "#FFFFFF"
GREEN = "#4CAF50"
RED = "#F44336"
BLUE = "#2196F3"


def bgr(color: str) -> tuple[int, int, int]:
    value = color.removeprefix("#")
    red, green, blue = (int(value[offset : offset + 2], 16) for offset in (0, 2, 4))
    return blue, green, red


class Screen:
    def __init__(self, background: str = WHITE, width: int = WIDTH, height: int = HEIGHT) -> None:
        self.image = np.full((height, width, 3), bgr(background), dtype=np.uint8)

    def rectangle(self, x: int, y: int, width: int, height: int, color: str, thickness: int = cv2.FILLED) -> Self:
        cv2.rectangle(self.image, (x, y), (x + width - 1, y + height - 1), bgr(color), thickness)
        return self

    def button(self, x: int, y: int, width: int, height: int, color: str, label: str = "OK") -> Self:
        self.rectangle(x, y, width, height, color)
        return self.text(label, x + width // 4, y + height // 2 + 12, WHITE)

    def pill(self, x: int, y: int, width: int, height: int, color: str) -> Self:
        radius = height // 2
        self.rectangle(x + radius, y, width - 2 * radius, height, color)
        self.circle(x + radius, y + radius, radius, color)
        return self.circle(x + width - radius - 1, y + radius, radius, color)

    def circle(self, center_x: int, center_y: int, radius: int, color: str) -> Self:
        cv2.circle(self.image, (center_x, center_y), radius, bgr(color), cv2.FILLED, cv2.LINE_AA)
        return self

    def polygon(self, points: Sequence[tuple[int, int]], color: str) -> Self:
        cv2.fillPoly(self.image, [np.array(points, dtype=np.int32)], bgr(color), cv2.LINE_AA)
        return self

    def text(self, text: str, x: int, y: int, color: str, scale: float = 1.2, thickness: int = 3) -> Self:
        cv2.putText(self.image, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, bgr(color), thickness, cv2.LINE_AA)
        return self

    def png(self, with_alpha: bool = False) -> bytes:
        image = cv2.cvtColor(self.image, cv2.COLOR_BGR2BGRA) if with_alpha else self.image
        encoded, data = cv2.imencode(".png", image)
        assert encoded
        return data.tobytes()
