import pytest

from green_button.domain.errors import InvalidPackageNameError
from green_button.domain.models import BoundingBox, PackageName, Point
from green_button.domain.selection import select_target
from tests.fakes import make_button


@pytest.mark.parametrize("value", ["com.example.app", "ru.vk.store", "com.example.my_app2", "A.b"])
def test_package_name_accepts_valid_names(value: str) -> None:
    assert str(PackageName(value)) == value


@pytest.mark.parametrize(
    "value",
    [
        "",
        "com",
        "com.",
        ".com",
        "com..app",
        "1com.app",
        "com.1app",
        "com._app",
        "com.example-app",
        "com.example app",
        "com.example;reboot",
    ],
)
def test_package_name_rejects_invalid_names(value: str) -> None:
    with pytest.raises(InvalidPackageNameError):
        PackageName(value)


def test_bounding_box_area_and_center() -> None:
    box = BoundingBox(x=100, y=200, width=301, height=100)

    assert box.area == 30100
    assert box.center == Point(250, 250)


def test_select_target_prefers_largest_button() -> None:
    small = make_button(0, 0, 100, 100)
    large = make_button(0, 200, 400, 150)
    medium = make_button(0, 400, 200, 100)

    assert select_target([small, large, medium]) == large


def test_select_target_returns_none_without_candidates() -> None:
    assert select_target([]) is None
