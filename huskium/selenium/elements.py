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

import logging
from typing import Any, cast, Iterable, Literal, Self, Type

from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.remote.shadowroot import ShadowRoot
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from ..logging import LogConfig, PageElementLoggerAdapter
from ..wait import Wait
from ..common import _Name
from .by import ByAttr
from .ecex import GenericECEX
from .page import GenericPage


LOGGER = logging.getLogger(__name__)
LOGGER.addFilter(LogConfig.PREFIX_FILTER)


class GenericElements[WD: WebDriver, WE: WebElement]:

    _page: GenericPage[WD, WE]
    _wait: Wait

    def __init__(
        self,
        by: str | None = None,
        value: str | None = None,
        *,
        timeout: int | float | None = None,
        remark: str | None = None
    ) -> None:
        """
        Initial Elements attributes.

        Args:
            by: Use `from huskium import By` for all locators.
            value: The locator value.
            timeout: The maximum time in seconds to find the element.
                If `None`, use `page.timeout` from descriptor.
            remark: Custom remark for identification or logging. If `None`,
                record as ``{"by": by, "value": value}``.
        """
        self._verify_data(by, value, timeout, remark)
        self._set_data(by, value, timeout, remark)

    def __get__(self, instance: GenericPage[WD, WE], owner: Type[GenericPage[WD, WE]]) -> Self:
        """Make "Elements" a descriptor of "Page"."""
        self._verify_get(instance, owner)
        if getattr(self, _Name._page, None) is not instance:
            self._page = instance
            self._wait = Wait(instance._driver, 1)
        self._sync_data()
        return self

    def __set__(self, instance: GenericPage[WD, WE], value: GenericElements) -> None:
        """Set dynamic element by `page.elements = Elements(...)` pattern."""
        self._verify_set(instance, value)
        self._set_data(value._by, value._value, value._timeout, value._remark)

    def dynamic(
        self,
        by: str,
        value: str,
        *,
        timeout: int | float | None = None,
        remark: str | None = None
    ) -> Self:
        """
        Set dynamic elements as `page.elements.dynamic(...)` pattern.
        All the args logic are the same as Elements.

        Examples:
            ::

                # my_page.py
                class MyPage(Page):

                    my_static_elements = Elements()

                    def my_dynamic_elements(self, accid):
                        return self.my_static_elements.dynamic(
                            By.ACCESSIBILITY_ID, accid,
                            remark="Dynamically set my_static_elements."
                        )

                # my_testcase.py
                class MyTestCase:
                    ...
                    my_page = MyPage(driver)
                    # The element accessibility id is dynamic.
                    id_ = Server.get_id()
                    # Dynamically retrieve the elements using any method.
                    my_page.my_dynamic_elements(id_).texts
                    # The static elements can be used after the dynamic one is set.
                    my_page.my_static_elements.locations

        """
        # Avoid using __init__() here, as it will reset the descriptor.
        self._verify_data(by, value, timeout, remark)
        self._set_data(by, value, timeout, remark)
        self._sync_data()
        return self

    def _verify_data(
        self,
        by: str | None,
        value: str | None,
        timeout: int | float | None,
        remark: str | None
    ) -> None:
        """Verify basic attributes."""
        self._verify_by(by)
        self._verify_value(value)
        self._verify_timeout(timeout)
        self._verify_remark(remark)

    def _set_data(
        self,
        by: str | None,
        value: str | None,
        timeout: int | float | None,
        remark: str | dict | None
    ) -> None:
        """Set basic attributes."""
        self._by = by
        self._value = value
        self._timeout = timeout
        self._remark = remark or self.default_remark
        self._logger = PageElementLoggerAdapter(LOGGER, self)

    def _sync_data(self) -> None:
        """Synchronize necessary attributes."""
        self._wait.timeout = self._page._timeout if self._timeout is None else self._timeout

    def _verify_by(self, by: Any) -> None:
        if by not in ByAttr.OPTIONAL_VALUES:
            raise ValueError(f'Invalid "by": "{by}". Use values from "By" (from huskium.selenium import By).')

    def _verify_value(self, value: Any) -> None:
        if not isinstance(value, str | None):
            raise TypeError(f'The set "value" must be str, got {type(value).__name__}.')

    def _verify_timeout(self, timeout: Any) -> None:
        if not isinstance(timeout, int | float | None):
            raise TypeError(f'The set "timeout" must be int or float, got {type(timeout).__name__}.')

    def _verify_remark(self, remark: Any) -> None:
        if not isinstance(remark, str | None):
            raise TypeError(f'The set "remark" must be str, got {type(remark).__name__}.')

    def _verify_get(self, instance: Any, owner: Any):
        self._verify_descriptor_instance(instance)
        self._verify_descriptor_owner(owner)

    def _verify_set(self, instance: Any, value: Any):
        self._verify_descriptor_instance(instance)
        self._verify_descriptor_value(value)

    def _verify_descriptor_instance(self, instance: Any) -> None:
        if not isinstance(instance, GenericPage):
            raise TypeError(
                f'"selenium Elements" must be used in "selenium Page" or "appium Page", got {type(instance).__name__}'
            )

    def _verify_descriptor_owner(self, owner: Any) -> None:
        if not issubclass(owner, GenericPage):
            raise TypeError(
                f'"selenium Elements" must be used in "selenium Page" or "appium Page", got {type(owner).__name__}'
            )

    def _verify_descriptor_value(self, value: Any) -> None:
        if not isinstance(value, GenericElements):
            raise TypeError(f'Assigned value must be "selenium Elements", got {type(value).__name__}.')

    @property
    def by(self) -> str | None:
        """The elements locator strategy."""
        return self._by

    @property
    def value(self) -> str | None:
        """The elements locator value."""
        return self._value

    @property
    def locator(self) -> tuple[str, str]:
        """The elements locator `(by, value)`"""
        if self._by and self._value:
            return (self._by, self._value)
        raise ValueError('The locator "(by, value)" must be set.')

    @property
    def timeout(self) -> int | float:
        """The elements current wait timeout in seconds."""
        return self._wait.timeout

    def reset_timeout(self, value: int | float | None = None) -> None:
        """Reset the elements timeout in seconds."""
        self._verify_timeout(value)
        self._timeout = value

    @property
    def remark(self) -> str | dict:
        """
        The elements remark.
        If not set, defaults to ``{"by": by, "value": value}``.
        """
        return self._remark

    @property
    def default_remark(self) -> dict:
        """The elements default remark ``{"by": by, "value": value}``."""
        return {"by": self._by, "value": self._value}

    def reset_remark(self, value: str | None = None) -> None:
        """
        Reset the elements remark. If value is None,
        defaults to ``{"by": by, "value": value}``.
        """
        self._verify_remark(value)
        self._remark = value or self.default_remark

    @property
    def logger(self) -> PageElementLoggerAdapter:
        """The elements logger."""
        return self._logger

    @property
    def page(self) -> GenericPage[WD, WE]:
        """The Page instance from the descriptor."""
        return self._page

    @property
    def driver(self) -> WD:
        """The WebDriver instance used by the page."""
        return self._page._driver

    @property
    def wait(self) -> Wait:
        """The current WebDriverWait instance."""
        return self._wait

    def waiting(
        self,
        timeout: int | float | None = None,
        ignored_exceptions: Type[Exception] | Iterable[Type[Exception]] | None = None
    ) -> Wait:
        """The final WebDriverWait instance."""
        self._wait.timeout = timeout
        self._wait.ignored_exceptions = ignored_exceptions
        return self._wait

    def find_elements(self, index: int | None = None) -> list[WE] | WE:
        """
        Using the traditional `find_elements()` or
        `find_elements()[index]` (if there is index) to locate elements.
        If there are no any element found, it will return empty list `[]`.
        """
        if isinstance(index, int):
            return cast(WE, self.driver.find_elements(*self.locator)[index])
        return cast(list[WE], self.driver.find_elements(*self.locator))

    def find(
        self,
        index: int | None = None,
        timeout: int | float | None = None,
        reraise: bool | None = None
    ) -> list[WE] | WE | Literal[False]:
        """
        Waits for the element or elements to be present.

        Args:
            index: `None` for all elemets.
            timeout: Maximum wait time in seconds.
                If `None`, uses `element.timeout`.
                If set, overrides with this value.
            reraise: Defines behavior when timed out.
                If `None`, follows `page.reraise`.
                If `True`, raises `TimeoutException`;
                if `False`, returns `False`.

        Returns:
            (list[WebElement] | WebElement | False):
                The `list[WebElement]` for `index=None`;
                the `WebElement` for `index=int`;
                `False` if no any element.

        """
        elements = self.wait_all_present(timeout, reraise)
        if isinstance(elements, list) and isinstance(index, int):
            # Raise an IndexError directly if the index has no corresponding element.
            return elements[index]
        return elements

    def _timeout_process(
        self,
        status: str,
        exc: TimeoutException,
        reraise: bool | None
    ) -> Literal[False]:
        """Handling a TimeoutException after it occurs."""
        exc.msg = f'Timed out waiting {self.wait.timeout} seconds for elements "{self.remark}" to be "{status}".'
        if self.page._timeout_reraise(reraise):
            raise exc
        return False

    def wait_all_present(
        self,
        timeout: int | float | None = None,
        reraise: bool | None = None
    ) -> list[WE] | Literal[False]:
        """
        Waits for all elements to become present.

        Args:
            timeout: Maximum wait time in seconds.
                If `None`, uses `element.timeout`.
                If set, overrides with this value.
            reraise: Defines behavior when timed out.
                If `None`, follows `page.reraise`.
                If `True`, raises `TimeoutException`;
                if `False`, returns `False`.

        Returns:
            (list[WebElement] | False):
                A list of `WebElement` if all are present within the timeout.
                `False` if all remain absent after the timeout(`reraise=False`).

        Raises:
            TimeoutException: Raised if all remain absent
                after the timeout(`reraise=True`).
        """
        try:
            return self.waiting(timeout).until(
                GenericECEX[WD, WE].presence_of_all_elements_located(self.locator)
            )
        except TimeoutException as exc:
            return self._timeout_process('all present', exc, reraise)

    def wait_all_absent(
        self,
        timeout: int | float | None = None,
        reraise: bool | None = None
    ) -> bool:
        """
        Waits for all elements to become absent.

        Args:
            timeout: Maximum wait time in seconds.
                If `None`, uses `element.timeout`.
                If set, overrides with this value.
            reraise: Defines behavior when timed out.
                If `None`, follows `page.reraise`.
                If `True`, raises `TimeoutException`;
                if `False`, returns `False`.

        Returns:
            bool:
                `True` if all are absent within the timeout. `False` if
                at least one is present after the timeout(`reraise=False`).

        Raises:
            TimeoutException: Raised if at least one remain present
                after the timeout(`reraise=True`).
        """
        try:
            return self.waiting(timeout).until(
                GenericECEX[WD, WE].absence_of_all_elements_located(self.locator)
            )
        except TimeoutException as exc:
            return self._timeout_process('all absent', exc, reraise)

    def wait_all_visible(
        self,
        timeout: int | float | None = None,
        reraise: bool | None = None
    ) -> list[WE] | Literal[False]:
        """
        Waits for all elements to become visible.

        Args:
            timeout: Maximum wait time in seconds.
                If `None`, uses `element.timeout`.
                If set, overrides with this value.
            reraise: Defines behavior when timed out.
                If `None`, follows `page.reraise`.
                If `True`, raises `TimeoutException`;
                if `False`, returns `False`.

        Returns:
            (list[WebElement] | False):
                A list of `WebElement` if all are visible within the timeout.
                `False` if at least one remain invisible or absent
                after the timeout(`reraise=False`).

        Raises:
            TimeoutException: Raised if at least one remain invisible or absent
                after the timeout(`reraise=True`).
        """
        try:
            return self.waiting(timeout, StaleElementReferenceException).until(
                GenericECEX[WD, WE].visibility_of_all_elements_located(self.locator)
            )
        except TimeoutException as exc:
            return self._timeout_process('all visible', exc, reraise)

    def wait_any_visible(
        self,
        timeout: int | float | None = None,
        reraise: bool | None = None
    ) -> list[WE] | Literal[False]:
        """
        Waits for at least one element to become visible.

        Args:
            timeout: Maximum wait time in seconds.
                If `None`, uses `element.timeout`.
                If set, overrides with this value.
            reraise: Defines behavior when timed out.
                If `None`, follows `page.reraise`.
                If `True`, raises `TimeoutException`;
                if `False`, returns `False`.

        Returns:
            (list[WebElement] | False):
                A list of `WebElement` if at least one is visible
                within the timeout. `False` if all remain invisible or absent
                after the timeout(`reraise=False`).

        Raises:
            TimeoutException: Raised if all remain invisible or absent
                after the timeout(`reraise=True`).
        """
        try:
            return self.waiting(timeout, StaleElementReferenceException).until(
                GenericECEX[WD, WE].visibility_of_any_elements_located(self.locator)
            )
        except TimeoutException as exc:
            return self._timeout_process('any visible', exc, reraise)

    @property
    def all_present_elements(self) -> list[WE]:
        """The same as `elements.wait_all_present(reraise=True)`."""
        return cast(list[WE], self.wait_all_present(reraise=True))

    @property
    def all_visible_elements(self) -> list[WE]:
        """The same as `elements.wait_all_visible(reraise=True)`."""
        return cast(list[WE], self.wait_all_visible(reraise=True))

    @property
    def any_visible_elements(self) -> list[WE]:
        """The same as elements.wait_any_visible(reraise=True)."""
        return cast(list[WE], self.wait_any_visible(reraise=True))

    def are_all_present(self, timeout: int | float | None = None) -> bool:
        """
        Whether the all elements are present.

        Args:
            timeout: Maximum wait time in seconds.

        Returns:
            bool:
                `True` if all are present within the timeout, `False` otherwise.
        """
        return bool(self.wait_all_present(timeout, False))

    def are_all_visible(self) -> bool:
        """
        Whether all elements are visible.

        Returns:
            bool:
                `True` if all are visible within the timeout, `False` otherwise.
        """
        return all(element.is_displayed() for element in self.all_present_elements)

    def are_any_visible(self) -> bool:
        """
        Whether at least one element is visible.

        Returns:
            bool:
                `True` if at least one is visible within the timeout,
                `False` otherwise.
        """
        return any(element.is_displayed() for element in self.all_present_elements)

    @property
    def quantity(self) -> int:
        """The quantity of all present elements."""
        return len(self.wait_all_present(reraise=False) or [])

    @property
    def texts(self) -> list[str]:
        """The texts of all present elements."""
        return [element.text for element in self.all_present_elements]

    @property
    def all_visible_texts(self) -> list[str]:
        """The texts of all elements until they are visible."""
        return [element.text for element in self.all_visible_elements]

    @property
    def any_visible_texts(self) -> list[str]:
        """The texts of the elements if at least one is visible."""
        return [element.text for element in self.any_visible_elements]

    @property
    def rects(self) -> list[dict[str, int]]:
        """The rects of all present elements."""
        return [
            {
                'x': rect['x'],
                'y': rect['y'],
                'width': rect['width'],
                'height': rect['height']
            }
            for element in self.all_present_elements
            for rect in [element.rect]
        ]

    @property
    def locations(self) -> list[dict[str, int]]:
        """The locations of all present elements."""
        return [element.location for element in self.all_present_elements]

    @property
    def sizes(self) -> list[dict]:
        """The sizes of all present elements."""
        return [
            {
                'width': size['width'],
                'height': size['height']
            }
            for element in self.all_present_elements
            for size in [element.size]
        ]

    @property
    def centers(self) -> list[dict]:
        """The center locations of all present elements."""
        return [
            {
                'x': int(rect['x'] + rect['width'] / 2),
                'y': int(rect['y'] + rect['height'] / 2)
            }
            for element in self.all_present_elements
            for rect in [element.rect]
        ]

    @property
    def shadow_roots(self) -> list[ShadowRoot]:
        """
        Returns shadow roots of the elements if there is one or an error.
        Only works from Chromium 96, Firefox 96, and Safari 16.4 onwards.
        If no shadow root was attached, raises `NoSuchShadowRoot`.
        """
        return [element.shadow_root for element in self.all_present_elements]

    @property
    def aria_roles(self) -> list[str]:
        """The ARIA roles of the current web elements."""
        return [element.aria_role for element in self.all_present_elements]

    @property
    def accessible_names(self) -> list[str]:
        """The ARIA Levels of the current webelement."""
        return [element.accessible_name for element in self.all_present_elements]

    def get_dom_attributes(self, name: str) -> list[str]:
        """
        Gets the given attributes of all present elements. Unlike
        `selenium.webdriver.remote.BaseWebElement.get_attribute`, this method
        only returns attributes declared in the element's HTML markup.

        Args:
            name: Name of the attribute to retrieve.

        Examples:
            ::

                text_length = page.element.get_dom_attributes("class")

        """
        return [element.get_dom_attribute(name) for element in self.all_present_elements]

    def get_attributes(self, name: str) -> list[str | dict | None]:
        """The specific attributes or properties of all present elements."""
        return [element.get_attribute(name) for element in self.all_present_elements]

    def get_properties(self, name: str) -> list[str | bool | dict | WE]:
        """The specific properties of all present elements."""
        return [
            cast(str | bool | dict | WE, element.get_property(name))
            for element in self.all_present_elements
        ]


class Elements(GenericElements[WebDriver, WebElement]):
    pass
