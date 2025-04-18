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


from typing import Callable, Literal

from appium.webdriver.webdriver import WebDriver
from appium.webdriver.webelement import WebElement

from ..selenium import GenericECEX


class ECEX(GenericECEX[WebDriver, WebElement]):

    @staticmethod
    def webview_is_present(
        switch: bool = True,
        index: int = -1
    ) -> Callable[[WebDriver], str | Literal[False]]:
        """
        Whether `WEBVIEW` context is present.

        Args:
            switch: Switch to the `WEBVIEW` context
                when it exists and `switch` is `True`.
            index: Switch to the specified context index,
                defaulting to the most recently appeared.

        Returns:
            (str | False):
                Current context `str` when a `WEBVIEW` exists;
                otherwise, `False` when no `WEBVIEW` exists.
        """

        def _predicate(driver: WebDriver):
            contexts = driver.contexts
            if any('WEBVIEW' in context for context in contexts):
                if switch:
                    driver.switch_to.context(contexts[index])
                return driver.context
            return False

        return _predicate
