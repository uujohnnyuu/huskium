# Author: Johnny Chou
# Email: johnny071531@gmail.com
# PyPI: https://pypi.org/project/huskium/
# GitHub: https://github.com/uujohnnyuu/huskium


from __future__ import annotations

from typing import Type

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from ..base.element import Element as BaseElement
from ..appium.page import Page as AppiumPage
from .by import ByAttr
from .page import Page


class Element(BaseElement[Page, WebDriver, WebElement]):

    def _verify_by(self, by: str | None):
        if by not in ByAttr.OPTIONAL_VALUES:
            raise ValueError(f'Invalid "by": "{by}". Use values from "By" (from huskium.selenium import By).')

    def _verify_instance(self, instance: Page | AppiumPage):
        if not isinstance(instance, Page | AppiumPage):
            raise TypeError(
                f'"selenium Element" must be used in "selenium Page" or "appium Page", got {type(instance).__name__}'
            )

    def _verify_owner(self, owner: Type[Page | AppiumPage]):
        if not issubclass(owner, Page | AppiumPage):
            raise TypeError(
                f'"selenium Element" must be used in "selenium Page" or "appium Page", got {type(owner).__name__}'
            )

    def _verify_set_value(self, value: Element):
        if not isinstance(value, Element):
            raise TypeError(f'Assigned value must be "selenium Element", got {type(value).__name__}.')
