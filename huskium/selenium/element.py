# Author: Johnny Chou
# Email: johnny071531@gmail.com
# PyPI: https://pypi.org/project/huskium/
# GitHub: https://github.com/uujohnnyuu/huskium


from __future__ import annotations

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from ..base.element import Element as BaseElement
from .by import ByAttr
from .page import Page


class Element(BaseElement[Page, WebDriver, WebElement]):
    
    def _verify_by(self, by: str | None):
        if by not in ByAttr.OPTIONAL_VALUES:
            raise ValueError(f'The set "by" strategy "{by}" is invalid, please refer to "selenium By".')