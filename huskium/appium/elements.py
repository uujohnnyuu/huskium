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

from appium.webdriver.webdriver import WebDriver
from appium.webdriver.webelement import WebElement

from ..selenium import GenericElements
from .by import ByAttr
from .page import Page


class Elements(GenericElements[WebDriver, WebElement]):

    page: Page

    def _verify_by(self, by: Any) -> None:
        if by not in ByAttr.OPTIONAL_VALUES:
            raise ValueError(f'Invalid "by": "{by}". Use values from "By" (from huskium.appium import By).')

    def _verify_descriptor_instance(self, instance: Any) -> None:
        if not isinstance(instance, Page):
            raise TypeError(
                f'"appium Elements" must be used in "appium Page", got {type(instance).__name__}'
            )

    def _verify_descriptor_owner(self, owner: Any) -> None:
        if not issubclass(owner, Page):
            raise TypeError(
                f'"appium Elements" must be used in "appium Page", got {type(owner).__name__}'
            )

    def _verify_descriptor_value(self, value: Any) -> None:
        if not isinstance(value, Elements):
            raise TypeError(f'Assigned value must be "appium Elements", got {type(value).__name__}.')

    @property
    def locations_in_view(self) -> list[dict[str, int]]:
        """
        Appium API.
        The locations relative to the view of all present elements.
        """
        return [element.location_in_view for element in self.all_present_elements]
