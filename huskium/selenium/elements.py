# Author: Johnny Chou
# Email: johnny071531@gmail.com
# PyPI: https://pypi.org/project/huskium/
# GitHub: https://github.com/uujohnnyuu/huskium

# NOTE
# We do not implement a cache mechanism in Elements, for obvious reasons.
# The state of multiple elements is unpredictable,
# and caching may not improve performance.
# To ensure stability, elements are re-located on every method call.


from __future__ import annotations

from typing import Any

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from ..generic import Elements as GenericElements
from .by import ByAttr


class Elements(GenericElements[WebDriver, WebElement]):

    def _verify_by(self, by: Any) -> None:
        if by not in ByAttr.OPTIONAL_VALUES:
            raise ValueError(f'Invalid "by": "{by}". Use values from "By" (from huskium.selenium import By).')

    def _verify_set_value(self, value: Any) -> None:
        if not isinstance(value, Elements):
            raise TypeError(f'Assigned value must be "selenium Elements", got {type(value).__name__}.')
