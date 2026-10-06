import cv2
import numpy as np

from detector import find_green_button

WHITE = (255, 255, 255)
GREEN = (80, 175, 76)
RED = (54, 67, 244)


def screen(*buttons: tuple[int, int, int, int, tuple[int, int, int]]) -> bytes:
    image = np.full((1280, 720, 3), WHITE, dtype=np.uint8)
    for x, y, width, height, color in buttons:
        cv2.rectangle(image, (x, y), (x + width - 1, y + height - 1), color, cv2.FILLED)
        cv2.putText(image, "OK", (x + 20, y + height // 2), cv2.FONT_HERSHEY_SIMPLEX, 1.2, WHITE, 3)
    return cv2.imencode(".png", image)[1].tobytes()


def test_finds_center_of_green_button() -> None:
    assert find_green_button(screen((100, 600, 400, 120, GREEN))) == (300, 660)


def test_ignores_buttons_of_other_colors() -> None:
    assert find_green_button(screen((100, 600, 400, 120, RED))) is None


def test_picks_green_button_among_others() -> None:
    assert find_green_button(screen((100, 300, 400, 120, RED), (100, 800, 400, 120, GREEN))) == (300, 860)
