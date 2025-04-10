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

from typing import Type

from appium.webdriver.webdriver import WebDriver
from appium.webdriver.webelement import WebElement

from ..base.elements import Elements as BaseElements
from .by import ByAttr
from .page import Page


class Elements(BaseElements[Page, WebDriver, WebElement]):

    def _verify_by(self, by: str | None):
        if by not in ByAttr.OPTIONAL_VALUES:
            raise ValueError(f'The set "by" strategy "{by}" is invalid, please refer to "appium By".')
        
    def _verify_instance(self, instance: Page):
        if not isinstance(instance, Page):
            raise TypeError(
                f'"appium Element" must be used in "appium Page", got {type(instance).__name__}'
            )
    
    def _verify_owner(self, owner: Type[Page]):
        if not issubclass(owner, Page):
            raise TypeError(
                f'"appium Element" must be used in "appium Page", got {type(owner).__name__}'
            )

    def _verify_set_value(self, value: Elements):
        if not isinstance(value, Elements):
            raise TypeError(f'Assigned value must be "appium Element", got {type(value).__name__}.')

    @property
    def locations_in_view(self) -> list[dict[str, int]]:
        """
        Appium API.
        The locations relative to the view of all present elements.
        """
        return [element.location_in_view for element in self.all_present_elements]
