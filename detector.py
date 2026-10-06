import cv2
import numpy as np

LOWER_GREEN = np.array([35, 80, 60], dtype=np.uint8)
UPPER_GREEN = np.array([85, 255, 255], dtype=np.uint8)
MIN_AREA_RATIO = 0.002
MIN_EXTENT = 0.7


def find_green_button(png: bytes) -> tuple[int, int] | None:
    image = cv2.imdecode(np.frombuffer(png, dtype=np.uint8), cv2.IMREAD_COLOR)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, LOWER_GREEN, UPPER_GREEN)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), dtype=np.uint8))
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    screen_height, screen_width = mask.shape
    best_area = MIN_AREA_RATIO * screen_width * screen_height
    best_center = None
    for contour in contours:
        x, y, width, height = cv2.boundingRect(contour)
        area = cv2.contourArea(contour)
        if width >= screen_width or area < MIN_EXTENT * width * height or area < best_area:
            continue
        best_area = area
        best_center = (x + width // 2, y + height // 2)
    return best_center
