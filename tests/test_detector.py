import pytest

from green_button.domain.errors import InvalidScreenshotError
from green_button.domain.models import BoundingBox, Button, Point
from green_button.infrastructure.vision.green_button_detector import OpenCvGreenButtonDetector
from tests.screens import BLUE, GREEN, RED, WHITE, WIDTH, Screen


def detect(screen: Screen) -> list[Button]:
    return OpenCvGreenButtonDetector().detect(screen.png())


def assert_near(actual: Point, expected: Point, tolerance: int = 2) -> None:
    assert abs(actual.x - expected.x) <= tolerance
    assert abs(actual.y - expected.y) <= tolerance


def test_detects_green_button_with_label() -> None:
    buttons = detect(Screen().button(160, 600, 400, 120, GREEN, "PRESS"))

    assert buttons == [Button(BoundingBox(160, 600, 400, 120))]


@pytest.mark.parametrize("color", ["#4CAF50", "#8BC34A", "#81C784", "#2E7D32", "#1B5E20", "#00C853", "#00FF00"])
def test_detects_common_green_shades(color: str) -> None:
    buttons = detect(Screen().button(100, 500, 520, 140, color, "Continue"))

    assert [button.bounds for button in buttons] == [BoundingBox(100, 500, 520, 140)]


def test_detects_green_button_on_dark_background() -> None:
    buttons = detect(Screen(background="#121212").button(100, 500, 520, 140, "#81C995", "Next"))

    assert [button.bounds for button in buttons] == [BoundingBox(100, 500, 520, 140)]


def test_detects_round_button_with_icon() -> None:
    screen = Screen().circle(360, 900, 84, GREEN).text("+", 335, 925, WHITE, scale=2.0, thickness=6)

    [button] = detect(screen)

    assert_near(button.center, Point(360, 900))


def test_detects_pill_shaped_button() -> None:
    [button] = detect(Screen().pill(100, 1000, 520, 130, GREEN).text("Buy", 310, 1080, WHITE))

    assert_near(button.center, Point(360, 1065))


def test_detects_every_green_button() -> None:
    screen = Screen().button(60, 300, 600, 140, GREEN, "Big").button(60, 600, 280, 120, GREEN, "Small")

    buttons = detect(screen)

    assert sorted(button.bounds.y for button in buttons) == [300, 600]


def test_detects_only_green_among_colored_buttons() -> None:
    screen = (
        Screen()
        .button(60, 200, 600, 140, RED, "Cancel")
        .button(60, 450, 600, 140, BLUE, "Details")
        .button(60, 700, 600, 140, GREEN, "Confirm")
    )

    assert [button.bounds for button in detect(screen)] == [BoundingBox(60, 700, 600, 140)]


def test_accepts_screenshot_with_alpha_channel() -> None:
    png = Screen().button(160, 600, 400, 120, GREEN).png(with_alpha=True)

    assert len(OpenCvGreenButtonDetector().detect(png)) == 1


@pytest.mark.parametrize(
    "color",
    [RED, BLUE, "#FFEB3B", "#009688", "#9E9E9E", "#000000"],
    ids=["red", "blue", "yellow", "teal", "grey", "black"],
)
def test_ignores_non_green_buttons(color: str) -> None:
    assert detect(Screen().button(100, 500, 520, 140, color)) == []


def test_ignores_screen_without_buttons() -> None:
    assert detect(Screen()) == []


def test_ignores_small_green_elements() -> None:
    screen = Screen().circle(100, 100, 12, GREEN).rectangle(300, 300, 30, 30, GREEN)

    assert detect(screen) == []


def test_ignores_thin_green_line() -> None:
    assert detect(Screen().rectangle(60, 700, 600, 8, GREEN)) == []


def test_ignores_outlined_green_frame() -> None:
    screen = Screen().rectangle(100, 500, 520, 140, GREEN, thickness=4).text("Outlined", 150, 580, GREEN)

    assert detect(screen) == []


def test_ignores_green_ring() -> None:
    assert detect(Screen().circle(360, 640, 80, GREEN).circle(360, 640, 50, WHITE)) == []


def test_ignores_green_text() -> None:
    assert detect(Screen().text("Welcome back!", 40, 400, GREEN, scale=2.0, thickness=5)) == []


def test_ignores_full_width_green_bar() -> None:
    screen = Screen().rectangle(0, 0, WIDTH, 160, GREEN).text("Title", 40, 100, WHITE)

    assert detect(screen) == []


def test_ignores_full_screen_green_background() -> None:
    assert detect(Screen(background=GREEN)) == []


@pytest.mark.parametrize(
    "points",
    [
        [(100, 100), (400, 100), (400, 200), (200, 200), (200, 500), (100, 500)],
        [(300, 700), (500, 800), (300, 900)],
    ],
    ids=["l-shape", "triangle"],
)
def test_ignores_non_button_shapes(points: list[tuple[int, int]]) -> None:
    assert detect(Screen().polygon(points, GREEN)) == []


@pytest.mark.parametrize("data", [b"", b"not an image"], ids=["empty", "garbage"])
def test_rejects_undecodable_screenshot(data: bytes) -> None:
    with pytest.raises(InvalidScreenshotError):
        OpenCvGreenButtonDetector().detect(data)
