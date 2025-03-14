# Author: Johnny Chou
# Email: johnny071531@gmail.com
# PyPI: https://pypi.org/project/huskium/
# GitHub: https://github.com/uujohnnyuu/huskium


from __future__ import annotations

import logging
import platform
import time
from typing import TYPE_CHECKING, Any, cast, Literal, Self, Type

from selenium.common.exceptions import TimeoutException
from selenium.types import WaitExcTypes
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.shadowroot import ShadowRoot
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.select import Select

from ..logging import LogConfig, PageElementLoggerAdapter
from ..exception import NoSuchCacheException
from ..types import WebDriver, WebElement, Coordinate
from . import ec_extension as ecex
from .wait import Wait
from .common import ELEMENT_REFERENCE_EXCEPTIONS, EXTENDED_IGNORED_EXCEPTIONS, _Name, _Verify, Offset, Area
from .page import Page


LOGGER = logging.getLogger(__name__)
LOGGER.addFilter(LogConfig.PREFIX_FILTER)


class Element:

    # ==================================================================================================================
    # Dynamic Attributes Type Checking
    # ==================================================================================================================

    if TYPE_CHECKING:
        _page: Page
        _wait: Wait
        _synced_cache: bool
        _present_cache: WebElement
        _visible_cache: WebElement
        _clickable_cache: WebElement
        _select_cache: Select

    # ==================================================================================================================
    # Core Process
    # ==================================================================================================================

    _CACHE: bool = True

    @classmethod
    def enable_default_cache(cls) -> None:
        """Set default cache to `True` for all Element objects."""
        cls._CACHE = True

    @classmethod
    def disable_default_cache(cls) -> None:
        """Set default cache to `False` for all Element objects."""
        cls._CACHE = False

    @classmethod
    def default_cache(cls) -> bool:
        """Get the Element default cache value."""
        return cls._CACHE

    def __init__(
        self,
        by: str | None = None,
        value: str | None = None,
        index: int | None = None,
        *,
        timeout: int | float | None = None,
        cache: bool | None = None,
        remark: str | None = None
    ) -> None:
        """
        Initial Element attributes.

        Args:
            by: Use `from huskium import By` for all locators.
            value: The locator value.
            index: Default `None` to use the `find_element()` strategy.
                If `int`, uses the `find_elements()[index]` strategy.
            timeout: The maximum time in seconds to find the element.
                If `None`, use `page.timeout` from descriptor.
            cache: `True` to cache the located WebElement for reuse; otherwise,
                locate the element every time. If `None`, use `Cache.Element`.
            remark: Custom remark for identification or logging. If `None`,
                record as ``{"by": by, "value": value, "index": index}``.
        """
        _Verify.element(by, value, index, timeout, cache, remark)
        self._set_data(by, value, index, timeout, cache, remark)

    def __get__(self, instance: Page, owner: Type[Page]) -> Self:
        """Make "Element" a descriptor of "Page"."""
        _Verify.descriptor_get(instance, owner, Page)
        if getattr(self, _Name._page, None) is not instance:
            self._page = instance
            self._wait = Wait(instance._driver, 1)
            self._clear_caches()
        self._sync_data()
        return self

    def __set__(self, instance: Page, value: Element) -> None:
        """Set dynamic element by `page.element = Element(...)` pattern."""
        _Verify.descriptor_set(instance, Page, value, Element)
        self._set_data(value._by, value._value, value._index, value._timeout, value._cache, value._remark)
        self._clear_caches()

    def dynamic(
        self,
        by: str,
        value: str,
        index: int | None = None,
        *,
        timeout: int | float | None = None,
        cache: bool | None = None,
        remark: str | None = None
    ) -> Self:
        """
        Set dynamic elements as `page.element.dynamic(...)` pattern.
        All the args logic are the same as Element.

        Examples:
            ::

                # my_page.py
                class MyPage(Page):

                    my_static_element = Element()

                    def my_dynamic_element(self, id_):
                        return self.my_static_element.dynamic(
                            By.ID, id_, remark="dynamic_elem"
                        )

                # my_testcase.py
                class MyTestCase:

                    my_page = MyPage(driver)

                    # The element ID is dynamic.
                    id_ = Server.get_id()

                    # Dynamically retrieve the element using any method.
                    my_page.my_dynamic_element(id_).text

                    # The static element can be used after the dynamic one set.
                    my_page.my_static_element.click()

        """
        # Avoid using __init__() here, as it will reset the descriptor.
        _Verify.element(by, value, index, timeout, cache, remark)
        self._set_data(by, value, index, timeout, cache, remark)
        self._sync_data()
        self._clear_caches()
        return self

    def _set_data(
        self,
        by: str | None,
        value: str | None,
        index: int | None,
        timeout: int | float | None,
        cache: bool | None,
        remark: str | dict | None
    ) -> None:
        """Set basic attributes."""
        self._by = by
        self._value = value
        self._index = index
        self._timeout = timeout
        self._cache = cache
        self._remark = remark or self.default_remark
        self._logger = PageElementLoggerAdapter(LOGGER, self)

    def _sync_data(self) -> None:
        """Synchronize necessary attributes."""
        self._wait.timeout = self._page._timeout if self._timeout is None else self._timeout
        self._synced_cache = type(self)._CACHE if self._cache is None else self._cache

    def _clear_caches(self) -> None:
        """Clear all caches to prevent wrong element reference issues."""
        for cache_name in _Name._caches:
            vars(self).pop(cache_name, None)

    @property
    def by(self) -> str | None:
        """The element locator strategy."""
        return self._by

    @property
    def value(self) -> str | None:
        """The element locator value."""
        return self._value

    @property
    def locator(self) -> tuple[str, str]:
        """The element locator `(by, value)`"""
        if self._by and self._value:
            return (self._by, self._value)
        raise ValueError('The locator "(by, value)" must be set.')

    @property
    def index(self) -> int | None:
        """The element index."""
        return self._index

    @property
    def timeout(self) -> int | float:
        """The element current wait timeout in seconds."""
        return self._wait.timeout

    def reset_timeout(self, value: int | float | None = None) -> None:
        """Reset the element timeout in seconds."""
        _Verify.timeout(value)
        self._timeout = value

    @property
    def cache(self) -> bool:
        """The element final synced cache state."""
        return self._synced_cache

    def enable_cache(self) -> None:
        """Enable the element cache."""
        self._cache = True

    def disable_cache(self) -> None:
        """Disable the element cache."""
        self._cache = False

    def unset_cache(self) -> None:
        """Unset the element cache to follow the default cache state."""
        self._cache = None

    @property
    def remark(self) -> str | dict:
        """
        The element remark.
        If not set, defaults to ``{"by": by, "value": value, "index": index}``.
        """
        return self._remark

    @property
    def default_remark(self) -> dict:
        """
        The element default remark
        ``{"by": by, "value": value, "index": index}``.
        """
        return {"by": self._by, "value": self._value, "index": self._index}

    def reset_remark(self, value: str | None = None) -> None:
        """
        Reset the element remark. If value is None,
        defaults to ``{"by": by, "value": value, "index": index}``.
        """
        _Verify.remark(value)
        self._remark = value or self.default_remark

    @property
    def logger(self) -> PageElementLoggerAdapter:
        """The element logger."""
        return self._logger

    @property
    def page(self) -> Page:
        """The Page instance from the descriptor."""
        return self._page

    @property
    def driver(self) -> WebDriver:
        """The WebDriver instance used by the page."""
        return self._page._driver

    @property
    def action(self) -> ActionChains:
        """The ActionChains instance used by the page."""
        return self._page._action

    @property
    def wait(self) -> Wait:
        """The current WebDriverWait instance."""
        return self._wait

    def waiting(
        self,
        timeout: int | float | None = None,
        ignored_exceptions: WaitExcTypes | None = None
    ) -> Wait:
        """The final WebDriverWait instance."""
        self._wait.timeout = timeout
        self._wait.ignored_exceptions = ignored_exceptions
        return self._wait

    # ==================================================================================================================
    # Find Element
    # ==================================================================================================================

    def find_element(self) -> WebElement:
        """
        Using the traditional `find_element()` or `find_elements()[index]`
        to locate element.
        It is recommended for use in situations where no waiting is required,
        such as the Android UiScrollable locator method.
        """
        if isinstance(self.index, int):
            return self.driver.find_elements(*self.locator)[self.index]
        return self.driver.find_element(*self.locator)

    def _cache_try(self, name: str) -> Any:
        """
        Return `getattr(self, name)`,
        or raise `NoSuchCacheException` if no cache is available.
        """
        if self.cache and hasattr(self, name):
            return getattr(self, name)
        raise NoSuchCacheException(f'No cache for "{name}", please relocate the element in except.')

    @property
    def present_try(self) -> WebElement:
        """
        This attribute must be used with `try-except`.

        Examples:
            ::

                try:
                    self.present_try.text
                except ELEMENT_REFERENCE_EXCEPTIONS:
                    self.present.text

        """
        return self._cache_try(_Name._present_cache)

    @property
    def visible_try(self) -> WebElement:
        """
        This attribute must be used with `try-except`.

        Examples:
            ::

                try:
                    self.visible_try.text
                except ELEMENT_REFERENCE_EXCEPTIONS:
                    self.visible.text

        """
        return self._cache_try(_Name._visible_cache)

    @property
    def clickable_try(self) -> WebElement:
        """
        This attribute must be used with `try-except`.

        Examples:
            ::

                try:
                    self.clickable_try.click()
                except ELEMENT_REFERENCE_EXCEPTIONS:
                    self.clickable.click()

        """
        return self._cache_try(_Name._clickable_cache)

    @property
    def select_try(self) -> Select:
        """
        This attribute must be used with `try-except`.

        Examples:
            ::

                try:
                    self.select_try.options
                except ELEMENT_REFERENCE_EXCEPTIONS:
                    self.select.options

        """
        return self._cache_try(_Name._select_cache)

    def _cache_present_element(self, element: WebElement | Any):
        """Cache the present element if caching is enabled."""
        if self.cache and isinstance(element, WebElement):
            self._present_cache = element

    def _cache_visible_element(self, element: WebElement | Any, extra: bool = True):
        """
        Cache the element as present and visible
        if caching is enabled and extra conditions are met.
        """
        if self.cache and isinstance(element, WebElement) and extra:
            self._visible_cache = self._present_cache = element

    def _cache_clickable_element(self, element: WebElement | Any, extra: bool = True):
        """
        Cache the element as present, visible, and clickable
        if caching is enabled and extra conditions are met.
        """
        if self.cache and isinstance(element, WebElement) and extra:
            self._clickable_cache = self._visible_cache = self._present_cache = element

    def _cache_select_object(self, select: Select):
        """Cache the Select instance if caching is enabled."""
        if self.cache and isinstance(select, Select):
            self._select_cache = select

    def _timeout_process(
        self,
        status: str,
        exc: TimeoutException,
        reraise: bool | None,
        present: bool = True
    ) -> Literal[False]:
        """Handling a TimeoutException after it occurs."""
        if not present:
            status += ' or absent'
        exc.msg = f'Timed out waiting {self.wait.timeout} seconds for element "{self.remark}" to be "{status}".'
        if isinstance(exc.__context__, NoSuchCacheException):
            exc.__context__ = None  # Suppress unnecessary internal exceptions.
        if self.page._timeout_reraise(reraise):
            raise exc
        return False

    def wait_present(
        self,
        timeout: int | float | None = None,
        reraise: bool | None = None
    ) -> WebElement | Literal[False]:
        """
        Waits for the element to become present.

        Args:
            timeout: Maximum wait time in seconds.
                If `None`, uses `element.timeout`.
                If set, overrides with this value.
            reraise: Defines behavior when timed out.
                If `None`, follows `page.reraise`.
                If `True`, raises `TimeoutException`;
                if `False`, returns `False`.

        Returns:
            (WebElement | False):
                The `WebElement` if present within the timeout;
                `False` if remains absent after the timeout(`reraise=False`).

        Raises:
            TimeoutException: Raised if it remains absent
                after the timeout(`reraise=True`).
        """
        try:
            element = self.waiting(timeout).until(
                ecex.presence_of_element_located(self.locator, self.index)
            )
            self._cache_present_element(element)
            return element
        except TimeoutException as exc:
            return self._timeout_process('present', exc, reraise)

    def wait_absent(
        self,
        timeout: int | float | None = None,
        reraise: bool | None = None
    ) -> bool:
        """
        Waits for the element to become absent.

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
                `True` if absent within the timeout;
                `False` if remains present after the timeout(`reraise=False`).

        Raises:
            TimeoutException: Raised if it remains present
                after the timeout(`reraise=True`).
        """
        try:
            return self.waiting(timeout).until(
                ecex.absence_of_element_located(self.locator, self.index)
            )
        except TimeoutException as exc:
            return self._timeout_process('absent', exc, reraise)

    def wait_visible(
        self,
        timeout: int | float | None = None,
        reraise: bool | None = None
    ) -> WebElement | Literal[False]:
        """
        Waits for the element to become visible.

        Args:
            timeout: Maximum wait time in seconds.
                If `None`, uses `element.timeout`.
                If set, overrides with this value.
            reraise: Defines behavior when timed out.
                If `None`, follows `page.reraise`.
                If `True`, raises `TimeoutException`;
                if `False`, returns `False`.

        Returns:
            (WebElement | False):
                The `WebElement` if visible within the timeout;
                `False` if remains invisible or absent
                after the timeout(`reraise=False`).

        Raises:
            TimeoutException: Raised if it remains invisible or absent
                after the timeout(`reraise=True`).
        """
        try:
            try:
                self._visible_cache = self.waiting(timeout).until(
                    ecex.visibility_of_element(self.present_try)
                )
                return self._visible_cache
            except ELEMENT_REFERENCE_EXCEPTIONS:
                element = self.waiting(timeout, EXTENDED_IGNORED_EXCEPTIONS).until(
                    ecex.visibility_of_element_located(self.locator, self.index)
                )
                self._cache_visible_element(element)
                return element
        except TimeoutException as exc:
            return self._timeout_process('visible', exc, reraise)

    def wait_invisible(
        self,
        timeout: int | float | None = None,
        present: bool = True,
        reraise: bool | None = None
    ) -> WebElement | bool:
        """
        Waits for the element to become invisible (or absent).

        Args:
            timeout: Maximum wait time in seconds.
                If `None`, uses `element.timeout`.
                If set, overrides with this value.
            present: Specifies whether the element must be present.
                If `True`, the element must be present.
                If `False`, the element can be absent.
            reraise: Defines behavior when timed out.
                If `None`, follows `page.reraise`.
                If `True`, raises `TimeoutException`;
                if `False`, returns `False`.

        Returns:
            (WebElement | bool):
                The `WebElement` if invisible within the timeout;
                `True` if absent(`present=False`) within the timeout;
                `False` if remains visible after the timeout(`reraise=False`).

        Raises:
            TimeoutException: Raised if it remains visible
                after the timeout(`reraise=True`).
        """
        try:
            try:
                return cast(
                    WebElement | Literal[True],
                    self.waiting(timeout).until(
                        ecex.invisibility_of_element(self.present_try, present)
                    )
                )
            except ELEMENT_REFERENCE_EXCEPTIONS:
                element_or_true: WebElement | Literal[True] = self.waiting(timeout, EXTENDED_IGNORED_EXCEPTIONS).until(
                    ecex.invisibility_of_element_located(self.locator, self.index, present)
                )
                self._cache_present_element(element_or_true)
                return element_or_true
        except TimeoutException as exc:
            return self._timeout_process('invisible', exc, reraise, present)

    def wait_clickable(
        self,
        timeout: int | float | None = None,
        reraise: bool | None = None
    ) -> WebElement | Literal[False]:
        """
        Waits for the element to become clickable.

        Args:
            timeout: Maximum wait time in seconds.
                If `None`, uses `element.timeout`.
                If set, overrides with this value.
            reraise: Defines behavior when timed out.
                If `None`, follows `page.reraise`.
                If `True`, raises `TimeoutException`;
                if `False`, returns `False`.

        Returns:
            (WebElement | False):
                The `WebElement` if clickable within the timeout;
                `False` if remains unclickable or absent
                after the timeout(`reraise=False`).

        Raises:
            TimeoutException: Raised if it remains unclickable or absent
                after the timeout(`reraise=True`).
        """
        try:
            try:
                self._clickable_cache = self._visible_cache = self.waiting(timeout).until(
                    ecex.element_to_be_clickable(self.present_try)
                )
                return self._clickable_cache
            except ELEMENT_REFERENCE_EXCEPTIONS:
                element = self.waiting(timeout, EXTENDED_IGNORED_EXCEPTIONS).until(
                    ecex.element_located_to_be_clickable(self.locator, self.index)
                )
                self._cache_clickable_element(element)
                return element
        except TimeoutException as exc:
            return self._timeout_process('clickable', exc, reraise)

    def wait_unclickable(
        self,
        timeout: int | float | None = None,
        present: bool = True,
        reraise: bool | None = None
    ) -> WebElement | bool:
        """
        Waits for the element to become unclickable (or absent).

        Args:
            timeout: Maximum wait time in seconds.
                If `None`, uses `element.timeout`.
                If set, overrides with this value.
            present: Specifies whether the element must be present.
                If `True`, the element must be present.
                If `False`, the element can be absent.
            reraise: Defines behavior when timed out.
                If `None`, follows `page.reraise`.
                If `True`, raises `TimeoutException`;
                if `False`, returns `False`.

        Returns:
            (WebElement | bool):
                The `WebElement` if unclickable within the timeout;
                `True` if absent(`present=False`) within the timeout;
                `False` if remains clickable after the timeout(`reraise=False`).

        Raises:
            TimeoutException: Raised if it remains clickable
                after the timeout(`reraise=True`).
        """
        try:
            try:
                return cast(
                    WebElement | Literal[True],
                    self.waiting(timeout).until(
                        ecex.element_to_be_unclickable(self.present_try, present)
                    )
                )
            except ELEMENT_REFERENCE_EXCEPTIONS:
                element_or_true: WebElement | Literal[True] = self.waiting(timeout, EXTENDED_IGNORED_EXCEPTIONS).until(
                    ecex.element_located_to_be_unclickable(self.locator, self.index, present)
                )
                self._cache_present_element(element_or_true)
                return element_or_true
        except TimeoutException as exc:
            return self._timeout_process('unclickable', exc, reraise, present)

    def wait_selected(
        self,
        timeout: int | float | None = None,
        reraise: bool | None = None
    ) -> WebElement | Literal[False]:
        """
        Waits for the element to become selected.

        Args:
            timeout: Maximum wait time in seconds.
                If `None`, uses `element.timeout`.
                If set, overrides with this value.
            reraise: Defines behavior when timed out.
                If `None`, follows `page.reraise`.
                If `True`, raises `TimeoutException`;
                if `False`, returns `False`.

        Returns:
            (WebElement | False):
                The `WebElement` if selected within the timeout;
                `False` if remains unselected or absent
                after the timeout(`reraise=False`).

        Raises:
            TimeoutException: Raised if it remains unselected or absent
                after the timeout(`reraise=True`).
        """
        try:
            try:
                return self.waiting(timeout).until(
                    ecex.element_to_be_selected(self.present_try)
                )
            except ELEMENT_REFERENCE_EXCEPTIONS:
                element = self.waiting(timeout, EXTENDED_IGNORED_EXCEPTIONS).until(
                    ecex.element_located_to_be_selected(self.locator, self.index)
                )
                self._cache_present_element(element)
                return element
        except TimeoutException as exc:
            return self._timeout_process('selected', exc, reraise)

    def wait_unselected(
        self,
        timeout: int | float | None = None,
        reraise: bool | None = None
    ) -> WebElement | Literal[False]:
        """
        Waits for the element to become unselected.

        Args:
            timeout: Maximum wait time in seconds.
                If `None`, uses `element.timeout`.
                If set, overrides with this value.
            reraise: Defines behavior when timed out.
                If `None`, follows `page.reraise`.
                If `True`, raises `TimeoutException`;
                if `False`, returns `False`.

        Returns:
            (WebElement | False):
                The `WebElement` if unselected within the timeout;
                `False` if remains selected or absent
                after the timeout(`reraise=False`).

        Raises:
            TimeoutException: Raised if it remains selected or absent
                after the timeout(`reraise=True`).
        """
        try:
            try:
                return self.waiting(timeout).until(
                    ecex.element_to_be_unselected(self.present_try)
                )
            except ELEMENT_REFERENCE_EXCEPTIONS:
                element = self.waiting(timeout, EXTENDED_IGNORED_EXCEPTIONS).until(
                    ecex.element_located_to_be_unselected(self.locator, self.index)
                )
                self._cache_present_element(element)
                return element
        except TimeoutException as exc:
            return self._timeout_process('unselected', exc, reraise)

    @property
    def present(self) -> WebElement:
        """ The same as `element.wait_present(reraise=True)`."""
        return cast(WebElement, self.wait_present(reraise=True))

    @property
    def visible(self) -> WebElement:
        """The same as element.wait_visible(reraise=True)."""
        return cast(WebElement, self.wait_visible(reraise=True))

    @property
    def clickable(self) -> WebElement:
        """The same as element.wait_clickable(reraise=True)."""
        return cast(WebElement, self.wait_clickable(reraise=True))

    @property
    def select(self) -> Select:
        """The Select instance used by the present element."""
        try:
            select = Select(self.present_try)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            select = Select(self.present)
        self._cache_select_object(select)
        return select

    @property
    def present_cache(self) -> WebElement | None:
        """The present element cache, `None` otherwise."""
        return getattr(self, _Name._present_cache, None)

    @property
    def visible_cache(self) -> WebElement | None:
        """The visible element cache, `None` otherwise."""
        return getattr(self, _Name._visible_cache, None)

    @property
    def clickable_cache(self) -> WebElement | None:
        """The clickable element cache, `None` otherwise."""
        return getattr(self, _Name._clickable_cache, None)

    @property
    def select_cache(self) -> Select | None:
        """The Select instance, `None` otherwise."""
        return getattr(self, _Name._select_cache, None)

    # ==================================================================================================================
    # Basic WebElement Process
    # ==================================================================================================================

    def is_present(self, timeout: int | float | None = None) -> bool:
        """Whether the element is present within the timeout."""
        return bool(self.wait_present(timeout, False))

    def is_visible(self) -> bool:
        """Whether the element is visible (displayed)."""
        try:
            element = self.present_try
            result = element.is_displayed()
        except ELEMENT_REFERENCE_EXCEPTIONS:
            element = self.present
            result = element.is_displayed()
        self._cache_visible_element(element, result)
        return result

    def is_enabled(self) -> bool:
        """Whether the element is enabled."""
        try:
            return self.present_try.is_enabled()
        except ELEMENT_REFERENCE_EXCEPTIONS:
            return self.present.is_enabled()

    def is_clickable(self) -> bool:
        """Whether the element is clickable (displayed and enabled)."""
        try:
            element = self.present_try
            result = element.is_displayed() and element.is_enabled()
        except ELEMENT_REFERENCE_EXCEPTIONS:
            element = self.present
            result = element.is_displayed() and element.is_enabled()
        self._cache_clickable_element(element, result)
        return result

    def is_selected(self) -> bool:
        """Whether the element is selected."""
        try:
            return self.present_try.is_selected()
        except ELEMENT_REFERENCE_EXCEPTIONS:
            return self.present.is_selected()

    def is_viewable(self, timeout: int | float | None = None) -> bool:
        """
        Appium API.
        This method is typically used with swipe-based element searching.
        Checks if the current element is visible on the mobile screen.
        """
        element = self.wait_present(timeout, False)
        result = bool(element and element.is_displayed())
        self._cache_visible_element(element, result)
        return result

    @property
    def text(self) -> str:
        """The text of the element when it is present."""
        try:
            return self.present_try.text
        except ELEMENT_REFERENCE_EXCEPTIONS:
            return self.present.text

    @property
    def visible_text(self) -> str:
        """The text of the element when it is visible."""
        try:
            return self.visible_try.text
        except ELEMENT_REFERENCE_EXCEPTIONS:
            return self.visible.text

    @property
    def tag_name(self) -> str:
        """The tagName property."""
        try:
            return self.present_try.tag_name
        except ELEMENT_REFERENCE_EXCEPTIONS:
            return self.present.tag_name

    @property
    def rect(self) -> dict:
        """
        The location and size of the element.
        For example: `{'x': 10, 'y': 15, 'width': 100, 'height': 200}`.
        """
        try:
            rect = self.present_try.rect
        except ELEMENT_REFERENCE_EXCEPTIONS:
            rect = self.present.rect
        # rearranged
        return {
            'x': rect['x'],
            'y': rect['y'],
            'width': rect['width'],
            'height': rect['height']
        }

    @property
    def location(self) -> dict:
        """
        The location of the element when it is in the renderable canvas.
        For example: `{'x': 200, 'y': 300}`.
        """
        try:
            return self.present_try.location
        except ELEMENT_REFERENCE_EXCEPTIONS:
            return self.present.location

    @property
    def location_once_scrolled_into_view(self) -> dict:
        """
        THIS PROPERTY MAY CHANGE WITHOUT WARNING.

        Use this to determine the on-screen location of an element
        that can be clicked, and it scrolls the element into view if necessary.

        Returns the top-left corner coordinates on the screen,
        or `(0, 0)` if the element is not visible.
        """
        try:
            return self.present_try.location_once_scrolled_into_view
        except ELEMENT_REFERENCE_EXCEPTIONS:
            return self.present.location_once_scrolled_into_view

    @property
    def location_in_view(self) -> dict[str, int]:
        """
        Appium API.
        Retrieve the location (coordination) of the element
        relative to the view when it is present.
        For example: `{'x': 100, 'y': 250}`.
        """
        try:
            return self.present_try.location_in_view  # type: ignore[attr-defined]
        except ELEMENT_REFERENCE_EXCEPTIONS:
            return self.present.location_in_view  # type: ignore[attr-defined]

    @property
    def size(self) -> dict:
        """
        The size of the element.
        For example: `{'width': 200, 'height': 100}`.
        """
        try:
            size = self.present_try.size
        except ELEMENT_REFERENCE_EXCEPTIONS:
            size = self.present.size
        # rearranged
        return {
            'width': size['width'],
            'height': size['height']
        }

    @property
    def border(self) -> dict[str, int]:
        """
        The border of the element.
        For example: `{'left': 150, 'right': 250, 'top': 200, 'bottom': 400}`.
        """
        try:
            rect = self.present_try.rect
        except ELEMENT_REFERENCE_EXCEPTIONS:
            rect = self.present.rect
        return {
            'left': int(rect['x']),
            'right': int(rect['x'] + rect['width']),
            'top': int(rect['y']),
            'bottom': int(rect['y'] + rect['height'])
        }

    @property
    def center(self) -> dict[str, int]:
        """
        The center location of the element.
        For example: `{'x': 80, 'y': 190}`.
        """
        try:
            rect = self.present_try.rect
        except ELEMENT_REFERENCE_EXCEPTIONS:
            rect = self.present.rect
        return {
            'x': int(rect['x'] + rect['width'] / 2),
            'y': int(rect['y'] + rect['height'] / 2)
        }

    @property
    def shadow_root(self) -> ShadowRoot:
        """
        Returns a ShadowRoot object of the element if there is one or an error.
        Only works from Chromium 96, Firefox 96, and Safari 16.4 onwards.
        If no shadow root was attached, raises `NoSuchShadowRoot`.
        """
        try:
            return self.present_try.shadow_root
        except ELEMENT_REFERENCE_EXCEPTIONS:
            return self.present.shadow_root

    @property
    def aria_role(self) -> str:
        """The ARIA role of the current web element."""
        try:
            return self.present_try.aria_role
        except ELEMENT_REFERENCE_EXCEPTIONS:
            return self.present.aria_role

    @property
    def accessible_name(self) -> str:
        """The ARIA Level of the current web element."""
        try:
            return self.present_try.accessible_name
        except ELEMENT_REFERENCE_EXCEPTIONS:
            return self.present.accessible_name

    def get_dom_attribute(self, name: str) -> str:
        """
        Gets the given attribute of the element. Unlike
        `selenium.webdriver.remote.BaseWebElement.get_attribute`, this method
        only returns attributes declared in the element's HTML markup.

        Args:
            name: Name of the attribute to retrieve.

        Examples:
            ::

                text_length = element.get_dom_attribute("class")

        """
        try:
            return self.present_try.get_dom_attribute(name)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            return self.present.get_dom_attribute(name)

    def get_attribute(self, name: Any | str) -> Any | str | dict | None:
        """
        This method will first try to return the value of a property with the
        given name. If a property with that name doesn't exist, it returns the
        value of the attribute with the same name. If there's no attribute with
        that name, `None` is returned.

        Values which are considered truthy, that is equals "true" or "false",
        are returned as booleans.  All other non-`None` values are returned
        as strings.  For attributes or properties which do not exist, `None`
        is returned.

        To obtain the exact value of the attribute or property, use
        `selenium.webdriver.remote.BaseWebElement.get_dom_attribute` or
        `selenium.webdriver.remote.BaseWebElement.get_property`.

        Args:
            name: Name of the attribute or property to retrieve.

        Examples:
            ::

                # Check if the "active" CSS class is applied to an element.
                is_active = "active" in target_element.get_attribute("class")

        """
        try:
            return self.present_try.get_attribute(name)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            return self.present.get_attribute(name)

    def get_property(self, name: Any) -> str | bool | WebElement | dict:
        """
        Gets the given property of the element.

        Args:
            name: Name of the property to retrieve.

        Examples:
            ::

                text_length = target_element.get_property("text_length")

        """
        try:
            return self.present_try.get_property(name)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            return self.present.get_property(name)

    def value_of_css_property(self, property_name: Any) -> str:
        """
        The value of a CSS property.

        Examples:
            ::

                page.element.value_of_css_property('color')

        """
        try:
            return self.present_try.value_of_css_property(property_name)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            return self.present.value_of_css_property(property_name)

    def visible_value_of_css_property(self, property_name: Any) -> str:
        """
        The visible value of a CSS property.

        Examples:
            ::

                page.element.visible_value_of_css_property('color')

        """
        try:
            return self.visible_try.value_of_css_property(property_name)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            return self.visible.value_of_css_property(property_name)

    def click(self) -> None:
        """Click the element when it is clickable."""
        try:
            self.clickable_try.click()
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.clickable.click()

    def delayed_click(self, sleep: int | float = 0.5) -> None:
        """
        Clicks the element after it becomes clickable,
        with a specified delay (sleep) in seconds.
        """
        try:
            cache = self.clickable_try
            time.sleep(sleep)
            cache.click()
        except ELEMENT_REFERENCE_EXCEPTIONS:
            element = self.clickable
            time.sleep(sleep)
            element.click()

    def clear(self) -> Self:
        """
        Clear the text of the field type element.

        Examples:
            ::

                my_page.my_element.clear()
                my_page.my_element.clear().send_keys('my text')
                my_page.my_element.click().clear().send_keys('my text')

        """
        try:
            self.clickable_try.clear()
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.clickable.clear()
        return self

    def send_keys(self, *value) -> Self:
        """
        Simulates typing into the element.

        Args:
            *value: The texts or keys to typing.

        Examples:
            ::

                my_page.my_element.send_keys('my_text')
                my_page.my_element.clear().send_keys('my_text')
                my_page.my_element.click().clear().send_keys('my_text')

        """
        try:
            self.clickable_try.send_keys(*value)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.clickable.send_keys(*value)
        return self

    def submit(self) -> None:
        """Submits a form."""
        try:
            self.present_try.submit()
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.present.submit()

    def switch_to_frame(
        self,
        timeout: int | float | None = None,
        reraise: bool | None = None
    ) -> bool:
        """Switch to the frame if is available."""
        try:
            return self.waiting(timeout).until(
                ec.frame_to_be_available_and_switch_to_it(self.locator),
            )
        except TimeoutException as exc:
            return self._timeout_process('available frame', exc, reraise)

    def screenshot(self, filename: str) -> bool:
        """
        Saves a screenshot of the current element to a PNG image file.
        Returns False if there is any IOError, else returns True.

        Args:
            filename: The **full path** you wish to save your screenshot to.
                This should end with a `.png` extension.
        """
        try:
            return self.present_try.screenshot(filename)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            return self.present.screenshot(filename)

    # ==================================================================================================================
    # ActionChains Process
    # ==================================================================================================================

    def perform(self) -> None:
        """
        ActionChains API. Performs all stored actions.

        Examples:
            ::

                # Basic usage. Execute element actions.
                page.element.scroll_to_element().action_click().perform()

                # Multiple actions to call, set perform to the last action.
                # This will execute all actions in page not just page.element2.
                page.element1.scroll_to_element().action_click()
                page.element2.drag_and_drop(page.element3).perform()

                # As above, it is the same to call perform by page:
                page.element1.scroll_to_element().action_click()
                page.element2.drag_and_drop(page.element3)
                page.perform()

        """
        self.action.perform()

    def reset_actions(self) -> None:
        """
        ActionChains API.
        Clears actions that are already stored in object of Page.
        once called, it will reset all stored actions in page.

        Examples:
            ::

                # Reset the stored actions by the last reset_actions.
                page.element1.scroll_to_element().action_click()
                page.element2.click_and_hold().reset_actions()

                # There is a better one structure,
                # reset all action calls made by page.
                page.element1.scroll_to_element().action_click()
                page.element2.click_and_hold()
                page.reset_actions()

        """
        self.action.reset_actions()

    def action_click(self) -> Self:
        """
        ActionChains API. Clicks an element.

        Examples:
            ::

                # Basic usage
                my_page.my_element.action_click().perform()

                # Chain with another method
                my_page.my_element.scroll_to_element().action_click().perform()

                # or
                my_page.my_element1.scroll_to_element().action_click()
                ...  # other process
                my_page.perform()

        """
        try:
            self.action.click(self.present_try)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.action.click(self.present)
        return self

    def click_and_hold(self) -> Self:
        """
        ActionChains API. Holds down the left mouse button on an element.

        Examples:
            ::

                # Basic usage
                my_page.my_element.click_and_hold().perform()

                # Chain with another method
                my_page.my_element.scroll_to_element().click_and_hold().perform()

                # or
                my_page.my_element1.scroll_to_element().click_and_hold()
                ...  # other process
                my_page.perform()

        """
        try:
            self.action.click_and_hold(self.present_try)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.action.click_and_hold(self.present)
        return self

    def context_click(self) -> Self:
        """
        ActionChains API. Performs a context-click (right click) on an element.

        Examples:
            ::

                # Basic usage
                my_page.my_element.context_click().perform()

                # Chain with another method
                my_page.my_element.scroll_to_element().context_click().perform()

                # or
                my_page.my_element1.scroll_to_element().context_click()
                ...  # other process
                my_page.perform()

        """
        try:
            self.action.context_click(self.present_try)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.action.context_click(self.present)
        return self

    def double_click(self) -> Self:
        """
        ActionChains API. Double-clicks an element.

        Examples:
            ::

                # Basic usage
                my_page.my_element.double_click()

                # Chain with another method
                my_page.my_element.scroll_to_element().double_click()

                # or
                my_page.my_element1.scroll_to_element().double_click()
                ...  # other process
                my_page.perform()

        """
        try:
            self.action.double_click(self.present_try)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.action.double_click(self.present)
        return self

    def drag_and_drop(self, target: Element) -> Self:
        """
        ActionChains API.
        Holds down the left mouse button on the source element,
        then moves to the target element and releases the mouse button.

        Args:
            target: The element to mouse up.

        Examples:
            ::

                # Basic usage
                page.element1.drag_and_drop(page.element2).perform()

                # Chain with another method
                page.element1.scroll_to_element().drag_and_drop(page.element2).perform()

                # or
                page.element1.scroll_to_element().drag_and_drop(page.element2)
                ...  # other process
                page.perform()

        """
        try:
            self.action.drag_and_drop(self.present_try, target.present_try)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.action.drag_and_drop(self.present, target.present)
        return self

    def drag_and_drop_by_offset(self, xoffset: int, yoffset: int) -> Self:
        """
        ActionChains API.
        Holds down the left mouse button on the source element,
        then moves to the target offset and releases the mouse button.

        Args:
            xoffset: X offset to move to, as a positive or negative integer.
            yoffset: Y offset to move to, as a positive or negative integer.

        Examples:
            ::

                # Basic usage
                page.element.drag_and_drop_by_offset(100, 200).perform()

                # Chain with another method
                page.element.scroll_to_element().drag_and_drop_by_offset(100, 200).perform()

                # or
                page.element.scroll_to_element().drag_and_drop_by_offset(100, 200)
                ...  # other process
                page.perform()

        """
        try:
            self.action.drag_and_drop_by_offset(self.present_try, xoffset, yoffset)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.action.drag_and_drop_by_offset(self.present, xoffset, yoffset)
        return self

    def hotkey(self, *value: str) -> Self:
        """
        ActionChains API. Sends hotkey to target element.

        Args:
            value: The combination of hotkey.

        Examples:
            ::

                # copy(control+c)
                page.element.hotkey(Keys.CONTROL, 'c').perform()

                # switch to previous application(command+shift+tab)
                page.element.hotkey(Keys.COMMAND, Keys.SHIFT, Keys.TAB).perform()

        """
        # key_down, first to focus target element.
        try:
            self.action.key_down(value[0], self.present_try)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.action.key_down(value[0], self.present)
        for key in value[1:-1]:
            self.action.key_down(key)
        # send_keys
        self.action.send_keys(value[-1])
        # key_up
        for key in value[-2::-1]:
            self.action.key_up(key)
        return self

    def key_down(self, value: str, focus: bool = True) -> Self:
        """
        ActionChains API.
        Sends a key press only, without releasing it.
        Should only be used with modifier keys (Control, Alt and Shift).
        If you want to perform a hotkey process, use hotkey() instead.

        Args:
            value: The modifier key to send. Values are defined in Keys class.
            focus: Whether to focus element or not.
                Default to focus current element.

        Examples:
            ::

                # copy(control+c)
                page.element.key_down(Key.CONTROL).action_send_keys('c').key_up(Key.CONTROL)

        """
        if focus:
            try:
                self.action.key_down(value, self.present_try)
            except ELEMENT_REFERENCE_EXCEPTIONS:
                self.action.key_down(value, self.present)
        else:
            self.action.key_down(value)
        return self

    def key_up(self, value: str, focus: bool = False) -> Self:
        """
        ActionChains API.
        Releases a modifier key.
        Should only be used with modifier keys (Control, Alt and Shift).
        If you want to perform a hotkey process, use hotkey() instead.

        Args:
            value: The modifier key to send. Values are defined in Keys class.
            focus: Whether to focus on the element or not.
                The default is NOT to focus on the current element
                as this is generally not the first action.

        Examples:
            ::

                # copy(control+c)
                page.element.key_down(Key.CONTROL).action_send_keys('c').key_up(Key.CONTROL)

        """
        if focus:
            try:
                self.action.key_up(value, self.present_try)
            except ELEMENT_REFERENCE_EXCEPTIONS:
                self.action.key_up(value, self.present)
        else:
            self.action.key_up(value)
        return self

    def action_send_keys(self, *keys_to_send: str) -> Self:
        """
        ActionChains API.
        Sends keys to current focused element.
        Note that it should have focused element first.

        Args:
            keys_to_send: The keys to send.
                Modifier keys constants can be found in the 'Keys' class.

        Examples:
            ::

                # Combine with key_down and key_up method
                page.element.key_down(Keys.COMMAND).action_send_keys('a').key_up(Keys.COMMAND).perform()

                # Send keys to focused element
                # This is recommend to use send_keys_to_element() instead.
                page.element.action_click()  # Need to have focused element first.
                page.element.action_send_keys('my_keys').perform()

        """
        self.action.send_keys(*keys_to_send)
        return self

    def send_keys_to_element(self, *keys_to_send: str) -> Self:
        """
        ActionChains API. Sends keys to an element.

        Args:
            keys_to_send: The keys to send.
                Modifier keys constants can be found in the 'Keys' class.

        Examples:
            ::

                # Basic usage
                page.element.send_keys_to_element(Keys.ENTER)

                # Chain with another method
                page.element.scroll_to_element(False).send_keys_to_element(Keys.ENTER)

                # or
                page.element.scroll_to_element(False).send_keys_to_element(Keys.ENTER)
                ...  # other process
                page.perform()

        """
        try:
            self.action.send_keys_to_element(self.present_try, *keys_to_send)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.action.send_keys_to_element(self.present, *keys_to_send)
        return self

    def move_to_element(self) -> Self:
        """
        ActionChains API. Moving the mouse to the middle of an element.

        Examples:
            ::

                # Basic usage
                page.element.move_to_element().perform()

                # Chain with another method
                page.element.scroll_to_element().move_to_element().perform()

                # or
                page.element.scroll_to_element().move_to_element()
                ...  # other process
                page.perform()

        """
        try:
            self.action.move_to_element(self.present_try)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.action.move_to_element(self.present)
        return self

    def move_to_element_with_offset(
        self,
        xoffset: int,
        yoffset: int,
    ) -> Self:
        """
        ActionChains API.
        Move the mouse by an offset of the specified element.
        Offsets are relative to the in-view center point of the element.

        Args:
            xoffset: X offset to move to, as a positive or negative integer.
            yoffset: Y offset to move to, as a positive or negative integer.

        Examples:
            ::

                # Basic usage
                page.element.move_to_element_with_offset(100, 200).perform()

                # Chain with another method
                page.element.scroll_to_element().move_to_element_with_offset(100, 200).perform()

                # or
                page.element.scroll_to_element().move_to_element_with_offset(100, 200)
                ...  # other process
                page.perform()

        """
        try:
            self.action.move_to_element_with_offset(self.present_try, xoffset, yoffset)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.action.move_to_element_with_offset(self.present, xoffset, yoffset)
        return self

    def release(self) -> Self:
        """
        ActionChains API. Releasing a held mouse button on an element.

        Examples:
            ::

                # Basic usage
                page.element.release().perform()

                # Chain with another method
                page.element.click_and_hold().release().perform()

                # or
                page.element.click_and_hold().release()
                ...  # other process
                page.perform()

        """
        try:
            self.action.release(self.present_try)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.action.release(self.present)
        return self

    def pause(self, seconds: int | float) -> Self:
        """
        ActionChains API.
        Pause all inputs for the specified duration in seconds.
        """
        self.action.pause(seconds)
        return self

    def scroll_to_element(self) -> Self:
        """
        ActionChains API.
        If the element is outside the viewport,
        scrolls the bottom of the element to the bottom of the viewport.

        Examples:
            ::

                # Basic usage
                page.element.scroll_to_element().perform()

                # Chain with another method
                page.element.scroll_to_element().action_click().perform()

                # or
                page.element1.scroll_to_element().action_click()
                ...  # other process
                page.perform()

        """
        try:
            self.action.scroll_to_element(self.present_try)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.action.scroll_to_element(self.present)
        return self

    def scroll_from_element(
        self,
        x_offset: int = 0,
        y_offset: int = 0,
        delta_x: int = 0,
        delta_y: int = 0
    ) -> Self:
        """
        ActionChains API.

        Set the origin to the center of the element with an offset,
        and perform the swipe with the specified delta.

        If the element is not in the viewport, the bottom of the element will
        first be scrolled to the bottom of the viewport.

        Args:
            x_offset: From origin element center, a negative value offset left.
            y_offset: From origin element center, a negative value offset up.
            delta_x: Distance along X axis to scroll using the wheel,
                a negative value scrolls left.
            delta_y: Distance along Y axis to scroll using the wheel,
                a negative value scrolls up.

        Examples:
            ::

                # Basic usage
                page.element.scroll_from_element(100, 200, -50, -100).perform()

                # Chain with another method
                page.element.scroll_from_element(-30, -50, 150, 100).action_click().perform()

                # or
                page.element.scroll_from_element(-30, -50, 150, 100).action_click()
                ...  # other process
                page.perform()

        """
        try:
            scroll_origin = ScrollOrigin.from_element(self.present_try, x_offset, y_offset)
            self.action.scroll_from_origin(scroll_origin, delta_x, delta_y)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            scroll_origin = ScrollOrigin.from_element(self.present, x_offset, y_offset)
            self.action.scroll_from_origin(scroll_origin, delta_x, delta_y)
        return self

    def tap(self, duration: int | None = None) -> Self:
        """
        Appium API.
        Tap the center location of the element when it is present.
        This method can be used when `click()` fails.

        Args:
            duration: Length of time to tap, in ms.
        """
        self.driver.tap([tuple(self.center.values())], duration)  # type: ignore[attr-defined]
        return self

    def app_scroll(self, target: Element, duration: int | None = None) -> Self:
        """
        Appium API. Scrolls from one element to another.

        Args:
            target: The element to scroll to (center of element).
            duration: Defines speed of scroll action when moving to target.
                Default is 600 ms for W3C spec.
        """
        try:
            self.driver.scroll(self.present_try, target.present_try, duration)  # type: ignore[attr-defined]
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.driver.scroll(self.present, target.present, duration)  # type: ignore[attr-defined]
        return self

    def app_drag_and_drop(self, target: Element, pause: float | None = None) -> Self:
        """
        Appium API. Drag the origin element to the destination element.

        Args:
            target: The element to drag to.
            pause: How long the action pauses before moving after
                the tap and hold in seconds.
        """
        try:
            self.driver.drag_and_drop(self.present_try, target.present_try, pause)  # type: ignore[attr-defined]
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.driver.drag_and_drop(self.present, target.present, pause)  # type: ignore[attr-defined]
        return self

    def swipe_by(
        self,
        offset: Coordinate = Offset.UP,
        area: Coordinate = Area.FULL,
        timeout: int | float = 3,
        max_round: int = 10,
        max_align: int = 2,
        min_xycmp: int = 100,
        duration: int = 1000
    ) -> Self:
        """
        Appium API.
        For native iOS and Android apps, it swipes the screen until
        the element becomes visible within the specified area.

        Args:
            offset: `(start_x, start_y, end_x, end_y)` or `(sx, sy, ex, ey)`.
            area: `(x, y, width, height)` or `(x, y, w, h)`.
            timeout: Maximum wait time in seconds.
            max_round: Maximum number of swipe attempts.
            max_align: Maximum attempts to align all borders of the element
                within the area (view) border.
            min_xycmp: Minimum x and y components to avoid being mistaken
                as a click **during alignment**.
                Should be considered along with `duration`.
            duration: Swipe and alignment duration in milliseconds.
                If too short, it may be mistaken as a click.
                Should be considered along with `offset` and `min_xycmp`.

        Examples:
            ::

                from huskium import Offset, Area

                # Swipe by default.
                # Offset.UP (sx, sy, ex, ey) = (0.5, 0.75, 0.5, 0.25)
                # Area.FULL (x, y, w, h) = (0.0, 0.0, 1.0, 1.0)
                # offset x: Fixed 0.5 of current window width.
                # offset y: From 0.75 to 0.25 of current window height.
                my_page.target_element.swipe_by()

                # Swipe to the direction using Offset.
                my_page.target_element.swipe_by(Offset.DOWN)
                my_page.target_element.swipe_by(Offset.UPPER_LEFT)

                # Swipe with customize relative offset.
                my_page.target_element.swipe_by((0.3, 0.85, 0.5, 0.35))

                # Swipe within a swipeable range.
                # Get the absolute area rect using the scrollable element.
                area = my_page.scrollable_element.rect
                my_page.target_element.swipe_by((0.3, 0.85, 0.5, 0.35), area)

                # Swipe with customize absolute offset.
                my_page.target_element.swipe_by((250, 300, 400, 700))

                # Swipe with customize relative offset of customize relative area.
                # The area is relative to current window rect, for example:
                # current window rect = (10, 20, 500, 1000)
                # area = (0.1, 0.2, 0.6, 0.7)
                # area_x = 10 + 500 x 0.1 = 60
                # area_y = 20 + 1000 x 0.2 = 220
                # area_width = 500 x 0.6 = 300
                # area_height = 1000 x 0.7 = 700
                my_page.target_element.swipe_by(
                    (0.3, 0.85, 0.5, 0.35), (0.1, 0.2, 0.6, 0.7)
                )

                # Swipe with customize relative offset of customize absolute area.
                my_page.target_element.swipe_by(
                    (0.3, 0.85, 0.5, 0.35), (100, 150, 300, 700)
                )

        """
        area = self.page._get_area(area)
        offset = self.page._get_offset(offset, area)
        self._swipe_by(offset, timeout, max_round, duration)
        self._align_by(area, max_align, min_xycmp, duration)
        return self

    def flick_by(
        self,
        offset: Coordinate = Offset.UP,
        area: Coordinate = Area.FULL,
        timeout: int | float = 3,
        max_round: int = 10,
        max_align: int = 2,
        min_xycmp: int = 100,
        duration: int = 1000
    ) -> Self:
        """
        Appium API.
        For native iOS and Android apps, it flicks the screen until
        the element becomes visible within the specified area.

        Args:
            offset: `(start_x, start_y, end_x, end_y)` or `(sx, sy, ex, ey)`.
            area: `(x, y, width, height)` or `(x, y, w, h)`.
            timeout: Maximum wait time in seconds.
            max_round: Maximum number of flick attempts.
            max_align: Maximum attempts to align all borders of the element
                within the area (view) border.
            min_xycmp: Minimum x and y components to avoid being mistaken
                as a click **during alignment**.
                Should be considered along with `duration`.
            duration: **Alignment** (not flick) duration in milliseconds.
                If too short, it may be mistaken as a click.
                Should be considered along with `min_xycmp`.

        Examples:
            ::

                from huskium import Offset, Area

                # Filck by default.
                # Offset.UP (sx, sy, ex, ey) = (0.5, 0.75, 0.5, 0.25)
                # Area.FULL (x, y, w, h) = (0.0, 0.0, 1.0, 1.0)
                # offset x: Fixed 0.5 of current window width.
                # offset y: From 0.75 to 0.25 of current window height.
                my_page.target_element.filck_by()

                # Filck to the direction using Offset.
                my_page.target_element.filck_by(Offset.DOWN)
                my_page.target_element.filck_by(Offset.UPPER_LEFT)

                # Filck with customize relative offset.
                my_page.target_element.filck_by((0.3, 0.85, 0.5, 0.35))

                # Filck within a filckable range.
                # Get the absolute area rect using the scrollable element.
                area = my_page.scrollable_element.rect
                my_page.target_element.filck_by((0.3, 0.85, 0.5, 0.35), area)

                # Filck with customize absolute offset.
                my_page.target_element.filck_by((250, 300, 400, 700))

                # Filck with customize relative offset of customize relative area.
                # The area is relative to current window rect, for example:
                # current window rect = (10, 20, 500, 1000)
                # area = (0.1, 0.2, 0.6, 0.7)
                # area_x = 10 + 500 x 0.1 = 60
                # area_y = 20 + 1000 x 0.2 = 220
                # area_width = 500 x 0.6 = 300
                # area_height = 1000 x 0.7 = 700
                my_page.target_element.filck_by(
                    (0.3, 0.85, 0.5, 0.35), (0.1, 0.2, 0.6, 0.7)
                )

                # Filck with customize relative offset of customize absolute area.
                my_page.target_element.filck_by(
                    (0.3, 0.85, 0.5, 0.35), (100, 150, 300, 700)
                )

        """
        area = self.page._get_area(area)
        offset = self.page._get_offset(offset, area)
        self._flick_by(offset, timeout, max_round)
        self._align_by(area, max_align, min_xycmp, duration)
        return self

    def _swipe_by(
        self,
        offset: tuple[int, int, int, int],
        timeout: int | float,
        max_round: int,
        duration: int
    ) -> int | None:
        if not max_round:
            self.logger.warning(f'For max_round is {max_round}, no swiping performed.')
            return None
        self.logger.debug('Start swiping.')
        round = 0
        while not self.is_viewable(timeout):
            if round == max_round:
                self.logger.warning(f'Stop swiping. Element remains not viewable after max {max_round} rounds.\n')
                return round
            self.driver.swipe(*offset, duration)  # type: ignore[attr-defined]
            round += 1
            self.logger.debug(f'Swiping round {round} done.\n')
        self.logger.debug(f'Stop swiping. Element is viewable after {round} rounds.\n')
        return round

    def _flick_by(
        self,
        offset: tuple[int, int, int, int],
        timeout: int | float,
        max_round: int
    ) -> int | None:
        if not max_round:
            self.logger.warning(f'For max_round is {max_round}, no flicking performed.')
            return None
        self.logger.debug('Start flicking.')
        round = 0
        while not self.is_viewable(timeout):
            if round == max_round:
                self.logger.warning(
                    f'Stop flicking. Element remains not viewable after max {max_round} rounds.\n')
                return round
            self.driver.flick(*offset)  # type: ignore[attr-defined]
            round += 1
            self.logger.debug(f'Flicking round {round} done.\n')
        self.logger.debug(f'Stop flicking. Element is viewable after {round} rounds.\n')
        return round

    def _align_by(
        self,
        area: tuple[int, int, int, int],
        max_align: int,
        min_xycmp: int,
        duration: int
    ) -> int | None:

        if not max_align:
            self.logger.debug(f'For max_align is {max_align}, no alignment performed.')
            return None

        self.logger.debug('Start aligning.')

        # Area critical points
        al, at, aw, ah = area  # rect
        ar, ab = (al + aw), (at + ah)  # right, bottom
        ahw, ahh = int(aw / 2), int(ah / 2)  # half_width, half_height
        acx, acy = (al + ahw), (at + ahh)  # center_x, center_y
        area_border = (al, ar, at, ab)
        self.logger.debug(f'AREA(l, r, t, b) = {area_border}')
        area_halfwh = (ahw, ahh)
        self.logger.debug(f'AREA(hw, hh) = {area_halfwh}')
        area_center = (acx, acy)
        self.logger.debug(f'AREA(cx, cy) = {area_center}')

        round = 0
        while (aligned_offset := self._get_aligned_offset(area_border, area_halfwh, area_center, min_xycmp)):
            if round == max_align:
                self.logger.debug(f'Stop aligning after max {max_align} rounds.\n')
                return round
            self.driver.swipe(*aligned_offset, duration)  # type: ignore[attr-defined]
            round += 1
            self.logger.debug(f'Aligning round {round} done.\n')
        self.logger.debug(f'Stop aligning after {round} round.\n')
        return round

    def _get_aligned_offset(
        self,
        area_border: tuple[int, int, int, int],
        area_halfwh: tuple[int, int],
        area_center: tuple[int, int],
        min_xycmp: int,
    ) -> tuple[int, int, int, int] | None:

        # area critical points
        al, ar, at, ab = area_border
        max_xcmp, max_ycmp = area_halfwh
        oex, oey = acx, acy = area_center

        # element border
        element_border = el, er, et, eb = tuple(self.border.values())
        self.logger.debug(f'ELEMENT(l, r, t, b) = {(element_border)}')

        # delta = (area - element)
        delta_border = dl, dr, dt, db = (al - el), (ar - er), (at - et), (ab - eb)
        self.logger.debug(f'DELTA(l, r, t, b) = {delta_border}')

        # align action = (l>0, r<0, t>0, b<0)
        align = align_dl, align_dr, align_dt, align_db = (dl > 0), (dr < 0), (dt > 0), (db < 0)
        self.logger.debug(f'ALIGN(l>0, r<0, t>0, b<0) = {align}')

        # update delta with min_distance
        if align_dl:
            dl = max(min(dl, max_xcmp), min_xycmp)  # max_xcmp >= dl >= min_xycmp > 0
            oex = acx + dl
            self.logger.debug(f'O(ex) = A(cx) + D{[min_xycmp, max_xcmp]}(l) = {acx} + {dl} = {oex}')
        if align_dr:
            dr = min(max(dr, -max_xcmp), -min_xycmp)  # 0 > -min_xycmp >= dr >= -max_xcmp
            oex = acx + dr
            self.logger.debug(f'O(ex) = A(cx) + D{[-min_xycmp, -max_xcmp]}(r) = {acx} + {dr} = {oex}')
        if align_dt:
            dt = max(min(dt, max_ycmp), min_xycmp)  # max_ycmp >= dt >= min_xycmp > 0
            oey = acy + dt
            self.logger.debug(f'O(ey) = A(cy) + D{[min_xycmp, max_ycmp]}(t) = {acy} + {dt} = {oey}')
        if align_db:
            db = min(max(db, -max_ycmp), -min_xycmp)  # 0 > -min_xycmp >= db >= -max_ycmp
            oey = acy + db
            self.logger.debug(f'O(ey) = A(cy) + D{[-min_xycmp, -max_ycmp]}(b) = {acy} + {db} = {oey}')

        # check if adjustment is needed
        if (oex, oey) == area_center:
            self.logger.debug('All the element border is in Area, no alignment required.')
            return None
        offset = (acx, acy, oex, oey)
        self.logger.debug(f'OFFSET(sx, sy, ex, ey) = {offset}')
        return offset

    # ==================================================================================================================
    # Select Process
    # ==================================================================================================================

    @property
    def options(self) -> list[WebElement]:
        """
        Select API.
        Returns a list of all options belonging to this select tag.
        """
        try:
            return self.select_try.options
        except ELEMENT_REFERENCE_EXCEPTIONS:
            return self.select.options

    @property
    def all_selected_options(self) -> list[WebElement]:
        """
        Select API.
        Returns a list of all selected options belonging to this select tag.
        """
        try:
            return self.select_try.all_selected_options
        except ELEMENT_REFERENCE_EXCEPTIONS:
            return self.select.all_selected_options

    @property
    def first_selected_option(self) -> WebElement:
        """
        Select API.
        The first selected option in this select tag,
        or the currently selected option in a normal select.
        """
        try:
            return self.select_try.first_selected_option
        except ELEMENT_REFERENCE_EXCEPTIONS:
            return self.select.first_selected_option

    def select_by_value(self, value: str) -> None:
        """
        Select API.
        Select all options that have a value matching the argument.

        That is, when given "foo" this would select an option like:
        `<option value="foo">Bar</option>`

        Args:
            value: The value to match against.
        """
        try:
            self.select_try.select_by_value(value)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.select.select_by_value(value)

    def select_by_index(self, index: int) -> None:
        """
        Select API.
        Select the option at the given index.

        This is done by examining the "index" attribute of an element,
        and not merely by counting.

        Args:
            index: The option at this index will be selected,
                throws `NoSuchElementException` if there is no option
                with specified index in SELECT.
        """
        try:
            self.select_try.select_by_index(index)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.select.select_by_index(index)

    def select_by_visible_text(self, text: str) -> None:
        """
        Select API.
        Select all options that display text matching the argument.

        That is, when given "Bar" this would select an option like:
        `<option value="foo">Bar</option>`

        Args:
            text: The visible text to match against,
                throws `NoSuchElementException` if there is no option
                with specified text in SELECT.
        """
        try:
            self.select_try.select_by_visible_text(text)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.select.select_by_visible_text(text)

    def deselect_all(self) -> None:
        """
        Select API. Clear all selected entries.
        This is only valid when the SELECT supports multiple selections.
        """
        try:
            self.select_try.deselect_all()
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.select.deselect_all()

    def deselect_by_value(self, value: str) -> None:
        """
        Select API.
        Deselect all options that have a value matching the argument.
        That is, when given "foo" this would deselect an option like:
        `<option value="foo">Bar</option>`.

        Args:
            value: The value to match against.
        """
        try:
            self.select_try.deselect_by_value(value)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.select.deselect_by_value(value)

    def deselect_by_index(self, index: int) -> None:
        """
        Select API.
        Deselect the option at the given index.
        This is done by examining the "index" attribute of an element,
        and not merely by counting.

        Args:
            index: The option at this index will be deselected.
        """
        try:
            self.select_try.deselect_by_index(index)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.select.deselect_by_index(index)

    def deselect_by_visible_text(self, text: str) -> None:
        """
        Select API.
        Deselect all options that display text matching the argument.
        That is, when given "Bar" this would deselect an option like:
        `<option value="foo">Bar</option>`.

        Args:
            text: The visible text to match against.
        """
        try:
            self.select_try.deselect_by_visible_text(text)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.select.deselect_by_visible_text(text)

    # ==================================================================================================================
    # Others
    # ==================================================================================================================

    def input(self, text: str = '', times: int = 1) -> Self:
        """
        Input text to the element.

        Args:
            text: The text to input.
            times: The number of times to repeat entering the text.

        Examples:
            ::

                my_page.my_element.input('123 456')
                my_page.my_element.input('123').space().input('456')
                my_page.my_element.input('6789', 4)

        """
        try:
            self.present_try.send_keys(text * times)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.present.send_keys(text * times)
        return self

    def enter(self) -> Self:
        """
        Send keys ENTER to the element.

        Examples:
            ::

                my_page.my_element.input('123 456').enter()

        """
        try:
            self.present_try.send_keys(Keys.ENTER)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.present.send_keys(Keys.ENTER)
        return self

    def select_all(self) -> Self:
        """
        **This is NOT Select relative function.**
        Send keys "COMMAND/CONTROL + A" to the element.

        Examples:
            ::

                my_page.my_element.select_all().copy()

        """
        first = Keys.COMMAND if platform.system().lower() == "darwin" else Keys.CONTROL
        try:
            self.present_try.send_keys(first, 'a')
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.present.send_keys(first, 'a')
        return self

    def cut(self) -> Self:
        """
        Send keys "COMMAND/CONTROL + X" to the element.

        Examples:
            ::

                my_page.my_element1.cut()
                my_page.my_element2.paste()

        """
        first = Keys.COMMAND if platform.system().lower() == "darwin" else Keys.CONTROL
        try:
            self.present_try.send_keys(first, 'x')
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.present.send_keys(first, 'x')
        return self

    def copy(self) -> Self:
        """
        Send keys "COMMAND/CONTROL + C" to the element.

        Examples:
            ::

                my_page.my_element1.copy()
                my_page.my_element2.paste()

        """
        first = Keys.COMMAND if platform.system().lower() == "darwin" else Keys.CONTROL
        try:
            self.present_try.send_keys(first, 'c')
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.present.send_keys(first, 'c')
        return self

    def paste(self) -> Self:
        """
        Send keys "COMMAND/CONTROL + V" to the element.

        Examples:
            ::

                my_page.my_element1.copy()
                my_page.my_element2.paste()

        """
        first = Keys.COMMAND if platform.system().lower() == "darwin" else Keys.CONTROL
        try:
            self.present_try.send_keys(first, 'v')
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.present.send_keys(first, 'v')
        return self

    def arrow_left(self, times: int = 1) -> Self:
        """
        Send keys "ARROW_LEFT" to the element.

        Args:
            times: The input times of key.

        Examples:
            ::

                my_page.my_element.arrow_left(3)

        """
        try:
            self.present_try.send_keys(Keys.ARROW_LEFT * times)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.present.send_keys(Keys.ARROW_LEFT * times)
        return self

    def arrow_right(self, times: int = 1) -> Self:
        """
        Selenium API
        Send keys "ARROW_RIGHT" to the element.

        Args:
            times: The input times of key.

        Examples:
            ::

                my_page.my_element.arrow_right(3)

        """
        try:
            self.present_try.send_keys(Keys.ARROW_RIGHT * times)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.present.send_keys(Keys.ARROW_RIGHT * times)
        return self

    def arrow_up(self, times: int = 1) -> Self:
        """
        Send keys "ARROW_UP" to the element.

        Args:
            times: The input times of key.

        Examples:
            ::

                my_page.my_element.arrow_up(3)

        """
        try:
            self.present_try.send_keys(Keys.ARROW_UP * times)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.present.send_keys(Keys.ARROW_UP * times)
        return self

    def arrow_down(self, times: int = 1) -> Self:
        """
        Send keys "ARROW_DOWN" to the element.

        Args:
            - times: The input times of key.

        Examples:
            ::

                my_page.my_element.arrow_down(3)

        """
        try:
            self.present_try.send_keys(Keys.ARROW_DOWN * times)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.present.send_keys(Keys.ARROW_DOWN * times)
        return self

    def backspace(self, times: int = 1) -> Self:
        """
        Send keys BACKSPACE to the element.

        Args:
            times: The input times of key.

        Examples:
            ::

                my_page.my_element.backspace(3).input('123456').enter()

        """
        try:
            self.present_try.send_keys(Keys.BACKSPACE * times)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.present.send_keys(Keys.BACKSPACE * times)
        return self

    def delete(self, times: int = 1) -> Self:
        """
        Send keys DELETE to the element.

        Args:
            times: The input times of key.

        Examples:
            ::

                my_page.my_element.delete(3)

        """
        try:
            self.present_try.send_keys(Keys.DELETE * times)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.present.send_keys(Keys.DELETE * times)
        return self

    def tab(self, times: int = 1) -> Self:
        """
        Send keys TAB to the element.

        Args:
            times: The input times of key.

        Examples:
            ::

                my_page.my_element.tab(2)

        """
        try:
            self.present_try.send_keys(Keys.TAB * times)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.present.send_keys(Keys.TAB * times)
        return self

    def space(self, times: int = 1) -> Self:
        """
        Send keys SPACE to the element.

        Args:
            times: The input times of key.

        Examples:
            ::

                my_page.my_element.space(4)

        """
        try:
            self.present_try.send_keys(Keys.SPACE * times)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.present.send_keys(Keys.SPACE * times)
        return self
