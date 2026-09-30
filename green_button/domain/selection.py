from collections.abc import Iterable

from green_button.domain.models import Button


def select_target(candidates: Iterable[Button]) -> Button | None:
    return max(candidates, key=lambda button: button.bounds.area, default=None)
