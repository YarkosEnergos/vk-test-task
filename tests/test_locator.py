import shutil
from pathlib import Path

import pytest

from green_button.infrastructure.adb.errors import AdbNotFoundError
from green_button.infrastructure.adb.locator import locate_adb


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(shutil, "which", lambda name: None)
    monkeypatch.delenv("ANDROID_HOME", raising=False)
    monkeypatch.delenv("ANDROID_SDK_ROOT", raising=False)


def make_sdk(root: Path) -> Path:
    platform_tools = root / "platform-tools"
    platform_tools.mkdir(parents=True)
    for name in ("adb", "adb.exe"):
        (platform_tools / name).touch()
    return root


def test_prefers_explicit_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(shutil, "which", lambda name: "/usr/bin/adb")

    assert locate_adb("/opt/platform-tools/adb") == "/opt/platform-tools/adb"


def test_uses_adb_from_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(shutil, "which", lambda name: "/usr/bin/adb")

    assert locate_adb() == "/usr/bin/adb"


@pytest.mark.parametrize("variable", ["ANDROID_HOME", "ANDROID_SDK_ROOT"])
def test_falls_back_to_android_sdk(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, variable: str) -> None:
    monkeypatch.setenv(variable, str(make_sdk(tmp_path)))

    assert Path(locate_adb()).parent == tmp_path / "platform-tools"


def test_raises_when_adb_is_missing() -> None:
    with pytest.raises(AdbNotFoundError, match="Platform-Tools"):
        locate_adb()
