# Author: Johnny Chou
# Email: johnny071531@gmail.com
# PyPI: https://pypi.org/project/huskium/
# GitHub: https://github.com/uujohnnyuu/huskium


from __future__ import annotations

from typing import Type

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from ..base.elements import Elements as BaseElements
from .by import ByAttr
from .page import Page
from ..appium.page import Page as AppiumPage


class Elements(BaseElements[Page, WebDriver, WebElement]):

    def _verify_by(self, by: str | None):
        if by not in ByAttr.OPTIONAL_VALUES:
            raise ValueError(f'The set "by" strategy "{by}" is invalid, please refer to "selenium By".')

    def _verify_instance(self, instance: Page | AppiumPage):
        if not isinstance(instance, Page | AppiumPage):
            raise TypeError(
                f'"selenium Element" must be used in "selenium Page" or "appium Page", not {type(instance).__name__}'
            )
    
    def _verify_owner(self, owner: Type[Page | AppiumPage]):
        if not issubclass(owner, Page | AppiumPage):
            raise TypeError(
                f'"selenium Element" must be used in "selenium Page" or "appium Page", not {type(owner).__name__}'
            )

    def _verify_set_value(self, value: Elements):
        if not isinstance(value, Elements):
            raise TypeError(f'Assigned value must be "selenium Elements", got {type(value).__name__}.')