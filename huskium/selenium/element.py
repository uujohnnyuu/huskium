# Author: Johnny Chou
# Email: johnny071531@gmail.com
# PyPI: https://pypi.org/project/huskium/
# GitHub: https://github.com/uujohnnyuu/huskium


from __future__ import annotations

import logging
import time
from typing import Any, cast, Iterable, Literal, Self, Type

from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver.remote.shadowroot import ShadowRoot
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.select import Select

from ..exception import NoSuchCacheException
from ..logging import LogConfig, PageElementLoggerAdapter
from ..wait import Wait
from ..common import _Name
from .by import ByAttr
from .ecex import GenericECEX
from .page import GenericPage


ELEMENT_REFERENCE_EXCEPTIONS = (NoSuchCacheException, StaleElementReferenceException)

LOGGER = logging.getLogger(__name__)
LOGGER.addFilter(LogConfig.PREFIX_FILTER)


class GenericElement[WD: WebDriver, WE: WebElement]:

    _page: GenericPage[WD, WE]
    _wait: Wait
    _synced_cache: bool
    _present_cache: WE
    _visible_cache: WE
    _clickable_cache: WE
    _select_cache: Select

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
        self._verify_data(by, value, index, timeout, cache, remark)
        self._set_data(by, value, index, timeout, cache, remark)

    def __get__(self, instance: GenericPage[WD, WE], owner: Type[GenericPage[WD, WE]]) -> Self:
        """Make "Element" a descriptor of "Page"."""
        self._verify_get(instance, owner)
        if getattr(self, _Name._page, None) is not instance:
            self._page = instance
            self._wait = Wait(instance._driver, 1)
            self._clear_caches()
        self._sync_data()
        return self

    def __set__(self, instance: GenericPage[WD, WE], value: GenericElement) -> None:
        """Set dynamic element by `page.element = Element(...)` pattern."""
        self._verify_set(instance, value)
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
        self._verify_data(by, value, index, timeout, cache, remark)
        self._set_data(by, value, index, timeout, cache, remark)
        self._sync_data()
        self._clear_caches()
        return self

    def _verify_data(
        self,
        by: str | None,
        value: str | None,
        index: int | None,
        timeout: int | float | None,
        cache: bool | None,
        remark: str | None
    ) -> None:
        """Verify basic attributes."""
        self._verify_by(by)
        self._verify_value(value)
        self._verify_index(index)
        self._verify_timeout(timeout)
        self._verify_cache(cache)
        self._verify_remark(remark)

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

    def _verify_by(self, by: Any) -> None:
        if by not in ByAttr.OPTIONAL_VALUES:
            raise ValueError(f'Invalid "by": "{by}". Use values from "By" (from huskium.selenium import By).')

    def _verify_value(self, value: Any) -> None:
        if not isinstance(value, str | None):
            raise TypeError(f'The set "value" must be str, got {type(value).__name__}.')

    def _verify_index(self, index: Any) -> None:
        if not isinstance(index, int | None):
            raise TypeError(f'The set "index" must be int, got {type(index).__name__}.')

    def _verify_timeout(self, timeout: Any) -> None:
        if not isinstance(timeout, int | float | None):
            raise TypeError(f'The set "timeout" must be int or float, got {type(timeout).__name__}.')

    def _verify_cache(self, cache: Any) -> None:
        if not isinstance(cache, bool | None):
            raise TypeError(f'The set "cache" must be bool, got {type(cache).__name__}.')

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
                f'"selenium Element" must be used in "selenium Page" or "appium Page", got {type(instance).__name__}'
            )

    def _verify_descriptor_owner(self, owner: Any) -> None:
        if not issubclass(owner, GenericPage):
            raise TypeError(
                f'"selenium Element" must be used in "selenium Page" or "appium Page", got {type(owner).__name__}'
            )

    def _verify_descriptor_value(self, value: Any) -> None:
        if not isinstance(value, GenericElement):
            raise TypeError(f'Assigned value must be "selenium Element", got {type(value).__name__}.')

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
        self._verify_timeout(value)
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
        self._verify_remark(value)
        self._remark = value or self.default_remark

    @property
    def logger(self) -> PageElementLoggerAdapter:
        """The element logger."""
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
        ignored_exceptions: Type[Exception] | Iterable[Type[Exception]] | None = None
    ) -> Wait:
        """The final WebDriverWait instance."""
        self._wait.timeout = timeout
        self._wait.ignored_exceptions = ignored_exceptions
        return self._wait

    def find_element(self) -> WE:
        """
        Using the traditional `find_element()` or `find_elements()[index]`
        to locate element.
        It is recommended for use in situations where no waiting is required,
        such as the Android UiScrollable locator method.
        """
        if isinstance(self.index, int):
            return cast(WE, self.driver.find_elements(*self.locator)[self.index])
        return cast(WE, self.driver.find_element(*self.locator))

    def _caching(self, name: str) -> Any:
        """
        Return `getattr(self, name)`,
        or raise `NoSuchCacheException` if no cache is available.
        """
        if self.cache and hasattr(self, name):
            return getattr(self, name)
        raise NoSuchCacheException(f'No cache for "{name}", please relocate the element in except.')

    @property
    def present_caching(self) -> WE:
        """
        This attribute must be used with `try-except`.

        Examples:
            ::

                try:
                    self.present_caching.text
                except ELEMENT_REFERENCE_EXCEPTIONS:
                    self.present_element.text

        """
        return self._caching(_Name._present_cache)

    @property
    def visible_caching(self) -> WE:
        """
        This attribute must be used with `try-except`.

        Examples:
            ::

                try:
                    self.visible_caching.text
                except ELEMENT_REFERENCE_EXCEPTIONS:
                    self.visible_element.text

        """
        return self._caching(_Name._visible_cache)

    @property
    def clickable_caching(self) -> WE:
        """
        This attribute must be used with `try-except`.

        Examples:
            ::

                try:
                    self.clickable_caching.click()
                except ELEMENT_REFERENCE_EXCEPTIONS:
                    self.clickable_element.click()

        """
        return self._caching(_Name._clickable_cache)

    @property
    def select_caching(self) -> Select:
        """
        This attribute must be used with `try-except`.

        Examples:
            ::

                try:
                    self.select_caching.options
                except ELEMENT_REFERENCE_EXCEPTIONS:
                    self.select.options

        """
        return self._caching(_Name._select_cache)

    def _cache_present_element(self, element: WE | Any):
        """Cache the present element if caching is enabled."""
        if self.cache and isinstance(element, WebElement):
            self._present_cache = cast(WE, element)

    def _cache_visible_element(self, element: WE | Any, extra: bool = True):
        """
        Cache the element as present and visible
        if caching is enabled and extra conditions are met.
        """
        if self.cache and isinstance(element, WebElement) and extra:
            self._visible_cache = self._present_cache = cast(WE, element)

    def _cache_clickable_element(self, element: WE | Any, extra: bool = True):
        """
        Cache the element as present, visible, and clickable
        if caching is enabled and extra conditions are met.
        """
        if self.cache and isinstance(element, WebElement) and extra:
            self._clickable_cache = self._visible_cache = self._present_cache = cast(WE, element)

    def _cache_select(self, select: Select):
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
    ) -> WE | Literal[False]:
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
                GenericECEX[WD, WE].presence_of_element_located(self.locator, self.index)
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
                GenericECEX[WD, WE].absence_of_element_located(self.locator, self.index)
            )
        except TimeoutException as exc:
            return self._timeout_process('absent', exc, reraise)

    def wait_visible(
        self,
        timeout: int | float | None = None,
        reraise: bool | None = None
    ) -> WE | Literal[False]:
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
                    GenericECEX[WD, WE].visibility_of_element(self.present_caching)
                )
                return self._visible_cache
            except ELEMENT_REFERENCE_EXCEPTIONS:
                element = self.waiting(timeout, StaleElementReferenceException).until(
                    GenericECEX[WD, WE].visibility_of_element_located(self.locator, self.index)
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
    ) -> WE | bool:
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
                    WE | Literal[True],
                    self.waiting(timeout).until(
                        GenericECEX[WD, WE].invisibility_of_element(self.present_caching, present)
                    )
                )
            except ELEMENT_REFERENCE_EXCEPTIONS:
                element_or_true = self.waiting(timeout, StaleElementReferenceException).until(
                    GenericECEX[WD, WE].invisibility_of_element_located(self.locator, self.index, present)
                )
                self._cache_present_element(element_or_true)
                return cast(WE | Literal[True], element_or_true)
        except TimeoutException as exc:
            return self._timeout_process('invisible', exc, reraise, present)

    def wait_clickable(
        self,
        timeout: int | float | None = None,
        reraise: bool | None = None
    ) -> WE | Literal[False]:
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
                    GenericECEX[WD, WE].element_to_be_clickable(self.present_caching)
                )
                return self._clickable_cache
            except ELEMENT_REFERENCE_EXCEPTIONS:
                element = self.waiting(timeout, StaleElementReferenceException).until(
                    GenericECEX[WD, WE].element_located_to_be_clickable(self.locator, self.index)
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
    ) -> WE | bool:
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
                    WE | Literal[True],
                    self.waiting(timeout).until(
                        GenericECEX[WD, WE].element_to_be_unclickable(self.present_caching, present)
                    )
                )
            except ELEMENT_REFERENCE_EXCEPTIONS:
                element_or_true = self.waiting(timeout, StaleElementReferenceException).until(
                    GenericECEX[WD, WE].element_located_to_be_unclickable(self.locator, self.index, present)
                )
                self._cache_present_element(element_or_true)
                return cast(WE | Literal[True], element_or_true)
        except TimeoutException as exc:
            return self._timeout_process('unclickable', exc, reraise, present)

    def wait_selected(
        self,
        timeout: int | float | None = None,
        reraise: bool | None = None
    ) -> WE | Literal[False]:
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
                    GenericECEX[WD, WE].element_to_be_selected(self.present_caching)
                )
            except ELEMENT_REFERENCE_EXCEPTIONS:
                element = self.waiting(timeout, StaleElementReferenceException).until(
                    GenericECEX[WD, WE].element_located_to_be_selected(self.locator, self.index)
                )
                self._cache_present_element(element)
                return element
        except TimeoutException as exc:
            return self._timeout_process('selected', exc, reraise)

    def wait_unselected(
        self,
        timeout: int | float | None = None,
        reraise: bool | None = None
    ) -> WE | Literal[False]:
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
                    GenericECEX[WD, WE].element_to_be_unselected(self.present_caching)
                )
            except ELEMENT_REFERENCE_EXCEPTIONS:
                element = self.waiting(timeout, StaleElementReferenceException).until(
                    GenericECEX[WD, WE].element_located_to_be_unselected(self.locator, self.index)
                )
                self._cache_present_element(element)
                return element
        except TimeoutException as exc:
            return self._timeout_process('unselected', exc, reraise)

    @property
    def present_element(self) -> WE:
        """ The same as `element.wait_present(reraise=True)`."""
        return cast(WE, self.wait_present(reraise=True))

    @property
    def visible_element(self) -> WE:
        """The same as element.wait_visible(reraise=True)."""
        return cast(WE, self.wait_visible(reraise=True))

    @property
    def clickable_element(self) -> WE:
        """The same as element.wait_clickable(reraise=True)."""
        return cast(WE, self.wait_clickable(reraise=True))

    @property
    def select(self) -> Select:
        """The Select instance used by the present element."""
        try:
            select = Select(self.present_caching)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            select = Select(self.present_element)
        self._cache_select(select)
        return select

    @property
    def present_cache(self) -> WE | None:
        """The present element cache, `None` otherwise."""
        return getattr(self, _Name._present_cache, None)

    @property
    def visible_cache(self) -> WE | None:
        """The visible element cache, `None` otherwise."""
        return getattr(self, _Name._visible_cache, None)

    @property
    def clickable_cache(self) -> WE | None:
        """The clickable element cache, `None` otherwise."""
        return getattr(self, _Name._clickable_cache, None)

    @property
    def select_cache(self) -> Select | None:
        """The Select instance, `None` otherwise."""
        return getattr(self, _Name._select_cache, None)

    def is_present(self, timeout: int | float | None = None) -> bool:
        """Whether the element is present within the timeout."""
        return bool(self.wait_present(timeout, False))

    def is_visible(self) -> bool:
        """Whether the element is visible (displayed)."""
        try:
            element = self.present_caching
            result = element.is_displayed()
        except ELEMENT_REFERENCE_EXCEPTIONS:
            element = self.present_element
            result = element.is_displayed()
        self._cache_visible_element(element, result)
        return result

    def is_enabled(self) -> bool:
        """Whether the element is enabled."""
        try:
            return self.present_caching.is_enabled()
        except ELEMENT_REFERENCE_EXCEPTIONS:
            return self.present_element.is_enabled()

    def is_clickable(self) -> bool:
        """Whether the element is clickable (displayed and enabled)."""
        try:
            element = self.present_caching
            result = element.is_displayed() and element.is_enabled()
        except ELEMENT_REFERENCE_EXCEPTIONS:
            element = self.present_element
            result = element.is_displayed() and element.is_enabled()
        self._cache_clickable_element(element, result)
        return result

    def is_selected(self) -> bool:
        """Whether the element is selected."""
        try:
            return self.present_caching.is_selected()
        except ELEMENT_REFERENCE_EXCEPTIONS:
            return self.present_element.is_selected()

    @property
    def text(self) -> str:
        """The text of the element when it is present."""
        try:
            return self.present_caching.text
        except ELEMENT_REFERENCE_EXCEPTIONS:
            return self.present_element.text

    @property
    def visible_text(self) -> str:
        """The text of the element when it is visible."""
        try:
            return self.visible_caching.text
        except ELEMENT_REFERENCE_EXCEPTIONS:
            return self.visible_element.text

    @property
    def tag_name(self) -> str:
        """The tagName property."""
        try:
            return self.present_caching.tag_name
        except ELEMENT_REFERENCE_EXCEPTIONS:
            return self.present_element.tag_name

    @property
    def rect(self) -> dict:
        """
        The location and size of the element.
        For example: `{'x': 10, 'y': 15, 'width': 100, 'height': 200}`.
        """
        try:
            rect = self.present_caching.rect
        except ELEMENT_REFERENCE_EXCEPTIONS:
            rect = self.present_element.rect
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
            return self.present_caching.location
        except ELEMENT_REFERENCE_EXCEPTIONS:
            return self.present_element.location

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
            return self.present_caching.location_once_scrolled_into_view
        except ELEMENT_REFERENCE_EXCEPTIONS:
            return self.present_element.location_once_scrolled_into_view

    @property
    def size(self) -> dict:
        """
        The size of the element.
        For example: `{'width': 200, 'height': 100}`.
        """
        try:
            size = self.present_caching.size
        except ELEMENT_REFERENCE_EXCEPTIONS:
            size = self.present_element.size
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
            rect = self.present_caching.rect
        except ELEMENT_REFERENCE_EXCEPTIONS:
            rect = self.present_element.rect
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
            rect = self.present_caching.rect
        except ELEMENT_REFERENCE_EXCEPTIONS:
            rect = self.present_element.rect
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
            return self.present_caching.shadow_root
        except ELEMENT_REFERENCE_EXCEPTIONS:
            return self.present_element.shadow_root

    @property
    def aria_role(self) -> str:
        """The ARIA role of the current web element."""
        try:
            return self.present_caching.aria_role
        except ELEMENT_REFERENCE_EXCEPTIONS:
            return self.present_element.aria_role

    @property
    def accessible_name(self) -> str:
        """The ARIA Level of the current web element."""
        try:
            return self.present_caching.accessible_name
        except ELEMENT_REFERENCE_EXCEPTIONS:
            return self.present_element.accessible_name

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
            return self.present_caching.get_dom_attribute(name)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            return self.present_element.get_dom_attribute(name)

    def get_attribute(self, name: str) -> str | dict | None:
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
            return self.present_caching.get_attribute(name)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            return self.present_element.get_attribute(name)

    def get_property(self, name: Any) -> str | bool | dict | WE:
        """
        Gets the given property of the element.

        Args:
            name: Name of the property to retrieve.

        Examples:
            ::

                text_length = target_element.get_property("text_length")

        """
        try:
            return cast(str | bool | dict | WE, self.present_caching.get_property(name))
        except ELEMENT_REFERENCE_EXCEPTIONS:
            return cast(str | bool | dict | WE, self.present_element.get_property(name))

    def value_of_css_property(self, property_name: Any) -> str:
        """
        The value of a CSS property.

        Examples:
            ::

                page.element.value_of_css_property('color')

        """
        try:
            return self.present_caching.value_of_css_property(property_name)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            return self.present_element.value_of_css_property(property_name)

    def visible_value_of_css_property(self, property_name: Any) -> str:
        """
        The visible value of a CSS property.

        Examples:
            ::

                page.element.visible_value_of_css_property('color')

        """
        try:
            return self.visible_caching.value_of_css_property(property_name)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            return self.visible_element.value_of_css_property(property_name)

    def click(self) -> None:
        """Click the element when it is clickable."""
        try:
            self.clickable_caching.click()
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.clickable_element.click()

    def delayed_click(self, sleep: int | float = 0.5) -> None:
        """
        Clicks the element after it becomes clickable,
        with a specified delay (sleep) in seconds.
        """
        try:
            cache = self.clickable_caching
            time.sleep(sleep)
            cache.click()
        except ELEMENT_REFERENCE_EXCEPTIONS:
            element = self.clickable_element
            time.sleep(sleep)
            element.click()

    def clear(self) -> Self:
        """
        Clear the text of the field type element.

        Examples:
            ::

                my_page.my_element.clear()
                my_page.my_element.clear().send_keys('my text')

        """
        try:
            self.clickable_caching.clear()
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.clickable_element.clear()
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
            self.clickable_caching.send_keys(*value)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.clickable_element.send_keys(*value)
        return self

    def submit(self) -> None:
        """Submits a form."""
        try:
            self.present_caching.submit()
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.present_element.submit()

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
            return self.present_caching.screenshot(filename)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            return self.present_element.screenshot(filename)

    def perform(self) -> None:
        """
        ActionChains API. Performs all stored actions.

        Examples:
            ::

                # Basic usage. Execute element actions.
                page.element.scroll_to_element().clicks().perform()

                # Multiple actions to call, set perform to the last action.
                # This will execute all actions in page not just page.element2.
                page.element1.scroll_to_element().clicks()
                page.element2.drag_and_drop(page.element3).perform()

                # As above, it is the same to call perform by page:
                page.element1.scroll_to_element().clicks()
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
                page.element1.scroll_to_element().clicks()
                page.element2.click_and_hold().reset_actions()

                # There is a better one structure,
                # reset all action calls made by page.
                page.element1.scroll_to_element().clicks()
                page.element2.click_and_hold()
                page.reset_actions()

        """
        self.action.reset_actions()

    def clicks_on_element(self) -> Self:
        """
        ActionChains API.
        Moves the mouse to the element's center and clicks it.

        Examples:
            ::

                page.element.clicks_on_element().perform()

                # or
                page.element.move_to_element().clicks().perform()

        """
        try:
            self.action.click(self.present_caching)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.action.click(self.present_element)
        return self

    def clicks(self) -> Self:
        """
        ActionChains API.
        Clicks on the current mouse position.

        Examples:
            ::

                page.element.move_to_element().clicks().perform()

                # or
                page.element.clicks_on_element().perform()

        """
        self.action.click()
        return self

    def click_and_hold_on_element(self) -> Self:
        """
        ActionChains API.
        Moves the mouse to the element's center
        and holds down the left mouse button it.

        Examples:
            ::

                page.element.click_and_hold_on_element().perform()

                # or
                page.element.move_to_element().click_and_hold().perform()

        """
        try:
            self.action.click_and_hold(self.present_caching)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.action.click_and_hold(self.present_element)
        return self

    def click_and_hold(self) -> Self:
        """
        ActionChains API.
        Holds down the left mouse button on the current mouse position.

        Examples:
            ::

                page.element.move_to_element().click_and_hold().perform()

                # or
                page.element.click_and_hold_on_element().perform()

        """
        self.action.click_and_hold()
        return self

    def context_click_on_element(self) -> Self:
        """
        ActionChains API.
        Moves the mouse to the element's center
        and performs a context-click (right click) on it.

        Examples:
            ::

                page.element.context_click_on_element().perform()

                # or
                page.element.move_to_element().context_click().perform()

        """
        try:
            self.action.context_click(self.present_caching)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.action.context_click(self.present_element)
        return self

    def context_click(self) -> Self:
        """
        ActionChains API.
        Performs a context-click (right click) on the current mouse position.

        Examples:
            ::

                page.element.move_to_element().context_click().perform()

                # or
                page.element.context_click_on_element().perform()

        """
        self.action.context_click()
        return self

    def double_click_on_element(self) -> Self:
        """
        ActionChains API.
        Moves the mouse to the element's center and double-clicks it.

        Examples:
            ::

                page.element.double_click_on_element().perform()

                # or
                page.element.move_to_element().double_click().perform()

        """
        try:
            self.action.double_click(self.present_caching)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.action.double_click(self.present_element)
        return self

    def double_click(self) -> Self:
        """
        ActionChains API.
        Double-clicks an element on the current mouse position.

        Examples:
            ::

                page.element.move_to_element().double_click().perform()

                # or
                page.element.double_click_on_element().perform()

        """
        self.action.double_click()
        return self

    def drag_and_drop(self, target: Element) -> Self:
        """
        ActionChains API.
        Holds down the left mouse button on the source element,
        then moves to the target element and releases the mouse button.

        Examples:
            ::

                page.element1.drag_and_drop(page.element2).perform()

        """
        try:
            self.action.drag_and_drop(self.present_caching, target.present_caching)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.action.drag_and_drop(self.present_element, target.present_element)
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

                page.element.drag_and_drop_by_offset(100, 200).perform()

        """
        try:
            self.action.drag_and_drop_by_offset(self.present_caching, xoffset, yoffset)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.action.drag_and_drop_by_offset(self.present_element, xoffset, yoffset)
        return self

    def send_hotkey_to_element(self, *keys: str) -> Self:
        """
        ActionChains API.
        Clicks the element's center and sends the hotkey sequence to it.

        Examples:
            ::

                page.element1.send_hotkey_to_element(Key.CONTROL, 'a').send_hotkey(Keys.CONTROL, 'c')
                page.element2.send_hotkey_to_element(Keys.CONTROL, 'v').perform()

        """
        # key_down: The first key.
        try:
            self.action.key_down(keys[0], self.present_caching)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.action.key_down(keys[0], self.present_element)
        # key_down: Intermediate keys (excluding first and last).
        for key in keys[1:-1]:  # ignored if only 2 keys
            self.action.key_down(key)
        # send_keys: The last key.
        self.action.send_keys(keys[-1])
        # key_up: All keys except the last, in reverse order.
        for key in keys[-2::-1]:
            self.action.key_up(key)
        return self

    def send_hotkey(self, *keys: str) -> Self:
        """
        ActionChains API.
        Sends the hotkey sequence to the focused position.

        Examples:
            ::

                # Ensure that it is already at the target position or element.
                page.element1.send_hotkey_to_element(Key.CONTROL, 'a').send_hotkey(Keys.CONTROL, 'c')
                page.element2.send_hotkey_to_element(Keys.CONTROL, 'v').perform()

        """
        # key_down: The first to the second last key.
        for key in keys[:-1]:
            self.action.key_down(key)
        # send_keys: The last key.
        self.action.send_keys(keys[-1])
        # key_up: The second last key to the first key.
        for key in keys[-2::-1]:
            self.action.key_up(key)
        return self

    def key_down_to_element(self, key: str) -> Self:
        """
        ActionChains API.
        Clicks the element's center and sends a modifier key press only.

        If you want to perform a combination key action, such as copying,
        it is recommended to use `send_hotkey_to_element()` instead.

        Examples:
            ::

                # ctrl+a, ctrl+c
                page.element.key_down_to_element(Key.CONTROL).sends_keys('a').key_up(Key.CONTROL)\
                .key_down(Key.CONTROL).sends_keys('c').key_up(Key.CONTROL).perform()

                # or using send_hotkey()
                page.element.send_hotkey_to_element(Key.CONTROL, 'a').send_hotkey(Keys.CONTROL, 'c').perform()

        """
        try:
            self.action.key_down(key, self.present_caching)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.action.key_down(key, self.present_element)
        return self

    def key_down(self, key: str) -> Self:
        """
        ActionChains API.
        Sends only a modifier key press at the current focused position.

        If you want to perform a combination key action, such as copying,
        it is recommended to use `send_hotkey()` instead.

        Examples:
            ::

                # ctrl+a, ctrl+c
                page.element.key_down_to_element(Key.CONTROL).sends_keys('a').key_up(Key.CONTROL)\
                .key_down(Key.CONTROL).sends_keys('c').key_up(Key.CONTROL).perform()

                # or using send_hotkey()
                page.element.send_hotkey_to_element(Key.CONTROL, 'a').send_hotkey(Keys.CONTROL, 'c').perform()

        """
        self.action.key_down(key)
        return self

    def key_up_to_element(self, key: str) -> Self:
        """
        ActionChains API.
        Clicks the element's center and releases a modifier key.

        If you want to perform a combination key action, such as copying,
        it is recommended to use `send_hotkey_to_element()` instead.

        Examples:
            ::

                # ctrl+a, ctrl+c
                page.element.key_down_to_element(Key.CONTROL).sends_keys('a').key_up(Key.CONTROL)\
                .key_down(Key.CONTROL).sends_keys('c').key_up(Key.CONTROL).perform()

                # or using send_hotkey()
                page.element.send_hotkey_to_element(Key.CONTROL, 'a').send_hotkey(Keys.CONTROL, 'c').perform()

        """
        try:
            self.action.key_up(key, self.present_caching)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.action.key_up(key, self.present_element)
        return self

    def key_up(self, key: str) -> Self:
        """
        ActionChains API.
        Releases a modifier key at the current focused position.

        If you want to perform a combination key action, such as copying,
        it is recommended to use `send_hotkey()` instead.

        Examples:
            ::

                # ctrl+a, ctrl+c
                page.element.key_down_to_element(Key.CONTROL).sends_keys('a').key_up(Key.CONTROL)\
                .key_down(Key.CONTROL).sends_keys('c').key_up(Key.CONTROL).perform()

                # or using send_hotkey()
                page.element.send_hotkey_to_element(Key.CONTROL, 'a').send_hotkey(Keys.CONTROL, 'c').perform()

        """
        self.action.key_up(key)
        return self

    def move_by_offset(self, xoffset: int, yoffset: int) -> Self:
        """
        ActionChains API.
        Moving the mouse to an offset from current mouse position.

        Args:
            xoffset: X offset to move to, as a positive or negative integer.
            yoffset: Y offset to move to, as a positive or negative integer.

        Examples:
            ::

                page.element.move_to_element().move_by_offset(100, 200).perform()

        """
        self.action.move_by_offset(xoffset, yoffset)
        return self

    def move_to_element(self) -> Self:
        """
        ActionChains API.
        Moving the mouse to the middle of an element.

        Examples:
            ::

                page.element.scroll_to_element().move_to_element().perform()

        """
        try:
            self.action.move_to_element(self.present_caching)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.action.move_to_element(self.present_element)
        return self

    def move_to_element_with_offset(self, xoffset: int, yoffset: int) -> Self:
        """
        ActionChains API.
        Move the mouse by an offset of the specified element.
        Offsets are relative to the in-view center point of the element.

        Args:
            xoffset: X offset to move to, as a positive or negative integer.
            yoffset: Y offset to move to, as a positive or negative integer.

        Examples:
            ::

                page.element.scroll_to_element().move_to_element_with_offset(100, 200).perform()

        """
        try:
            self.action.move_to_element_with_offset(self.present_caching, xoffset, yoffset)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.action.move_to_element_with_offset(self.present_element, xoffset, yoffset)
        return self

    def pause(self, seconds: int | float) -> Self:
        """
        ActionChains API.
        Pause all inputs for the specified duration in seconds.
        """
        self.action.pause(seconds)
        return self

    def release_on_element(self) -> Self:
        """
        ActionChains API.
        Releasing a held mouse button on an element.

        Examples:
            ::

                page.element.release_on_element().perform()

        """
        try:
            self.action.release(self.present_caching)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.action.release(self.present_element)
        return self

    def release(self) -> Self:
        """
        ActionChains API.
        Releasing a held mouse button on the current position.

        Examples:
            ::

                page.element.click_and_hold_on_element().release().perform()

        """
        self.action.release()
        return self

    def sends_keys_to_element(self, *keys: str) -> Self:
        """
        ActionChains API.
        Sends keys to an element.

        Examples:
            ::

                page.element.sends_keys_to_element('some text', Keys.ENTER)

        """
        try:
            self.action.send_keys_to_element(self.present_caching, *keys)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.action.send_keys_to_element(self.present_element, *keys)
        return self

    def sends_keys(self, *keys: str) -> Self:
        """
        ActionChains API.
        Sends keys to the current focused position.

        Examples:
            ::

                # Combine with key_down() and key_up()
                page.element.key_down_to_element(Key.CONTROL).sends_keys('a').key_up(Key.CONTROL).perform()

        """
        self.action.send_keys(*keys)
        return self

    def scroll_to_element(self) -> Self:
        """
        ActionChains API.
        If the element is outside the viewport,
        scrolls the bottom of the element to the bottom of the viewport.

        Examples:
            ::

                page.element.scroll_to_element().clicks().perform()

        """
        try:
            self.action.scroll_to_element(self.present_caching)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.action.scroll_to_element(self.present_element)
        return self

    def scroll_by_amount(self, delta_x: int, delta_y: int) -> Self:
        """
        ActionChains API.
        Scrolls by provided amounts with the origin
        in the top left corner of the viewport.

        Args:
            delta_x: Distance along X axis to scroll using the wheel.
                A negative value scrolls left.
            delta_y: Distance along Y axis to scroll using the wheel.
                A negative value scrolls up.

        Examples:
            ::

                page.element.move_to_element().scroll_by_amount(100, 200).perform()

        """
        self.action.scroll_by_amount(delta_x, delta_y)
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

                page.element.scroll_from_element(-30, -50, 150, 100).clicks().perform()

        """
        try:
            scroll_origin = ScrollOrigin.from_element(self.present_caching, x_offset, y_offset)
            self.action.scroll_from_origin(scroll_origin, delta_x, delta_y)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            scroll_origin = ScrollOrigin.from_element(self.present_element, x_offset, y_offset)
            self.action.scroll_from_origin(scroll_origin, delta_x, delta_y)
        return self

    def scroll_from_origin(
        self,
        x_offset: int = 0,
        y_offset: int = 0,
        delta_x: int = 0,
        delta_y: int = 0,
    ) -> Self:
        """
        ActionChains API.
        Scrolls by provided amount based on a provided origin.
        The scroll origin is the upper left of the viewport plus any offsets.

        Args:
            x_offset: from origin viewport, a negative value offset left.
            y_offset: from origin viewport, a negative value offset up.
            delta_x: Distance along X axis to scroll using the wheel.
                A negative value scrolls left.
            delta_y: Distance along Y axis to scroll using the wheel.
                A negative value scrolls up.

        Raises:
            MoveTargetOutOfBoundsException: If the origin with offset is
                outside the viewport.

        Examples:
            ::

                page.element.scroll_to_element().scroll_from_origin(150, 100, 100, 200).perform()

        """
        scroll_origin = ScrollOrigin.from_viewport(x_offset, y_offset)
        self.action.scroll_from_origin(scroll_origin, delta_x, delta_y)
        return self

    @property
    def options(self) -> list[WE]:
        """
        Select API.
        Returns a list of all options belonging to this select tag.
        """
        try:
            return cast(list[WE], self.select_caching.options)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            return cast(list[WE], self.select.options)

    @property
    def all_selected_options(self) -> list[WE]:
        """
        Select API.
        Returns a list of all selected options belonging to this select tag.
        """
        try:
            return cast(list[WE], self.select_caching.all_selected_options)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            return cast(list[WE], self.select.all_selected_options)

    @property
    def first_selected_option(self) -> WE:
        """
        Select API.
        The first selected option in this select tag,
        or the currently selected option in a normal select.
        """
        try:
            return cast(WE, self.select_caching.first_selected_option)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            return cast(WE, self.select.first_selected_option)

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
            self.select_caching.select_by_value(value)
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
            self.select_caching.select_by_index(index)
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
            self.select_caching.select_by_visible_text(text)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.select.select_by_visible_text(text)

    def deselect_all(self) -> None:
        """
        Select API. Clear all selected entries.
        This is only valid when the SELECT supports multiple selections.
        """
        try:
            self.select_caching.deselect_all()
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
            self.select_caching.deselect_by_value(value)
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
            self.select_caching.deselect_by_index(index)
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
            self.select_caching.deselect_by_visible_text(text)
        except ELEMENT_REFERENCE_EXCEPTIONS:
            self.select.deselect_by_visible_text(text)


class Element(GenericElement[WebDriver, WebElement]):
    pass
