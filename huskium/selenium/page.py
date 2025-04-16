# Author: Johnny Chou
# Email: johnny071531@gmail.com
# PyPI: https://pypi.org/project/huskium/
# GitHub: https://github.com/uujohnnyuu/huskium


from __future__ import annotations

from typing import Any

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from appium.webdriver.webdriver import WebDriver as AppiumWebDriver

from ..generic import Page as GenericPage


class Page(GenericPage[WebDriver, WebElement]):
    
    def _verify_driver(self, driver: Any) -> None:
        if not isinstance(driver, WebDriver):
            raise TypeError(f'The "driver" must be "selenium WebDriver", got {type(driver).__name__}.')
        if isinstance(driver, AppiumWebDriver):
            raise TypeError('The "driver" must be "selenium WebDriver", got "appium WebDriver".')
