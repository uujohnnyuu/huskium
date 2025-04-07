# Author: Johnny Chou
# Email: johnny071531@gmail.com
# PyPI: https://pypi.org/project/huskium/
# GitHub: https://github.com/uujohnnyuu/huskium


"""
Expected Conditions Extension (ECEX)

Overview:
    ECEX extends official `expected_conditions (EC)` module.

Locator Handling:
    The `locator` follows the same structure as `EC`.

Index Feature:
    The `index` allows using the `find_elements(*locator)[index]` pattern.
    If `index` is `None`, `find_element(*locator)` is used instead.

Exception Handling:
    ECEX separates methods for locators and WebElements to enable more robust
    exception handling.
"""


from __future__ import annotations

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from ..base.ecex import ECEX as BaseECEX


class ECEX(BaseECEX[WebDriver, WebElement]):
    pass