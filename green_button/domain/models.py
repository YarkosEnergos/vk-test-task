import re
from dataclasses import dataclass

from green_button.domain.errors import InvalidPackageNameError

_PACKAGE_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+")


@dataclass(frozen=True, slots=True)
class PackageName:
    value: str

    def __post_init__(self) -> None:
        if not _PACKAGE_NAME.fullmatch(self.value):
            raise InvalidPackageNameError(self.value)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class Point:
    x: int
    y: int


@dataclass(frozen=True, slots=True)
class BoundingBox:
    x: int
    y: int
    width: int
    height: int

    @property
    def area(self) -> int:
        return self.width * self.height

    @property
    def center(self) -> Point:
        return Point(self.x + self.width // 2, self.y + self.height // 2)


@dataclass(frozen=True, slots=True)
class Button:
    bounds: BoundingBox

    @property
    def center(self) -> Point:
        return self.bounds.center
