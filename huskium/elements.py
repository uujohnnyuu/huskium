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
from typing import TYPE_CHECKING, cast, Literal, Self, Type

from selenium.common.exceptions import TimeoutException
from selenium.types import WaitExcTypes
from selenium.webdriver.remote.shadowroot import ShadowRoot
from selenium.webdriver.support.ui import WebDriverWait

from . import ec_extension as ecex
from .by import ByAttribute
from .config import Log
from .logging import PageElementLoggerAdapter
from .page import Page
from .types import WebDriver, WebElement
from .shared import EXTENDED_IGNORED_EXCEPTIONS, _Name


LOGGER = logging.getLogger(__name__)
LOGGER.addFilter(Log.PREFIX_FILTER)


class Elements:

    if TYPE_CHECKING:
        _page: Page
        _driver: WebDriver
        _wait_timeout: int | float

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
                record as `(by="{by}", value="{value}")`.
        """
        self._verify_data(by, value, timeout, remark)
        self._set_data(by, value, timeout, remark)

    def __get__(self, instance: Page, owner: Type[Page] | None = None) -> Self:
        """Make "Elements" a descriptor of "Page"."""
        if not isinstance(instance, Page):
            raise TypeError(f'"{type(self).__name__}" must be used with a "Page" instance.')
        if getattr(self, _Name._page, None) != instance:
            self._page = instance
            self._driver = instance._driver
            self.logger.debug(f'[__get__] Driver updated: {self._driver}.')
        else:
            self.logger.debug(f'[__get__] Using existing driver: {self._driver}.')
        return self

    def __set__(self, instance: Page, value: Elements) -> None:
        """Set dynamic element by `self.elements = Elements(...)` pattern."""
        if not isinstance(value, Elements):
            raise TypeError('Only "Elements" objects are allowed to be assigned.')
        # Avoid using __init__() here, as it may reset the descriptor.
        # Do not call dynamic, as it will duplicate the verification.
        self._set_data(value.by, value.value, value.timeout, value.remark)
        self.logger.debug('[__set__] Dynamic element set.')

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
        self.logger.debug('[dynamic] Dynamic element set.')
        return self

    def _verify_data(self, by, value, timeout, remark) -> None:
        """Verify basic attributes."""
        if by not in ByAttribute.VALUES_WITH_NONE:
            raise ValueError(f'The "by" strategy "{by}" is undefined.')
        if not isinstance(value, (str, type(None))):
            raise TypeError(f'The "value" type must be "str", not "{type(value).__name__}".')
        if not isinstance(timeout, (int, float, type(None))):
            raise TypeError(f'The "timeout" type must be "int" or "float", not "{type(timeout).__name__}".')
        if not isinstance(remark, (str, type(None))):
            raise TypeError(f'The "remark" type must be "str", not "{type(remark).__name__}".')

    def _set_data(self, by, value, timeout, remark) -> None:
        """Set basic attributes."""
        self._by = by
        self._value = value
        self._timeout = timeout
        self._remark = remark
        self._logger = PageElementLoggerAdapter(LOGGER, self)

    @property
    def by(self) -> str | None:
        """The initial `by`."""
        return self._by

    @property
    def value(self) -> str | None:
        """The initial `value`."""
        return self._value

    @property
    def locator(self) -> tuple[str, str]:
        """The locator `(by, value)`"""
        if self._by and self._value:
            return (self._by, self._value)
        raise ValueError('"by" and "value" cannot be None when performing element operations.')

    @property
    def timeout(self) -> int | float:
        """If initial `timeout=None`, return `page.timeout`."""
        return self._page._timeout if self._timeout is None else self._timeout

    @property
    def remark(self) -> str:
        """If initial `remark=None`, return (by="{by}", value="{value}")."""
        return self._remark or f'(by="{self._by}", value="{self._value}")'

    @property
    def logger(self) -> PageElementLoggerAdapter:
        """The initial `logger`."""
        return self._logger

    @property
    def page(self) -> Page:
        """The `page` from descriptor."""
        return self._page

    @property
    def driver(self) -> WebDriver:
        """The `driver` from `page`."""
        return self._driver

    def find_elements(self, index: int | None = None) -> list[WebElement] | WebElement:
        """
        Using the traditional `find_elements()` or
        `find_elements()[index]` (if there is index) to locate elements.
        If there are no any element found, it will return empty list `[]`.
        """
        if isinstance(index, int):
            return self.driver.find_elements(*self.locator)[index]
        return self.driver.find_elements(*self.locator)

    @property
    def wait_timeout(self) -> int | float | None:
        """
        The final waiting timeout of the element.
        If no any element action has been executed yet, it will return None.
        """
        return getattr(self, _Name._wait_timeout, None)

    @property
    def wait_reraise(self) -> bool | None:
        """The final reraise value."""
        return getattr(self, _Name._wait_reraise, None)

    def wait(
        self,
        timeout: int | float | None = None,
        ignored_exceptions: WaitExcTypes | None = None
    ) -> WebDriverWait:
        """
        Get a WebDriverWait object.

        Args:
            timeout: Maximum wait time in seconds.
                If `None`, it initializes with the elements timeout.
            ignored_exceptions: Iterable ignored exception classes.
                If `None`, it contains `NoSuchElementException` only.
        """
        self._wait_timeout = self.timeout if timeout is None else timeout
        return WebDriverWait(
            driver=self.driver,
            timeout=self._wait_timeout,
            ignored_exceptions=ignored_exceptions
        )

    def _timeout_reraise(self, reraise: bool | None) -> bool:
        """The final reraise decision."""
        self._wait_reraise = self.page.reraise if reraise is None else reraise
        return self._wait_reraise

    def _timeout_process(
        self,
        status: str,
        exc: TimeoutException,
        reraise: bool | None
    ) -> Literal[False]:
        """Handling a TimeoutException after it occurs."""
        exc.msg = f'Timed out waiting {self.wait_timeout} seconds for elements "{self.remark}" to be "{status}".'
        if self._timeout_reraise(reraise):
            self.logger.exception(exc.msg, stacklevel=2)
            raise exc
        self.logger.warning(exc.msg, exc_info=True, stacklevel=2)
        return False

    def find(
        self,
        index: int | None = None,
        timeout: int | float | None = None,
        reraise: bool | None = None
    ) -> list[WebElement] | WebElement | Literal[False]:
        """
        Waits for the element or elements to be present.

        Args:
            index: `None` for all elemets.
            timeout: Maximum wait time in seconds.
                If `None`, uses `self.timeout`.
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

    def wait_all_present(
        self,
        timeout: int | float | None = None,
        reraise: bool | None = None
    ) -> list[WebElement] | Literal[False]:
        """
        Waits for all elements to become present.

        Args:
            timeout: Maximum wait time in seconds.
                If `None`, uses `self.timeout`.
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
            elements = self.wait(timeout).until(
                ecex.presence_of_all_elements_located(self.locator)
            )
            self.logger.debug(f'Locator -> AllPresentE = {elements}')
            return elements
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
                If `None`, uses `self.timeout`.
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
            true: Literal[True] = self.wait(timeout).until(
                ecex.absence_of_all_elements_located(self.locator)
            )
            self.logger.debug(f'Locator -> AllAbsent = {true}')
            return true
        except TimeoutException as exc:
            return self._timeout_process('all absent', exc, reraise)

    def wait_all_visible(
        self,
        timeout: int | float | None = None,
        reraise: bool | None = None
    ) -> list[WebElement] | Literal[False]:
        """
        Waits for all elements to become visible.

        Args:
            timeout: Maximum wait time in seconds.
                If `None`, uses `self.timeout`.
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
            elements = self.wait(timeout, EXTENDED_IGNORED_EXCEPTIONS).until(
                ecex.visibility_of_all_elements_located(self.locator)
            )
            self.logger.debug(f'locator -> AllVisibleE : {elements}')
            return elements
        except TimeoutException as exc:
            return self._timeout_process('all visible', exc, reraise)

    def wait_any_visible(
        self,
        timeout: int | float | None = None,
        reraise: bool | None = None
    ) -> list[WebElement] | Literal[False]:
        """
        Waits for at least one element to become visible.

        Args:
            timeout: Maximum wait time in seconds.
                If `None`, uses `self.timeout`.
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
            elements = self.wait(timeout, EXTENDED_IGNORED_EXCEPTIONS).until(
                ecex.visibility_of_any_elements_located(self.locator)
            )
            self.logger.debug(f'locator -> AnyVisibleE : {elements}')
            return elements
        except TimeoutException as exc:
            return self._timeout_process('any visible', exc, reraise)

    @property
    def all_present(self) -> list[WebElement]:
        """The same as `elements.wait_all_present(reraise=True)`."""
        return cast(list[WebElement], self.wait_all_present(reraise=True))

    @property
    def all_visible(self) -> list[WebElement]:
        """The same as `elements.wait_all_visible(reraise=True)`."""
        return cast(list[WebElement], self.wait_all_visible(reraise=True))

    @property
    def any_visible(self) -> list[WebElement]:
        """The same as elements.wait_any_visible(reraise=True)."""
        return cast(list[WebElement], self.wait_any_visible(reraise=True))

    def are_all_present(self, timeout: int | float | None = None) -> bool:
        """
        Whether the all elements are present.

        Args:
            timeout: Maximum wait time in seconds.

        Returns:
            bool:
                `True` if all are present within the timeout, `False` otherwise.
        """
        return True if self.wait_all_present(timeout, False) else False

    def are_all_visible(self) -> bool:
        """
        Whether all elements are visible.

        Returns:
            bool:
                `True` if all are visible within the timeout, `False` otherwise.
        """
        elements = self.all_present
        for index, element in enumerate(elements, 1):
            if not element.is_displayed():
                self.logger.debug(f'Element {index} is invisible.')
                return False
        self.logger.debug(f'All {len(elements)} elements are visible.')
        return True

    def are_any_visible(self) -> bool:
        """
        Whether at least one element is visible.

        Returns:
            bool:
                `True` if at least one is visible within the timeout,
                `False` otherwise.
        """
        elements = self.all_present
        visible_elements = [element for element in elements if element.is_displayed()]
        if visible_elements:
            self.logger.debug(f'Among all {len(elements)} elements, {len(visible_elements)} are visible.')
            return True
        self.logger.debug(f'All {len(elements)} elements are invisible.')
        return False

    @property
    def quantity(self) -> int:
        """The quantity of all present elements."""
        try:
            return len(self.all_present)
        except TimeoutException:
            return 0

    @property
    def texts(self) -> list[str]:
        """The texts of all present elements."""
        return [element.text for element in self.all_present]

    @property
    def all_visible_texts(self) -> list[str]:
        """The texts of all elements until they are visible."""
        return [element.text for element in self.all_visible]

    @property
    def any_visible_texts(self) -> list[str]:
        """The texts of the elements if at least one is visible."""
        return [element.text for element in self.any_visible]

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
            for element in self.all_present
            for rect in [element.rect]
        ]

    @property
    def locations(self) -> list[dict[str, int]]:
        """The locations of all present elements."""
        return [element.location for element in self.all_present]

    @property
    def sizes(self) -> list[dict]:
        """The sizes of all present elements."""
        return [
            {
                'width': size['width'],
                'height': size['height']
            }
            for element in self.all_present
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
            for element in self.all_present
            for rect in [element.rect]
        ]

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
        return [element.get_dom_attribute(name) for element in self.all_present]

    def get_attributes(self, name: str) -> list[str | dict | None]:
        """The specific attributes or properties of all present elements."""
        return [element.get_attribute(name) for element in self.all_present]

    def get_properties(self, name: str) -> list[WebElement | bool | dict | str]:
        """The specific properties of all present elements."""
        return [element.get_property(name) for element in self.all_present]

    @property
    def locations_in_view(self) -> list[dict[str, int]]:
        """
        Appium API.
        The locations relative to the view of all present elements.
        """
        return [element.location_in_view for element in self.all_present]  # type: ignore[union-attr]

    @property
    def shadow_roots(self) -> list[ShadowRoot]:
        """
        Returns shadow roots of the elements if there is one or an error.
        Only works from Chromium 96, Firefox 96, and Safari 16.4 onwards.
        If no shadow root was attached, raises `NoSuchShadowRoot`.
        """
        return [element.shadow_root for element in self.all_present]

    @property
    def aria_roles(self) -> list[str]:
        """The ARIA roles of the current web elements."""
        return [element.aria_role for element in self.all_present]

    @property
    def accessible_names(self) -> list[str]:
        """The ARIA Levels of the current webelement."""
        return [element.accessible_name for element in self.all_present]
