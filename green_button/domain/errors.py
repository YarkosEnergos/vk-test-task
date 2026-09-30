class GreenButtonError(Exception):
    pass


class InvalidPackageNameError(GreenButtonError, ValueError):
    def __init__(self, value: str) -> None:
        super().__init__(f"invalid Android package name: {value!r}")
        self.value = value


class InvalidScreenshotError(GreenButtonError):
    pass


class DeviceError(GreenButtonError):
    pass


class DeviceUnavailableError(DeviceError):
    pass


class AppNotInstalledError(DeviceError):
    def __init__(self, package: str) -> None:
        super().__init__(f"package {package} is not installed on the device")
        self.package = package


class AppLaunchError(DeviceError):
    pass
