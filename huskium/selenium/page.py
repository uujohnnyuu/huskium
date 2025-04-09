# Author: Johnny Chou
# Email: johnny071531@gmail.com
# PyPI: https://pypi.org/project/huskium/
# GitHub: https://github.com/uujohnnyuu/huskium


from __future__ import annotations

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from ..base.page import Page as BasePage


class Page(BasePage[WebDriver, WebElement]):

    def _verify_driver(self, driver: WebDriver):
        if type(driver) is not WebDriver:
            raise TypeError(f'The "driver" must be exactly "selenium WebDriver", got {type(driver).__name__}.')
