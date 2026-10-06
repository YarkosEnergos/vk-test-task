import subprocess

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
COMMAND_TIMEOUT = 30


class AdbError(Exception):
    pass


def run(*args: str) -> bytes:
    try:
        result = subprocess.run(["adb", *args], capture_output=True, timeout=COMMAND_TIMEOUT)
    except FileNotFoundError:
        raise AdbError("adb not found: install Android SDK Platform-Tools and add adb to PATH") from None
    except subprocess.TimeoutExpired:
        raise AdbError(f"adb {' '.join(args)} timed out after {COMMAND_TIMEOUT} s") from None
    if result.returncode != 0:
        message = result.stderr.decode(errors="replace").strip()
        raise AdbError(message or f"adb {' '.join(args)} exited with code {result.returncode}")
    return result.stdout


def launch_app(package: str) -> None:
    output = run("shell", "monkey", "-p", package, "-c", "android.intent.category.LAUNCHER", "1")
    if b"monkey aborted" in output:
        raise AdbError(f"cannot launch {package}: app is not installed or has no launcher activity")


def take_screenshot() -> bytes:
    data = run("exec-out", "screencap", "-p")
    if not data.startswith(PNG_SIGNATURE):
        raise AdbError("device returned an invalid screenshot")
    return data


def tap(x: int, y: int) -> None:
    run("shell", "input", "tap", str(x), str(y))
