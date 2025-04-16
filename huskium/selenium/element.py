# Author: Johnny Chou
# Email: johnny071531@gmail.com
# PyPI: https://pypi.org/project/huskium/
# GitHub: https://github.com/uujohnnyuu/huskium


from __future__ import annotations

from typing import Any

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from ..generic import Element as GenericElement
from .by import ByAttr


class Element(GenericElement[WebDriver, WebElement]):

    def _verify_by(self, by: Any) -> None:
        if by not in ByAttr.OPTIONAL_VALUES:
            raise ValueError(f'Invalid "by": "{by}". Use values from "By" (from huskium.selenium import By).')

    def _verify_set_value(self, value: Any) -> None:
        if not isinstance(value, Element):
            raise TypeError(f'Assigned value must be "selenium Element", got {type(value).__name__}.')
