# Author: Johnny Chou
# Email: johnny071531@gmail.com
# PyPI: https://pypi.org/project/huskium/
# GitHub: https://github.com/uujohnnyuu/huskium


from __future__ import annotations

from appium.webdriver.common.appiumby import AppiumBy


class By(AppiumBy):
    """All Selenium `By` and Appium `AppiumBy` methods."""
    pass


class ByAttribute:
    """
    Mainly used for internal validation of `By`.
    It can also be used to check the available `By` attributes
    in your current Selenium and Appium version.
    """

    NAMES = [attr for attr in dir(By) if not attr.startswith('__')]
    """A list of all `By` attribute names as strings."""

    VALUES = [getattr(By, attr) for attr in NAMES]
    """A list of all `By` attribute values."""

    VALUES_WITH_NONE = VALUES + [None]
    """A list of `VALUES`, including `None`."""
