# Author: Johnny Chou
# Email: johnny071531@gmail.com
# PyPI: https://pypi.org/project/huskium/
# GitHub: https://github.com/uujohnnyuu/huskium


from __future__ import annotations

import logging
import platform
import time
from typing import TYPE_CHECKING, Any, cast, Literal, Self, Type

from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.types import WaitExcTypes
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.shadowroot import ShadowRoot
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait

from . import ec_extension as ecex
from .by import ByAttribute
from .config import Cache, Timeout, Offset, Area
from .log_filter import PrefixFilter
from .log_adapter import PageElementLoggerAdapter
from .page import Page, Coordinate
from .types import SeleniumWebElement, WebDriver, WebElement


ELEMENT_REFERENCE_EXCEPTION = (AttributeError, StaleElementReferenceException)
EXTENDED_IGNORED_EXCEPTIONS = (StaleElementReferenceException,)

LOGGER = logging.getLogger(__name__)
PREFIX_FILTER = PrefixFilter()
LOGGER.addFilter(PREFIX_FILTER)


class _Name:
    _page = '_page'
    _wait_timeout = '_wait_timeout'
    _present_cache = '_present_cache'
    _visible_cache = '_visible_cache'
    _clickable_cache = '_clickable_cache'
    _select_cache = '_select_cache'
    _caches = [_present_cache, _visible_cache, _clickable_cache, _select_cache]


class Element:

    if TYPE_CHECKING:
        _page: Page
        _driver: WebDriver
        _wait_timeout: int | float
        _present_cache: WebElement
        _visible_cache: WebElement
        _clickable_cache: WebElement
        _select_cache: Select

    def __init__(
        self,
        by: str | None = None,
        value: str | None = None,
        index: int | None = None,
        *,
        timeout: int | float | None = None,
        remark: str | None = None,
        cache: bool | None = None
    ) -> None:
        """
        Initial Element attributes.

        Args:
            - by:
                - None (default): Initialize an empty descriptor.
                - str: Use `from huskium import By` for Selenium and Appium locators.
            - value:
                - None (default): Initialize an empty descriptor.
                - str: The locator value.
            - index:
                - None (default): Uses the `find_element()` strategy.
                - int: Uses the `find_elements()[index]` strategy.
            - timeout:
                - None (default): Uses `Timeout.DEFAULT` in seconds.
                - int, float: Explicit wait time in seconds.
            - remark:
                - None (default): Auto-generates remark info as
                    `(by="{by}", value="{value}", index={index})`.
                - str: Custom remark for identification or logging.
            - cache:
                - None (default): Uses `Cache.Element`, with the default set to True.
                - True: Cache the located WebElement for reuse.
                - False: Do not cache and locate the element every time.
        """
        self._verify_data(by, value, index, timeout, remark, cache)
        self._set_data(by, value, index, timeout, remark, cache)
        self._logger = PageElementLoggerAdapter(LOGGER, type(self).__name__, self.remark)

    def __get__(self, instance: Page, owner: Type[Page] | None = None) -> Self:
        """
        Make "Element" a descriptor of "Page".
        """
        if not isinstance(instance, Page):
            raise TypeError(f'"{type(self).__name__}" must be used with a "Page" instance.')
        # If the stored _page differs from the current value,
        # it indicates the driver has been updated.
        # Assign the current value to _page and clear all caches to avoid InvalidSessionIdException.
        if getattr(self, _Name._page, None) != instance:
            self._page = instance
            self._driver = instance._driver
            self._logger.debug(f'Get new driver {self._driver}.')
            self._if_clear_caches()
        return self

    def __set__(self, instance: Page, value: Element) -> None:
        """
        Set dynamic element by `self.element = Element(...)` pattern.
        """
        if not isinstance(value, Element):
            raise TypeError('Only "Element" objects are allowed to be assigned.')
        # Avoid using self.__init__() here, as it may reset the descriptor.
        # It’s better not to call dynamic, as it will duplicate the verification.
        self._set_data(value.by, value.value, value.index, value.timeout, value.remark, value.cache)
        self._logger.debug('Dynamically set element attributes.')
        self._if_clear_caches()  # dynamic element should clear caches.

    def _exc_info(self, exc: TimeoutException) -> tuple:
        """
        Ignore inner `AttributeError` raised by `self._xxx_cache` and
        StaleElementReferenceException raised by `self._if_force_relocate()`,
        record only the main TimeoutException.

        return `type(exc), exc, exc.__traceback__`
        """
        if isinstance(exc.__context__, ELEMENT_REFERENCE_EXCEPTION):
            exc.__context__ = None
        return type(exc), exc, exc.__traceback__

    def dynamic(
        self,
        by: str,
        value: str,
        index: int | None = None,
        *,
        timeout: int | float | None = None,
        remark: str | None = None,
        cache: bool | None = None
    ) -> Self:
        """
        In a Page subclass, use a data descriptor to define dynamic elements.
        This is a simplified version of the __set__ method.

        Usage::

            # my_page.py
            class MyPage(Page):

                my_static_element = Element()

                def my_dynamic_element(self, id_):
                    return self.my_static_element.dynamic(
                        By.ID, id_,
                        remark="Dynamically set my_static_element."
                    )

            # my_testcase.py
            class MyTestCase:
                ...
                my_page = MyPage(driver)
                # The element ID is dynamic.
                id_ = Server.get_id()
                # Dynamically retrieve the element using any method.
                my_page.my_dynamic_element(id_).text
                # The static element can be used after the dynamic one is set.
                my_page.my_static_element.click()

        """
        # Avoid using self.__init__() here, as it will reset the descriptor.
        self._verify_data(by, value, index, timeout, remark, cache)
        self._set_data(by, value, index, timeout, remark, cache)
        self._if_clear_caches()  # dynamic element should clear caches.
        return self

    def _verify_data(self, by, value, index, timeout, remark, cache) -> None:
        """
        Verify basic attributes.
        """
        if by not in ByAttribute.VALUES_WITH_NONE:
            raise ValueError(f'The locator strategy "{by}" is undefined.')
        if not isinstance(value, (str, type(None))):
            raise TypeError(
                'The locator value type should be "str", '
                f'not "{type(value).__name__}".'
            )
        if not isinstance(index, (int, type(None))):
            raise TypeError(
                'The index type should be "int", '
                f'not "{type(index).__name__}".'
            )
        if not isinstance(timeout, (int, float, type(None))):
            raise TypeError(
                'The timeout type should be "int" or "float", '
                f'not "{type(timeout).__name__}".'
            )
        if not isinstance(remark, (str, type(None))):
            raise TypeError(
                'The remark type should be "str", '
                f'not "{type(remark).__name__}".'
            )
        if not isinstance(cache, (bool, type(None))):
            raise TypeError(
                'The cache type should be "bool", '
                f'not "{type(cache).__name__}".'
            )

    def _set_data(self, by, value, index, timeout, remark, cache) -> None:
        """
        Set basic attributes.
        """
        self._by = by
        self._value = value
        self._index = index
        self._timeout = timeout
        self._remark = remark
        self._cache = cache

    def _if_clear_caches(self) -> None:
        """
        If cache is True, clear all caches.
        """
        if self.cache:
            for cache_name in _Name._caches:
                if vars(self).pop(cache_name, None):
                    self._logger.debug(f'Clear cache <{cache_name}>.', stacklevel=2)

    def _if_force_relocate(self) -> None:
        """
        If cache is False, raise `StaleElementReferenceException` and force relocate the element.
        """
        if not self.cache:
            raise StaleElementReferenceException

    @property
    def by(self) -> str | None:
        return self._by

    @property
    def value(self) -> str | None:
        return self._value

    @property
    def locator(self) -> tuple[str, str]:
        """
        (by, value)
        """
        if self._by and self._value:
            return (self._by, self._value)
        raise ValueError(
            '"by" and "value" cannot be None when performing element operations. '
            'Please ensure both are provided with valid values.'
        )

    @property
    def index(self) -> int | None:
        return self._index

    @property
    def timeout(self) -> int | float:
        """
        If initial timeout is None, return `Timeout.DEFAULT`.
        """
        return Timeout.DEFAULT if self._timeout is None else self._timeout

    @property
    def remark(self) -> str:
        """
        If initial remark is None, return (by="{by}", value="{value}", index={index}).
        """
        return self._remark or f'(by="{self._by}", value="{self._value}", index={self._index})'

    @property
    def cache(self) -> bool:
        """
        If initial cache is None, return `Cache.ELEMENT`.
        """
        return Cache.ELEMENT if self._cache is None else self._cache

    @property
    def driver(self) -> WebDriver:
        return self._driver

    @property
    def action(self) -> ActionChains:
        """
        Get ActionChains object from Page-related instance.
        """
        return self._page._action

    def find_element(self) -> WebElement:
        """
        Using the traditional `find_element()` or
        `find_elements()[index]` (if there is index) to locate element.
        It is recommended for use in situations where no waiting is required,
        such as the Android UiScrollable locator method.
        """
        if isinstance(self.index, int):
            return self.driver.find_elements(*self.locator)[self.index]
        return self.driver.find_element(*self.locator)

    def wait(
        self,
        timeout: int | float | None = None,
        ignored_exceptions: WaitExcTypes | None = None
    ) -> WebDriverWait:
        """
        Get an object of WebDriverWait.

        Args:
            - timeout: The maximum time in seconds to wait for the expected condition.
                By default, it initializes with the element timeout.
            - ignored_exceptions: iterable structure of exception classes ignored during calls.
                By default, it contains NoSuchElementException only.
        """
        self._wait_timeout = self.timeout if timeout is None else timeout
        return WebDriverWait(
            driver=self.driver,
            timeout=self._wait_timeout,
            ignored_exceptions=ignored_exceptions
        )

    @property
    def wait_timeout(self) -> int | float | None:
        """
        Get the final waiting timeout of the element.
        If no element action has been executed yet, it will return None.
        """
        return getattr(self, _Name._wait_timeout, None)

    def _timeout_message(self, status: str, present: bool = True) -> str:
        """
        Timed out waiting {self._wait_timeout} seconds for element "{self.remark}" to be "{status}".
        if not present: status += ' or absent'
        """
        if not present:
            status += ' or absent'
        return (
            f'Timed out waiting {self._wait_timeout} seconds '
            f'for element "{self.remark}" to be "{status}".'
        )

    def _timeout_process(
        self,
        status: str,
        exc: TimeoutException,
        reraise: bool | None = None,
        present: bool = True
    ) -> Literal[False]:
        """
        Handling a TimeoutException after it occurs.
        """
        exc.msg = self._timeout_message(status, present)
        if Timeout.reraise(reraise):
            self._logger.exception(exc.msg, exc_info=self._exc_info(exc), stacklevel=2)
            raise exc from None
        self._logger.warning(exc.msg, exc_info=self._exc_info(exc), stacklevel=2)
        return False

    def wait_present(
        self,
        timeout: int | float | None = None,
        reraise: bool | None = None
    ) -> WebElement | Literal[False]:
        """
        Wait for the element to become present.

        Args:
            - timeout: Maximum wait time (in seconds) for the element to reach the expected state.
                Defaults to the element's timeout value if None.
            - reraise: Determines behavior when the element state is not as expected:
                - bool: True to raise a TimeoutException; False to return False.
                - None: Follows `Timeout.RERAISE`.

        Returns:
            - WebElement: The element reached the expected state within the timeout.
            - False: The element failed to reach the expected state if `reraise` is False.

        Exception:
            - TimeoutException: Raised if `reraise` is True and
                the element did not reach the expected state within the timeout.
        """
        try:
            element = self.wait(timeout).until(
                ecex.presence_of_element_located(self.locator, self.index)
            )
            if self.cache:
                self._present_cache = element
                self._logger.debug(f'locator -> present_cache : {self._present_cache}')
            else:
                self._logger.debug(f'locator -> present_element : {element}')
            return element
        except TimeoutException as exc:
            return self._timeout_process('present', exc, reraise)

    def wait_absent(
        self,
        timeout: int | float | None = None,
        reraise: bool | None = None
    ) -> bool:
        """
        Wait for the element to become absent.

        Args:
            - timeout: Maximum wait time (in seconds) for the element to reach the expected state.
                Defaults to the element's timeout value if None.
            - reraise: Determines behavior when the element state is not as expected:
                - bool: True to raise a TimeoutException; False to return False.
                - None: Follows `Timeout.RERAISE`.

        Returns:
            - WebElement: The element reached the expected state within the timeout.
            - False: The element failed to reach the expected state if `reraise` is False.

        Exception:
            - TimeoutException: Raised if `reraise` is True and
                the element did not reach the expected state within the timeout.
        """
        try:
            true: Literal[True] = self.wait(timeout).until(
                ecex.absence_of_element_located(self.locator, self.index)
            )
            self._logger.debug(f'locator -> absent : {true}')
            return true
        except TimeoutException as exc:
            return self._timeout_process('absent', exc, reraise)

    def wait_visible(
        self,
        timeout: int | float | None = None,
        reraise: bool | None = None
    ) -> WebElement | Literal[False]:
        """
        Wait for the element to become visible.

        Args:
            - timeout: Maximum wait time (in seconds) for the element to reach the expected state.
                Defaults to the element's timeout value if None.
            - reraise: Determines behavior when the element state is not as expected:
                - bool: True to raise a TimeoutException; False to return False.
                - None: Follows `Timeout.RERAISE`.

        Returns:
            - WebElement: The element reached the expected state within the timeout.
            - False: The element failed to reach the expected state if `reraise` is False.

        Exception:
            - TimeoutException: Raised if `reraise` is True and
                the element did not reach the expected state within the timeout.
        """
        try:
            try:
                self._if_force_relocate()
                self._visible_cache = self.wait(timeout).until(
                    ecex.visibility_of_element(self._present_cache)
                )
                self._logger.debug(f'present_cache -> visible_cache : {self._visible_cache}')
                return self._visible_cache
            except ELEMENT_REFERENCE_EXCEPTION:
                element = self.wait(timeout, EXTENDED_IGNORED_EXCEPTIONS).until(
                    ecex.visibility_of_element_located(self.locator, self.index)
                )
                if self.cache:
                    self._visible_cache = self._present_cache = element
                    self._logger.debug(f'locator -> present_cache -> visible_cache : {self._visible_cache}')
                else:
                    self._logger.debug(f'locator -> visible_element : {element}')
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
        Wait for the element to become invisible.

        Args:
            - timeout: Maximum wait time (in seconds) for the element to reach the expected state.
                Defaults to the element's timeout value if None.
            - present: Specifies whether the element should be present:
                - True: The element must be present in the expected state.
                - False: The element can be present in the expected state or absent.
            - reraise: Defines behavior when the element state is not as expected:
                - bool: True to raise a TimeoutException; False to return False.
                - None: Follows `Timeout.RERAISE`, a boolean that defaults to True.

        Returns:
            - WebElement: The element reached the expected state within the timeout.
            - True: The element is absent within the timeout,
                and `present` is False, allowing absence.
            - False: The element failed to reach the expected state
                within the timeout if `reraise` is False.

        Exception:
            - TimeoutException: Raised if `reraise` is True and
                the element did not reach the expected state within the timeout.
        """
        try:
            try:
                self._if_force_relocate()
                element_or_true: WebElement | Literal[True] = self.wait(timeout).until(
                    ecex.invisibility_of_element(self._present_cache, present)
                )
                self._logger.debug(f'present_cache -> invisible({present} : {element_or_true}')
                return element_or_true
            except ELEMENT_REFERENCE_EXCEPTION:
                element_or_true = self.wait(timeout, EXTENDED_IGNORED_EXCEPTIONS).until(
                    ecex.invisibility_of_element_located(self.locator, self.index, present)
                )
                if self.cache and isinstance(element_or_true, WebElement):
                    self._present_cache = element_or_true
                    self._logger.debug(f'locator -> present_cache -> invisible({present} : {self._present_cache}')
                else:
                    self._logger.debug(f'locator -> invisible({present} : {element_or_true}')
                return element_or_true
        except TimeoutException as exc:
            return self._timeout_process('invisible', exc, reraise, present)

    def wait_clickable(
        self,
        timeout: int | float | None = None,
        reraise: bool | None = None
    ) -> WebElement | Literal[False]:
        """
        Wait for the element to become clickable.

        Args:
            - timeout: Maximum wait time (in seconds) for the element to reach the expected state.
                Defaults to the element's timeout value if None.
            - reraise: Determines behavior when the element state is not as expected:
                - bool: True to raise a TimeoutException; False to return False.
                - None: Follows `Timeout.RERAISE`.

        Returns:
            - WebElement: The element reached the expected state within the timeout.
            - False: The element failed to reach the expected state if `reraise` is False.

        Exception:
            - TimeoutException: Raised if `reraise` is True and
                the element did not reach the expected state within the timeout.
        """
        try:
            try:
                self._if_force_relocate()
                self._clickable_cache = self._visible_cache = self.wait(timeout).until(
                    ecex.element_to_be_clickable(self._present_cache)
                )
                self._logger.debug(f'present_cache -> visible_cache -> clickable_cache : {self._clickable_cache}')
                return self._clickable_cache
            except ELEMENT_REFERENCE_EXCEPTION:
                element = self.wait(timeout, EXTENDED_IGNORED_EXCEPTIONS).until(
                    ecex.element_located_to_be_clickable(self.locator, self.index)
                )
                if self.cache:
                    self._clickable_cache = self._visible_cache = self._present_cache = element
                    self._logger.debug(
                        'locator -> present_cache -> visible_cache -> clickable_cache : '
                        f'{self._clickable_cache}'
                    )
                else:
                    self._logger.debug(f'locator -> clickable_element : {element}')
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
        Wait for the element to become unclickable.

        Args:
            - timeout: Maximum wait time (in seconds) for the element to reach the expected state.
                Defaults to the element's timeout value if None.
            - present: Specifies whether the element should be present:
                - True: The element must be present in the expected state.
                - False: The element can be present in the expected state or absent.
            - reraise: Defines behavior when the element state is not as expected:
                - bool: True to raise a TimeoutException; False to return False.
                - None: Follows `Timeout.RERAISE`, a boolean that defaults to True.

        Returns:
            - WebElement: The element reached the expected state within the timeout.
            - True: The element is absent within the timeout,
                and `present` is False, allowing absence.
            - False: The element failed to reach the expected state
                within the timeout if `reraise` is False.

        Exception:
            - TimeoutException: Raised if `reraise` is True and
                the element did not reach the expected state within the timeout.
        """
        try:
            try:
                self._if_force_relocate()
                element_or_true: WebElement | Literal[True] = self.wait(timeout).until(
                    ecex.element_to_be_unclickable(self._present_cache, present)
                )
                self._logger.debug(f'present_cache -> unclickable({present} : {element_or_true}')
                return element_or_true
            except ELEMENT_REFERENCE_EXCEPTION:
                element_or_true = self.wait(timeout, EXTENDED_IGNORED_EXCEPTIONS).until(
                    ecex.element_located_to_be_unclickable(self.locator, self.index, present)
                )
                if self.cache and isinstance(element_or_true, WebElement):
                    self._present_cache = element_or_true
                    self._logger.debug(
                        f'locator -> present_cache -> unclickable({present}) : '
                        f'{self._present_cache}'
                    )
                else:
                    self._logger.debug(f'locator -> unclickable({present} : {element_or_true}')
                return element_or_true
        except TimeoutException as exc:
            return self._timeout_process('unclickable', exc, reraise, present)

    def wait_selected(
        self,
        timeout: int | float | None = None,
        reraise: bool | None = None
    ) -> WebElement | Literal[False]:
        """
        Wait for the element to become selected.

        Args:
            - timeout: Maximum wait time (in seconds) for the element to reach the expected state.
                Defaults to the element's timeout value if None.
            - reraise: Determines behavior when the element state is not as expected:
                - bool: True to raise a TimeoutException; False to return False.
                - None: Follows `Timeout.RERAISE`.

        Returns:
            - WebElement: The element reached the expected state within the timeout.
            - False: The element failed to reach the expected state if `reraise` is False.

        Exception:
            - TimeoutException: Raised if `reraise` is True and
                the element did not reach the expected state within the timeout.
        """
        try:
            try:
                self._if_force_relocate()
                element = self.wait(timeout).until(
                    ecex.element_to_be_selected(self._present_cache)
                )
                self._logger.debug(f'present_cache -> selected : {element}')
                return element
            except ELEMENT_REFERENCE_EXCEPTION:
                element = self.wait(timeout, EXTENDED_IGNORED_EXCEPTIONS).until(
                    ecex.element_located_to_be_selected(self.locator, self.index)
                )
                if self.cache:
                    self._present_cache = element
                    self._logger.debug(f'locator -> present_cache -> selected : {self._present_cache}')
                else:
                    self._logger.debug(f'locator -> selected : {element}')
                return element
        except TimeoutException as exc:
            return self._timeout_process('selected', exc, reraise)

    def wait_unselected(
        self,
        timeout: int | float | None = None,
        reraise: bool | None = None
    ) -> WebElement | Literal[False]:
        """
        Waiting for the element to become unselected.

        Note:
            - The behavior of "unselected" differs from "invisible" and "unclickable."
            - The selection state is primarily influenced by user actions,
                so the element must be present.
            - As a result, absence is not considered an expected outcome.

        Args:
            - timeout: Maximum wait time (in seconds) for the element to reach the expected state.
                Defaults to the element's timeout value if None.
            - reraise: Determines behavior when the element state is not as expected:
                - bool: True to raise a TimeoutException; False to return False.
                - None: Follows `Timeout.RERAISE`.

        Returns:
            - WebElement: The element reached the expected state within the timeout.
            - False: The element failed to reach the expected state if `reraise` is False.

        Exception:
            - TimeoutException: Raised if `reraise` is True and
                the element did not reach the expected state within the timeout.
        """
        try:
            try:
                self._if_force_relocate()
                element = self.wait(timeout).until(
                    ecex.element_to_be_unselected(self._present_cache)
                )
                self._logger.debug(f'present_cache -> unselected : {element}')
                return element
            except ELEMENT_REFERENCE_EXCEPTION:
                element = self.wait(timeout, EXTENDED_IGNORED_EXCEPTIONS).until(
                    ecex.element_located_to_be_unselected(self.locator, self.index)
                )
                if self.cache:
                    self._present_cache = element
                    self._logger.debug(f'locator -> present_cache -> unselected : {self._present_cache}')
                else:
                    self._logger.debug(f'locator -> unselected : {element}')
                return element
        except TimeoutException as exc:
            return self._timeout_process('unselected', exc, reraise)

    @property
    def present(self) -> WebElement:
        """
        The same as `element.wait_present(reraise=True)`.
        """
        return cast(WebElement, self.wait_present(reraise=True))

    @property
    def visible(self) -> WebElement:
        """
        The same as element.wait_visible(reraise=True).
        """
        return cast(WebElement, self.wait_visible(reraise=True))

    @property
    def clickable(self) -> WebElement:
        """
        The same as element.wait_clickable(reraise=True).
        """
        return cast(WebElement, self.wait_clickable(reraise=True))

    @property
    def present_cache(self) -> WebElement | None:
        """
        Retrieve the stored WebElement if it is present.
        If the element has not been searched for, return None.
        """
        return getattr(self, _Name._present_cache, None)

    @property
    def visible_cache(self) -> WebElement | None:
        """
        Retrieve the stored WebElement if it is visible.
        If the element has not been searched for, return None.
        """
        return getattr(self, _Name._visible_cache, None)

    @property
    def clickable_cache(self) -> WebElement | None:
        """
        Retrieve the stored WebElement if it is clickable.
        If the element has not been searched for, return None.
        """
        return getattr(self, _Name._clickable_cache, None)

    def is_present(self, timeout: int | float | None = None) -> bool:
        """
        Whether the element is present.

        Args:
            - timeout: Maximum time in seconds to wait for the element to become present.

        Returns:
            - True: The element is present before timeout.
            - False: The element is still not present after timeout.
        """
        return True if self.wait_present(timeout, False) else False

    def is_visible(self) -> bool:
        """
        Whether the element is visible.
        It is the same as the official `is_displayed()` method.
        """
        try:
            self._if_force_relocate()
            result = self._present_cache.is_displayed()
        except ELEMENT_REFERENCE_EXCEPTION:
            result = self.present.is_displayed()
        if self.cache and result:
            self._visible_cache = self._present_cache
        return result

    def is_enabled(self) -> bool:
        """
        Whether the element is enabled.
        """
        try:
            self._if_force_relocate()
            return self._present_cache.is_enabled()
        except ELEMENT_REFERENCE_EXCEPTION:
            return self.present.is_enabled()

    def is_clickable(self) -> bool:
        """
        Whether the element is clickable.
        """
        try:
            self._if_force_relocate()
            result = self._present_cache.is_displayed() and self._present_cache.is_enabled()
        except ELEMENT_REFERENCE_EXCEPTION:
            element = self.present
            result = element.is_displayed() and element.is_enabled()
        if self.cache and result:
            self._clickable_cache = self._visible_cache = self._present_cache
        return result

    def is_selected(self) -> bool:
        """
        Whether the element is selected.
        """
        try:
            self._if_force_relocate()
            return self._present_cache.is_selected()
        except ELEMENT_REFERENCE_EXCEPTION:
            return self.present.is_selected()

    def screenshot(self, filename: str) -> bool:
        """
        Saves a screenshot of the current element to a PNG image file.
        Returns False if there is any IOError, else returns True.

        Args:
            - filename: The full path you wish to save your screenshot to.
                This should end with a `.png` extension.
        """
        try:
            self._if_force_relocate()
            return self._present_cache.screenshot(filename)
        except ELEMENT_REFERENCE_EXCEPTION:
            return self.present.screenshot(filename)

    @property
    def text(self) -> str:
        """
        The text of the element when it is present.
        """
        try:
            self._if_force_relocate()
            return self._present_cache.text
        except ELEMENT_REFERENCE_EXCEPTION:
            return self.present.text

    @property
    def visible_text(self) -> str:
        """
        The text of the element when it is visible.
        """
        try:
            self._if_force_relocate()
            return self._visible_cache.text
        except ELEMENT_REFERENCE_EXCEPTION:
            return self.visible.text

    @property
    def rect(self) -> dict:
        """
        A dictionary with the size and location of the element when it is present.

        Note that the official rect may have decimals,
        we remain consistent with the official standards.

        Return example: {'x': 10, 'y': 15, 'width': 100, 'height': 200}
        """
        try:
            self._if_force_relocate()
            rect = self._present_cache.rect
        except ELEMENT_REFERENCE_EXCEPTION:
            rect = self.present.rect
        # rearranged
        return {
            'x': rect['x'],
            'y': rect['y'],
            'width': rect['width'],
            'height': rect['height']
        }

    @property
    def location(self) -> dict[str, int]:
        """
        The location of the element when it is present in the renderable canvas.

        Note that the official location has been rounded,
        so the x, y may be different with rect.

        Return example: {'x': 200, 'y': 300}
        """
        try:
            self._if_force_relocate()
            return self._present_cache.location
        except ELEMENT_REFERENCE_EXCEPTION:
            return self.present.location

    @property
    def size(self) -> dict[str, int]:
        """
        The size of the element when it is present.

        Note that the official size may have decimals;
        We remain consistent with the official standards.

        Return example: {'width': 200, 'height': 100}
        """
        try:
            self._if_force_relocate()
            size = self._present_cache.size
        except ELEMENT_REFERENCE_EXCEPTION:
            size = self.present.size
        # rearranged
        return {
            'width': size['width'],
            'height': size['height']
        }

    @property
    def border(self) -> dict[str, int]:
        """
        The border of the element when it is present.

        Return is rounded down, for example:
        {'left': 150, 'right': 250, 'top': 200, 'bottom': 400}
        """
        try:
            self._if_force_relocate()
            rect = self._present_cache.rect
        except ELEMENT_REFERENCE_EXCEPTION:
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
        The center location of the element when it is present.

        Return is rounded down, for example:
        {'x': 80, 'y': 190}
        """
        try:
            self._if_force_relocate()
            rect = self._present_cache.rect
        except ELEMENT_REFERENCE_EXCEPTION:
            rect = self.present.rect
        return {
            'x': int(rect['x'] + rect['width'] / 2),
            'y': int(rect['y'] + rect['height'] / 2)
        }

    def click(self) -> None:
        """
        Click the element when it is clickable.
        """
        try:
            self._if_force_relocate()
            self._clickable_cache.click()
        except ELEMENT_REFERENCE_EXCEPTION:
            self.clickable.click()

    def delayed_click(self, sleep: int | float = 0.5) -> None:
        """
        Waits until the element is clickable, then delays for a specified time before clicking.

        Args:
            - sleep: Delay in seconds before clicking.
        """
        try:
            self._if_force_relocate()
            time.sleep(sleep)
            self._clickable_cache.click()
        except ELEMENT_REFERENCE_EXCEPTION:
            element = self.clickable
            time.sleep(sleep)
            element.click()

    @property
    def shadow_root(self) -> ShadowRoot:
        """
        Returns a shadow root of the element if there is one or an error.
        Only works from Chromium 96, Firefox 96, and Safari 16.4 onwards.

        Returns:
            - ShadowRoot object

        Exception:
            - NoSuchShadowRoot: If no shadow root was attached to element.
        """
        try:
            self._if_force_relocate()
            return self._present_cache.shadow_root
        except ELEMENT_REFERENCE_EXCEPTION:
            return self.present.shadow_root

    @property
    def location_once_scrolled_into_view(self) -> dict:
        """
        THIS PROPERTY MAY CHANGE WITHOUT WARNING.
        Use this to discover where on the screen an element is so that we can click it.
        This method should cause the element to be scrolled into view.
        Returns the top lefthand corner location on the screen,
        or zero coordinates if the element is not visible.
        """
        try:
            self._if_force_relocate()
            return self._present_cache.location_once_scrolled_into_view
        except ELEMENT_REFERENCE_EXCEPTION:
            return self.present.location_once_scrolled_into_view

    @property
    def aria_role(self) -> str:
        """
        Returns the ARIA role of the current web element.
        """
        try:
            self._if_force_relocate()
            return self._present_cache.aria_role
        except ELEMENT_REFERENCE_EXCEPTION:
            return self.present.aria_role

    @property
    def accessible_name(self) -> str:
        """
        Returns the ARIA Level of the current webelement.
        """
        try:
            self._if_force_relocate()
            return self._present_cache.accessible_name
        except ELEMENT_REFERENCE_EXCEPTION:
            return self.present.accessible_name

    def tap(self, duration: int | None = None) -> Self:
        """
        Appium API.
        Tap the center location of the element when it is present.
        This method can be used when `click()` fails.

        Args:
            - duration: Length of time to tap, in ms.
        """
        self.driver.tap([tuple(self.center.values())], duration)  # type: ignore[attr-defined]
        return self

    def app_drag_and_drop(
        self,
        target: Element,
        pause: float | None = None
    ) -> Self:
        """
        Appium API.
        Drag the origin element to the destination element.

        Args:
            target: The element to drag to.
            pause: How long the action pauses before moving after the tap and hold in seconds.
        """
        try:
            self._if_force_relocate()
            self.driver.drag_and_drop(self._present_cache, target._present_cache, pause)  # type: ignore[attr-defined]
        except ELEMENT_REFERENCE_EXCEPTION:
            self.driver.drag_and_drop(self.present, target.present, pause)  # type: ignore[attr-defined]
        return self

    def app_scroll(self, target: Element, duration: int | None = None) -> Self:
        """
        Appium API.
        Scrolls from one element to another

        Args:
            - target: The element to scroll to (center of element).
            - duration: Defines speed of scroll action when moving to target.
                Default is 600 ms for W3C spec.
        """
        try:
            self._if_force_relocate()
            self.driver.scroll(self._present_cache, target._present_cache, duration)  # type: ignore[attr-defined]
        except ELEMENT_REFERENCE_EXCEPTION:
            self.driver.scroll(self.present, target.present, duration)  # type: ignore[attr-defined]
        return self

    def is_viewable(self, timeout: int | float | None = None) -> bool:
        """
        Appium API.
        For native iOS and Android,
        access the element status whether it is in view border.

        Args:
            - timeout: Maximum time in seconds to wait for the element to become present.
        """
        element = self.wait_present(timeout, False)
        if element and element.is_displayed():
            if self.cache:
                self._visible_cache = element
            return True
        return False

    def swipe_by(
        self,
        offset: Coordinate = Offset.UP,
        area: Coordinate = Area.FULL,
        timeout: int | float = 3,
        max_round: int = 10,
        max_adjustment: int = 2,
        min_distance: int = 100,
        duration: int = 1000
    ) -> Self:
        """
        Appium API.
        For native iOS and Android apps, it swipes the screen until the element becomes visible
        within the specified area.

        Args:
            - offset: Please refer to the Usage.
            - area: Please refer to the Usage.
            - timeout: The maximum time in seconds to wait for the element to become visible.
            - max_round: The maximum number of swipes allowed.
            - max_adjustment: The maximum number of adjustments
                to align all borders of the element within the view border.
            - min_distance: The minimum swipe distance to avoid being mistaken for a click.
            - duration: The duration of the swipe and adjustment in milliseconds.

        Note on Args "min_distance" and "duration":
            - Both parameters are used to adjust the element position with a swipe
                when the element is visible but not within the desired area.
            - The default settings are based on sliding at a rate of 100 pixels per second,
                which has been found to be stable.
            - It is recommended not to change these parameter values
                unless you have specific testing scenarios.

        Usage::

            # Swipe parameters. Refer to the Class notes for details.
            from huskium import Offset, Area

            # Swipe down.
            my_page.target_element.swipe_by(Offset.DOWN)

            # Swipe to the right.
            my_page.target_element.swipe_by(Offset.RIGHT)

            # Swipe to the upper left.
            my_page.target_element.swipe_by(Offset.UPPER_LEFT)

            # Default is swiping up.
            # offset = Offset.UP = (0.5, 0.75, 0.5, 0.25)
            # area = Area.FULL = (0.0, 0.0, 1.0, 1.0)
            # offset x: Fixed 50% (0.5) of 100% (1.0) current window width.
            # offset y: From 75% (0.75) to 25% (0.25) of 100% (1.0) current window height.
            my_page.target_element.swipe_by()

            # This is the most recommended method to swipe within a swipeable range.
            # Get the absolute area coordinates using the scrollable element's rect.
            area = my_page.scrollable_element.rect
            my_page.target_element.swipe_by((0.3, 0.85, 0.5, 0.35), area)

            # Swipe with customize absolute offset.
            # Note that the area parameter will affect the adjusting process.
            # We recommend not setting the area in this case,
            # unless you have a specific testing scenario.
            # ex. Swiping range is not within the area,
            # and the target element should be inside the area after swiping.
            my_page.target_element.swipe_by((250, 300, 400, 700))

            # Swipe with customize relative offset of current window size.
            my_page.target_element.swipe_by((0.3, 0.85, 0.5, 0.35))

            # Swipe with customize relative offset of customize relative area.
            # The area is relative to current window rect, for example:
            # current window rect = (10, 20, 500, 1000)
            # area = (0.1, 0.2, 0.6, 0.7)
            # area_x = 10 + 500 x 0.1 = 60
            # area_y = 20 + 1000 x 0.2 = 220
            # area_width = 500 x 0.6 = 300
            # area_height = 1000 x 0.7 = 700
            my_page.target_element.swipe_by((0.3, 0.85, 0.5, 0.35), (0.1, 0.2, 0.6, 0.7))

            # Swipe with customize relative offset of customize absolute area.
            my_page.target_element.swipe_by((0.3, 0.85, 0.5, 0.35), (100, 150, 300, 700))

        """
        area = self._page._get_area(area)
        offset = self._page._get_offset(offset, area)
        self._start_swiping_by(offset, duration, timeout, max_round)
        self._start_adjusting_by(offset, area, max_adjustment, min_distance, duration)
        return self

    def flick_by(
        self,
        offset: Coordinate = Offset.UP,
        area: Coordinate = Area.FULL,
        timeout: int | float = 3,
        max_round: int = 10,
        max_adjustment: int = 2,
        min_distance: int = 100,
        duration: int = 1000
    ) -> Self:
        """
        Appium API.
        For native iOS and Android apps, it flicks the screen until the element becomes visible
        within the specified area.

        Args:
            - offset: Please refer to the Usage.
            - area: Please refer to the Usage.
            - timeout: The maximum time in seconds to wait for the element to become visible.
            - max_round: The maximum number of flicks allowed.
            - max_adjustment: The maximum number of adjustments
                to align all borders of the element within the view border.
            - min_distance: The minimum flick distance to avoid being mistaken for a click.
            - duration: The duration of the adjustment (not flick) in milliseconds.

        Note on Args "min_distance" and "duration":
            - Both parameters are used to adjust the element position with a flick
                when the element is visible but not within the desired area.
            - The default settings are based on sliding at a rate of 100 pixels per second,
                which has been found to be stable.
            - It is recommended not to change these parameter values
                unless you have specific testing scenarios.

        Usage::

            # Flick parameters. Refer to the Class notes for details.
            from huskium import Offset, Area

            # Flick down.
            my_page.target_element.flick_by(Offset.DOWN)

            # Flick to the right.
            my_page.target_element.flick_by(Offset.RIGHT)

            # Flick to the upper left.
            my_page.target_element.flick_by(Offset.UPPER_LEFT)

            # Default is flicking up.
            # offset = Offset.UP = (0.5, 0.75, 0.5, 0.25)
            # area = Area.FULL = (0.0, 0.0, 1.0, 1.0)
            # offset x: Fixed 50% (0.5) of 100% (1.0) current window width.
            # offset y: From 75% (0.75) to 25% (0.25) of 100% (1.0) current window height.
            my_page.target_element.flick_by()

            # This is the most recommended method to flick within a swipeable range.
            # Get the absolute area coordinates using the scrollable element's rect.
            area = my_page.scrollable_element.rect
            my_page.target_element.flick_by((0.3, 0.85, 0.5, 0.35), area)

            # Flick with customize absolute offset.
            # Note that the area parameter will affect the adjusting process.
            # We recommend not setting the area in this case,
            # unless you have a specific testing scenario.
            # ex. Swiping range is not within the area,
            # and the target element should be inside the area after flicking.
            my_page.target_element.flick_by((250, 300, 400, 700))

            # Flick with customize relative offset of current window size.
            my_page.target_element.flick_by((0.3, 0.85, 0.5, 0.35))

            # Flick with customize relative offset of customize relative area.
            # The area is relative to current window rect, for example:
            # current window rect = (10, 20, 500, 1000)
            # area = (0.1, 0.2, 0.6, 0.7)
            # area x = 10 + 500 x 0.1 = 60
            # area y = 20 + 1000 x 0.2 = 220
            # area width = 500 x 0.6 = 300
            # area height = 1000 x 0.7 = 700
            my_page.target_element.flick_by((0.3, 0.85, 0.5, 0.35), (0.1, 0.2, 0.6, 0.7))

            # Flick with customize relative offset of customize absolute area.
            my_page.target_element.flick_by((0.3, 0.85, 0.5, 0.35), (100, 150, 300, 700))

        """
        area = self._page._get_area(area)
        offset = self._page._get_offset(offset, area)
        self._start_flicking_by(offset, timeout, max_round)
        self._start_adjusting_by(offset, area, max_adjustment, min_distance, duration)
        return self

    def _start_swiping_by(
        self,
        offset: tuple[int, int, int, int],
        duration: int,
        timeout: int | float,
        max_round: int
    ) -> int | None:
        if not max_round:
            self._logger.warning(f'For max_round is {max_round}, no swiping performed.')
            return None
        self._logger.debug(f'Start swiping.')
        round = 0
        while not self.is_viewable(timeout):
            if round == max_round:
                self._logger.warning(f'Stop swiping. Element remains not viewable after max {max_round} rounds.\n')
                return round
            self.driver.swipe(*offset, duration)  # type: ignore[attr-defined]
            round += 1
            self._logger.debug(f'Swiping round {round} done.\n')
        self._logger.debug(f'Stop swiping. Element is viewable after {round} rounds.\n')
        return round

    def _start_flicking_by(
        self,
        offset: tuple[int, int, int, int],
        timeout: int | float,
        max_round: int
    ) -> int | None:
        if not max_round:
            self._logger.warning(f'For max_round is {max_round}, no flicking performed.')
            return None
        self._logger.debug(f'Start flicking.')
        round = 0
        while not self.is_viewable(timeout):
            if round == max_round:
                self._logger.warning(
                    f'Stop flicking. Element remains not viewable after max {max_round} rounds.\n')
                return round
            self.driver.flick(*offset)  # type: ignore[attr-defined]
            round += 1
            self._logger.debug(f'Flicking round {round} done.\n')
        self._logger.debug(f'Stop flicking. Element is viewable after {round} rounds.\n')
        return round

    def _start_adjusting_by(
        self,
        offset: tuple[int, int, int, int],
        area: tuple[int, int, int, int],
        max_adjustment: int,
        min_distance: int,
        duration: int
    ) -> int | None:
        if not max_adjustment:
            self._logger.debug(f'For max_adjustment is {max_adjustment}, no adjustment performed.')
            return None
        self._logger.debug('Start adjusting.')
        round = 0
        while (adjusted_offset := self._get_adjusted_offset(offset, area, min_distance)):
            if round == max_adjustment:
                self._logger.debug(f'Stop adjusting after max {max_adjustment} rounds.\n')
                return round
            self.driver.swipe(*adjusted_offset, duration)  # type: ignore[attr-defined]
            round += 1
            self._logger.debug(f'Adjusting round {round} done.\n')
        self._logger.debug(f'Stop adjusting after {round} round.\n')
        return round

    def _get_adjusted_offset(
        self,
        offset: tuple[int, int, int, int],
        area: tuple[int, int, int, int],
        min_distance: int,
    ) -> tuple[int, int, int, int] | None:

        def dist(delta) -> int:
            return int(max(abs(delta), min_distance) * (1 if delta >= 0 else -1))

        # original offset
        start_x, start_y, end_x, end_y = offset
        self._logger.debug(f'OriginalOffset(sx, sy, ex, ey: {offset}')

        # area border
        area_left, area_top, area_width, area_height = area
        area_right = area_left + area_width
        area_bottom = area_top + area_height
        self._logger.debug(f'Area(l, r, t, b: {(area_left, area_right, area_top, area_bottom)}')

        # element border
        element_left, element_right, element_top, element_bottom = self.border.values()
        self._logger.debug(f'Element(l, r, t, b: {(element_left, element_right, element_top, element_bottom)}')

        # delta = (area - element)
        delta_left = area_left - element_left
        delta_right = area_right - element_right
        delta_top = area_top - element_top
        delta_bottom = area_bottom - element_bottom
        self._logger.debug(f'Delta(A-E(l, r, t, b): {(delta_left, delta_right, delta_top, delta_bottom)}')

        # adjust action, note that this must use delta to judge
        adjust_action = ((delta_left > 0), (delta_right < 0), (delta_top > 0), (delta_bottom < 0))
        self._logger.debug(f'AdjustAction(l>0, r<0, t>0, b<0: {adjust_action}')

        # compare delta with min_distance
        dist_left = dist(delta_left)
        dist_right = dist(delta_right)
        dist_top = dist(delta_top)
        dist_bottom = dist(delta_bottom)
        self._logger.debug(
            f'AdjustDistance(min={min_distance})(l, r, t, b): '
            f'{(dist_left, dist_right, dist_top, dist_bottom)}'
        )
        adjust_actions = {
            (True, False, True, False): (dist_left, dist_top),
            (False, False, True, False): (0, dist_top),
            (False, True, True, False): (dist_right, dist_top),
            (True, False, False, False): (dist_left, 0),
            (False, True, False, False): (dist_right, 0),
            (True, False, False, True): (dist_left, dist_bottom),
            (False, False, False, True): (0, dist_bottom),
            (False, True, False, True): (dist_right, dist_bottom),
        }
        delta_x, delta_y = adjust_actions.get(adjust_action, (0, 0))
        self._logger.debug(f'(delta_x, delta_y: {(delta_x, delta_y)}')

        # return
        if delta_x == 0 and delta_y == 0:
            self._logger.debug('No further adjustment needed.')
            return None
        end_x, end_y = (start_x + delta_x), (start_y + delta_y)
        adjusted_offset = (start_x, start_y, end_x, end_y)
        self._logger.debug(f'OriginalOffset(sx, sy, ex, ey: {offset}')
        self._logger.debug(f'AdjustedOffset(sx, sy, ex, ey: {adjusted_offset}')
        return adjusted_offset

    def clear(self) -> Self:
        """
        Clear the text of the field type element.

        Usage::

            my_page.my_element.clear()
            my_page.my_element.clear().send_keys('my_text')
            my_page.my_element.click().clear().send_keys('my_text')

        """
        try:
            self._if_force_relocate()
            self._clickable_cache.clear()
        except ELEMENT_REFERENCE_EXCEPTION:
            self.clickable.clear()
        return self

    def send_keys(self, *value) -> Self:
        """
        Simulates typing into the element.

        Args:
            - value: The texts or keys to typing.

        Usage::

            my_page.my_element.send_keys('my_text')
            my_page.my_element.clear().send_keys('my_text')
            my_page.my_element.click().clear().send_keys('my_text')

        """
        try:
            self._if_force_relocate()
            self._clickable_cache.send_keys(*value)
        except ELEMENT_REFERENCE_EXCEPTION:
            self.clickable.send_keys(*value)
        return self

    def get_dom_attribute(self, name: str) -> str:
        """
        Gets the given attribute of the element. Unlike
        `selenium.webdriver.remote.BaseWebElement.get_attribute`,
        this method only returns attributes declared in the element's HTML markup.

        Args:
            - name: Name of the attribute to retrieve.

        Usage::

            text_length = element.get_dom_attribute("class")

        """
        try:
            self._if_force_relocate()
            return self._present_cache.get_dom_attribute(name)
        except ELEMENT_REFERENCE_EXCEPTION:
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

        To obtain the exact value of the attribute or property,
        use `selenium.webdriver.remote.BaseWebElement.get_dom_attribute` or
        `selenium.webdriver.remote.BaseWebElement.get_property` methods respectively.

        Args:
            - name: Name of the attribute or property to retrieve.

        Usage::

            # Check if the "active" CSS class is applied to an element.
            is_active = "active" in target_element.get_attribute("class")

        """
        try:
            self._if_force_relocate()
            return self._present_cache.get_attribute(name)
        except ELEMENT_REFERENCE_EXCEPTION:
            return self.present.get_attribute(name)

    def get_property(self, name: Any) -> str | bool | WebElement | dict:
        """
        Gets the given property of the element.

        Args:
            - name: Name of the property to retrieve.

        Usage::

            text_length = target_element.get_property("text_length")

        """
        try:
            self._if_force_relocate()
            return self._present_cache.get_property(name)
        except ELEMENT_REFERENCE_EXCEPTION:
            return self.present.get_property(name)

    def submit(self) -> None:
        """
        Selenium API.
        Submits a form.
        """
        try:
            self._if_force_relocate()
            self._clickable_cache.submit()
        except ELEMENT_REFERENCE_EXCEPTION:
            self.clickable.submit()

    @property
    def tag_name(self) -> str:
        """
        Selenium API.
        This element's tagName property.
        """
        try:
            self._if_force_relocate()
            return self._present_cache.tag_name
        except ELEMENT_REFERENCE_EXCEPTION:
            return self.present.tag_name

    def value_of_css_property(self, property_name: Any) -> str:
        """
        Selenium API.
        The value of a CSS property.
        """
        try:
            self._if_force_relocate()
            return self._present_cache.value_of_css_property(property_name)
        except ELEMENT_REFERENCE_EXCEPTION:
            return self.present.value_of_css_property(property_name)

    def visible_value_of_css_property(self, property_name: Any) -> str:
        """
        Selenium API.
        The visible value of a CSS property.
        """
        try:
            self._if_force_relocate()
            return self._visible_cache.value_of_css_property(property_name)
        except ELEMENT_REFERENCE_EXCEPTION:
            return self.visible.value_of_css_property(property_name)

    def switch_to_frame(
        self,
        timeout: int | float | None = None,
        reraise: bool | None = None
    ) -> bool:
        """
        Selenium API.
        If the frame is available it switches the given driver to the specified frame.
        """
        try:
            return self.wait(timeout).until(
                ec.frame_to_be_available_and_switch_to_it(self.locator),
            )
        except TimeoutException as exc:
            return self._timeout_process('available frame', exc, reraise)

    def perform(self) -> None:
        """
        Selenium ActionChains API.
        Performs all stored actions.
        once called, it will execute all stored actions in page.

        Usage::

            # Basic usage. Execute element actions.
            my_page.my_element.scroll_to_element().action_click().perform()

            # Multiple actions to call, set perform to the last action.
            # This will execute all actions in my_page not just my_page.my_element2.
            my_page.my_element1.scroll_to_element().action_click()
            my_page.my_element2.drag_and_drop(my_page.element3).perform()

            # As above, it is the same to call perform by page, which is more clear:
            my_page.my_element1.scroll_to_element().action_click()
            my_page.my_element2.drag_and_drop(my_page.element3)
            my_page.perform()

        """
        self.action.perform()

    def reset_actions(self) -> None:
        """
        Selenium ActionChains API.
        Clears actions that are already stored in object of Page.
        once called, it will reset all stored actions in page.

        Usage::

            # Reset the stored actions by the last reset_actions.
            my_page.my_element1.scroll_to_element().action_click()
            my_page.my_element2.click_and_hold().reset_actions()

            # There is a better one structure,
            # reset all action calls made by my_page.
            my_page.my_element1.scroll_to_element().action_click()
            my_page.my_element2.click_and_hold()
            my_page.reset_actions()

        """
        self.action.reset_actions()

    def action_click(self) -> Self:
        """
        Selenium ActionChains API.
        Clicks an element.

        Usage::

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
            self._if_force_relocate()
            self.action.click(self._present_cache)
        except ELEMENT_REFERENCE_EXCEPTION:
            self.action.click(self.present)
        return self

    def click_and_hold(self) -> Self:
        """
        Selenium ActionChains API.
        Holds down the left mouse button on an element.

        Usage::

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
            self._if_force_relocate()
            self.action.click_and_hold(self._present_cache)
        except ELEMENT_REFERENCE_EXCEPTION:
            self.action.click_and_hold(self.present)
        return self

    def context_click(self) -> Self:
        """
        Selenium ActionChains API.
        Performs a context-click (right click) on an element.

        Usage::

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
            self._if_force_relocate()
            self.action.context_click(self._present_cache)
        except ELEMENT_REFERENCE_EXCEPTION:
            self.action.context_click(self.present)
        return self

    def double_click(self) -> Self:
        """
        Selenium ActionChains API.
        Double-clicks an element.

        Usage::

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
            self._if_force_relocate()
            self.action.double_click(self._present_cache)
        except ELEMENT_REFERENCE_EXCEPTION:
            self.action.double_click(self.present)
        return self

    def drag_and_drop(self, target: Element) -> Self:
        """
        Selenium ActionChains API.
        Holds down the left mouse button on the source element,
        then moves to the target element and releases the mouse button.

        Args:
        - target: The element to mouse up. Allowing Element or WebElement type.

        Usage::

            # Basic usage
            my_page.my_element1.drag_and_drop(my_page.my_element2).perform()

            # Chain with another method
            my_page.my_element1.scroll_to_element().drag_and_drop(my_page.my_element2).perform()

            # or
            my_page.my_element1.scroll_to_element().drag_and_drop(my_page.my_element2)
            ...  # other process
            my_page.perform()

        """
        try:
            self._if_force_relocate()
            self.action.drag_and_drop(self._present_cache, target._present_cache)
        except ELEMENT_REFERENCE_EXCEPTION:
            self.action.drag_and_drop(self.present, target.present)
        return self

    def drag_and_drop_by_offset(self, xoffset: int, yoffset: int) -> Self:
        """
        Selenium ActionChains API.
        Holds down the left mouse button on the source element,
        then moves to the target offset and releases the mouse button.

        Args:
            - xoffset: X offset to move to, as a positive or negative integer.
            - yoffset: Y offset to move to, as a positive or negative integer.

        Usage::

            # Basic usage
            my_page.my_element.drag_and_drop_by_offset(100, 200).perform()

            # Chain with another method
            my_page.my_element.scroll_to_element().drag_and_drop_by_offset(100, 200).perform()

            # or
            my_page.my_element.scroll_to_element().drag_and_drop_by_offset(100, 200)
            ...  # other process
            my_page.perform()

        """
        try:
            self._if_force_relocate()
            self.action.drag_and_drop_by_offset(self._present_cache, xoffset, yoffset)
        except ELEMENT_REFERENCE_EXCEPTION:
            self.action.drag_and_drop_by_offset(self.present, xoffset, yoffset)
        return self

    def hotkey(self, *value: str) -> Self:
        """
        Selenium ActionChains API.
        Sends hotkey to target element.

        Args:
            - value: The combination of hotkey.

        Usage::

            # copy(control+c)
            my_page.my_element.hotkey(Keys.CONTROL, 'c').perform()

            # switch to previous application(command+shift+tab)
            my_page.my_element.hotkey(Keys.COMMAND, Keys.SHIFT, Keys.TAB).perform()

        """
        # key_down, first to focus target element.
        try:
            self._if_force_relocate()
            self.action.key_down(value[0], self._present_cache)
        except ELEMENT_REFERENCE_EXCEPTION:
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
        Selenium ActionChains API.
        Sends a key press only, without releasing it.
        Should only be used with modifier keys (Control, Alt and Shift).
        If you want to perform a hotkey process,
        it is recommended to use hotkey() instead.

        Args:
            - value: The modifier key to send. Values are defined in Keys class.
            - focus: Whether to focus element or not. Default to focus current element.

        Usage::

            # copy(control+c)
            my_page.my_element.key_down(Key.CONTROL).action_send_keys('c').key_up(Key.CONTROL)

        """
        if focus:
            try:
                self._if_force_relocate()
                self.action.key_down(value, self._present_cache)
            except ELEMENT_REFERENCE_EXCEPTION:
                self.action.key_down(value, self.present)
        else:
            self.action.key_down(value)
        return self

    def key_up(self, value: str, focus: bool = False) -> Self:
        """
        Selenium ActionChains API.
        Releases a modifier key.
        Should only be used with modifier keys (Control, Alt and Shift).
        If you want to perform a hotkey process,
        it is recommended to use hotkey() instead.

        Args:
            - value: The modifier key to send. Values are defined in Keys class.
            - focus: Whether to focus on the element or not.
                The default is NOT to focus on the current element
                as this is generally not the first action.

        Usage::

            # copy(control+c)
            my_page.my_element.key_down(Key.CONTROL).action_send_keys('c').key_up(Key.CONTROL)

        """
        if focus:
            try:
                self._if_force_relocate()
                self.action.key_up(value, self._present_cache)
            except ELEMENT_REFERENCE_EXCEPTION:
                self.action.key_up(value, self.present)
        else:
            self.action.key_up(value)
        return self

    def action_send_keys(self, *keys_to_send: str) -> Self:
        """
        Selenium ActionChains API.
        Sends keys to current focused element.
        Note that it should have focused element first.

        Args:
            - keys_to_send: The keys to send.
                Modifier keys constants can be found in the 'Keys' class.

        Usage::

            # Combine with key_down and key_up method
            my_page.my_element.key_down(Keys.COMMAND).action_send_keys('a').key_up(Keys.COMMAND).perform()

            # Send keys to focused element
            # This is recommend to use send_keys_to_element() instead.
            my_page.my_element.action_click()  # Need to have focused element first.
            my_page.my_element.action_send_keys('my_keys').perform()

        """
        self.action.send_keys(*keys_to_send)
        return self

    def send_keys_to_element(self, *keys_to_send: str) -> Self:
        """
        Selenium ActionChains API.
        Sends keys to an element.

        Args:
            - keys_to_send: The keys to send.
                Modifier keys constants can be found in the 'Keys' class.

        Usage::

            # Basic usage
            my_page.my_element.send_keys_to_element(Keys.ENTER)

            # Chain with another method
            my_page.my_element.scroll_to_element(False).send_keys_to_element(Keys.ENTER)

            # or
            my_page.my_element.scroll_to_element(False).send_keys_to_element(Keys.ENTER)
            ...  # other process
            my_page.perform()

        """
        try:
            self._if_force_relocate()
            self.action.send_keys_to_element(self._present_cache, *keys_to_send)
        except ELEMENT_REFERENCE_EXCEPTION:
            self.action.send_keys_to_element(self.present, *keys_to_send)
        return self

    def move_to_element(self) -> Self:
        """
        Selenium ActionChains API.
        Moving the mouse to the middle of an element.

        Usage::

            # Basic usage
            my_page.my_element.move_to_element().perform()

            # Chain with another method
            my_page.my_element.scroll_to_element().move_to_element().perform()

            # or
            my_page.my_element.scroll_to_element().move_to_element()
            ...  # other process
            my_page.perform()

        """
        try:
            self._if_force_relocate()
            self.action.move_to_element(self._present_cache)
        except ELEMENT_REFERENCE_EXCEPTION:
            self.action.move_to_element(self.present)
        return self

    def move_to_element_with_offset(
        self,
        xoffset: int,
        yoffset: int,
    ) -> Self:
        """
        Selenium ActionChains API.
        Move the mouse by an offset of the specified element.
        Offsets are relative to the in-view center point of the element.

        Args:
            - xoffset: X offset to move to, as a positive or negative integer.
            - yoffset: Y offset to move to, as a positive or negative integer.

        Usage::

            # Basic usage
            my_page.my_element.move_to_element_with_offset(100, 200).perform()

            # Chain with another method
            my_page.my_element.scroll_to_element().move_to_element_with_offset(100, 200).perform()

            # or
            my_page.my_element.scroll_to_element().move_to_element_with_offset(100, 200)
            ...  # other process
            my_page.perform()

        """
        try:
            self._if_force_relocate()
            self.action.move_to_element_with_offset(self._present_cache, xoffset, yoffset)
        except ELEMENT_REFERENCE_EXCEPTION:
            self.action.move_to_element_with_offset(self.present, xoffset, yoffset)
        return self

    def release(self) -> Self:
        """
        Selenium ActionChains API.
        Releasing a held mouse button on an element.

        Usage::

            # Basic usage
            my_page.my_element.release().perform()

            # Chain with another method
            my_page.my_element.click_and_hold().release().perform()

            # or
            my_page.my_element.click_and_hold().release()
            ...  # other process
            my_page.perform()

        """
        try:
            self._if_force_relocate()
            self.action.release(self._present_cache)
        except ELEMENT_REFERENCE_EXCEPTION:
            self.action.release(self.present)
        return self

    def pause(self, seconds: int | float) -> Self:
        """
        Selenium ActionChains API.
        Pause all inputs for the specified duration in seconds.
        """
        self.action.pause(seconds)
        return self

    def scroll_to_element(self) -> Self:
        """
        Selenium ActionChains API.
        If the element is outside the viewport,
        scrolls the bottom of the element to the bottom of the viewport.

        Usage::

            # Basic usage
            my_page.my_element.scroll_to_element().perform()

            # Chain with another method
            my_page.my_element.scroll_to_element().action_click().perform()

            # or
            my_page.my_element1.scroll_to_element().action_click()
            ...  # other process
            my_page.perform()

        """
        try:
            self._if_force_relocate()
            self.action.scroll_to_element(self._present_cache)
        except ELEMENT_REFERENCE_EXCEPTION:
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
        Selenium ActionChains API.
        Set the origin to the center of the element with an offset,
        and perform the swipe with the specified delta.
        If the element is not in the viewport,
        the bottom of the element will first be scrolled to the bottom of the viewport.

        Args:
            - x_offset: From origin element center, a negative value offset left.
            - y_offset: From origin element center, a negative value offset up.
            - delta_x: Distance along X axis to scroll using the wheel,
                a negative value scrolls left.
            - delta_y: Distance along Y axis to scroll using the wheel,
                a negative value scrolls up.
            - perform: Default is True to perform the stored action immediately;
                otherwise, store the action to be performed later.

        Usage::

            # Basic usage
            my_page.my_element.scroll_from_element(100, 200, -50, -100).perform()

            # Chain with another method
            my_page.my_element.scroll_from_element(-30, -50, 150, 100).action_click().perform()

            # or
            my_page.my_element.scroll_from_element(-30, -50, 150, 100).action_click()
            ...  # other process
            my_page.perform()

        """
        try:
            self._if_force_relocate()
            scroll_origin = ScrollOrigin.from_element(self._present_cache, x_offset, y_offset)
            self.action.scroll_from_origin(scroll_origin, delta_x, delta_y)
        except ELEMENT_REFERENCE_EXCEPTION:
            scroll_origin = ScrollOrigin.from_element(self.present, x_offset, y_offset)
            self.action.scroll_from_origin(scroll_origin, delta_x, delta_y)
        return self

    @property
    def select(self) -> Select:
        """
        Get the Select object by present element.
        """
        try:
            self._if_force_relocate()
            self._select_cache = Select(self._present_cache)
        except ELEMENT_REFERENCE_EXCEPTION:
            self._select_cache = Select(self.present)
        return self._select_cache

    @property
    def select_cache(self) -> Select | None:
        """
        Get the Select cache.
        """
        return getattr(self, _Name._select_cache, None)

    @property
    def options(self) -> list[SeleniumWebElement]:
        """
        Selenium Select API.
        Returns a list of all options belonging to this select tag.
        """
        # All Select-related methods must be encapsulated using this structure
        # to ensure no unnecessary steps are taken.
        # The reason is that if "self._select_cache.method()" raises a
        # StaleElementReferenceException or InvalidSessionIdException,
        # we can directly rebuild with "self._select_cache = Select(self.present)",
        # without needing to check "self._select_cache = Select(self._present_cache)" again.
        try:
            try:
                # The main process.
                self._if_force_relocate()
                return self._select_cache.options
            except AttributeError:
                # Handle the first AttributeError:
                # If there is no available select attribute,
                # create it using the "_present_cache" first.
                self._select_cache = Select(self._present_cache)
        except ELEMENT_REFERENCE_EXCEPTION:
            # Handle ElementReferenceException by creating a new select object.
            # This exception can be triggered in two scenarios:
            # 1. The main process triggers a stale exception.
            # 2. During the first AttributeError handling,
            #    if there is no "_present_cache" attribute,
            #    or it triggers a stale or invalid session exception when initializing.
            self._select_cache = Select(self.present)
        return self._select_cache.options

    @property
    def all_selected_options(self) -> list[SeleniumWebElement]:
        """
        Selenium Select API.
        Returns a list of all selected options belonging to this select tag.
        """
        try:
            try:
                self._if_force_relocate()
                return self._select_cache.all_selected_options
            except AttributeError:
                self._select_cache = Select(self._present_cache)
        except ELEMENT_REFERENCE_EXCEPTION:
            self._select_cache = Select(self.present)
        return self._select_cache.all_selected_options

    @property
    def first_selected_option(self) -> SeleniumWebElement:
        """
        Selenium Select API.
        The first selected option in this select tag,
        or the currently selected option in a normal select.
        """
        try:
            try:
                self._if_force_relocate()
                return self._select_cache.first_selected_option
            except AttributeError:
                self._select_cache = Select(self._present_cache)
        except ELEMENT_REFERENCE_EXCEPTION:
            self._select_cache = Select(self.present)
        return self._select_cache.first_selected_option

    def select_by_value(self, value: str) -> None:
        """
        Selenium Select API.
        Select all options that have a value matching the argument.

        That is, when given "foo" this would select an option like:
        <option value="foo">Bar</option>

        Args:
            - value: The value to match against.
        """
        try:
            try:
                self._if_force_relocate()
                return self._select_cache.select_by_value(value)
            except AttributeError:
                self._select_cache = Select(self._present_cache)
        except ELEMENT_REFERENCE_EXCEPTION:
            self._select_cache = Select(self.present)
        return self._select_cache.select_by_value(value)

    def select_by_index(self, index: int) -> None:
        """
        Selenium Select API.
        Select the option at the given index.

        This is done by examining the "index" attribute of an element, and not merely by counting.

        Args:
            - index: The option at this index will be selected,
                throws NoSuchElementException if there is no option with specified index in SELECT.
        """
        try:
            try:
                self._if_force_relocate()
                return self._select_cache.select_by_index(index)
            except AttributeError:
                self._select_cache = Select(self._present_cache)
        except ELEMENT_REFERENCE_EXCEPTION:
            self._select_cache = Select(self.present)
        return self._select_cache.select_by_index(index)

    def select_by_visible_text(self, text: str) -> None:
        """
        Selenium Select API.
        Select all options that display text matching the argument.

        That is, when given "Bar" this would select an option like:
        <option value="foo">Bar</option>

        Args:
            - text: The visible text to match against,
                throws NoSuchElementException if there is no option with specified text in SELECT.
        """
        try:
            try:
                self._if_force_relocate()
                return self._select_cache.select_by_visible_text(text)
            except AttributeError:
                self._select_cache = Select(self._present_cache)
        except ELEMENT_REFERENCE_EXCEPTION:
            self._select_cache = Select(self.present)
        return self._select_cache.select_by_visible_text(text)

    def deselect_all(self) -> None:
        """
        Selenium Select API.
        Clear all selected entries.
        This is only valid when the SELECT supports multiple selections.
        """
        try:
            try:
                self._if_force_relocate()
                return self._select_cache.deselect_all()
            except AttributeError:
                self._select_cache = Select(self._present_cache)
        except ELEMENT_REFERENCE_EXCEPTION:
            self._select_cache = Select(self.present)
        return self._select_cache.deselect_all()

    def deselect_by_value(self, value: str) -> None:
        """
        Selenium Select API.
        Deselect all options that have a value matching the argument.
        That is, when given "foo" this would deselect an option like:
        <option value="foo">Bar</option>

        Args:
            - value: The value to match against.
        """
        try:
            try:
                self._if_force_relocate()
                return self._select_cache.deselect_by_value(value)
            except AttributeError:
                self._select_cache = Select(self._present_cache)
        except ELEMENT_REFERENCE_EXCEPTION:
            self._select_cache = Select(self.present)
        return self._select_cache.deselect_by_value(value)

    def deselect_by_index(self, index: int) -> None:
        """
        Selenium Select API.
        Deselect the option at the given index.
        This is done by examining the "index" attribute of an element,
        and not merely by counting.

        Args:
            - index: The option at this index will be deselected.
        """
        try:
            try:
                self._if_force_relocate()
                return self._select_cache.deselect_by_index(index)
            except AttributeError:
                self._select_cache = Select(self._present_cache)
        except ELEMENT_REFERENCE_EXCEPTION:
            self._select_cache = Select(self.present)
        return self._select_cache.deselect_by_index(index)

    def deselect_by_visible_text(self, text: str) -> None:
        """
        Selenium Select API.
        Deselect all options that display text matching the argument.
        That is, when given "Bar" this would deselect an option like:
        <option value="foo">Bar</option>

        Args:
            - text: The visible text to match against.
        """
        try:
            try:
                self._if_force_relocate()
                return self._select_cache.deselect_by_visible_text(text)
            except AttributeError:
                self._select_cache = Select(self._present_cache)
        except ELEMENT_REFERENCE_EXCEPTION:
            self._select_cache = Select(self.present)
        return self._select_cache.deselect_by_visible_text(text)

    @property
    def location_in_view(self) -> dict[str, int]:
        """
        Appium API.
        Retrieve the location (coordination) of the element
        relative to the view when it is present.

        Return example: {'x': 100, 'y': 250}
        """
        try:
            self._if_force_relocate()
            return self._present_cache.location_in_view  # type: ignore[attr-defined]
        except ELEMENT_REFERENCE_EXCEPTION:
            return self.present.location_in_view  # type: ignore[attr-defined]

    def input(self, text: str = '', times: int = 1) -> Self:
        """
        Selenium API
        Input text to the element.

        Args:
            - text: The text to input.

        Usage::

            my_page.my_element.input('123 456')
            my_page.my_element.input('123').space().input('456')
            my_page.my_element.input('6789', 4)

        """
        try:
            self._if_force_relocate()
            self._present_cache.send_keys(text * times)
        except ELEMENT_REFERENCE_EXCEPTION:
            self.present.send_keys(text * times)
        return self

    def enter(self) -> Self:
        """
        Selenium API
        Send keys ENTER to the element.

        Usage::

            my_page.my_element.input('123 456').enter()

        """
        try:
            self._if_force_relocate()
            self._present_cache.send_keys(Keys.ENTER)
        except ELEMENT_REFERENCE_EXCEPTION:
            self.present.send_keys(Keys.ENTER)
        return self

    def select_all(self) -> Self:
        """
        Selenium API, this is NOT Select relative function.
        Send keys "COMMAND/CONTROL + A" to the element.

        Usage::

            my_page.my_element.select_all().copy()

        """
        first = Keys.COMMAND if platform.system().lower() == "darwin" else Keys.CONTROL
        try:
            self._if_force_relocate()
            self._present_cache.send_keys(first, 'a')
        except ELEMENT_REFERENCE_EXCEPTION:
            self.present.send_keys(first, 'a')
        return self

    def cut(self) -> Self:
        """
        Selenium API
        Send keys "COMMAND/CONTROL + X" to the element.

        Usage::

            my_page.my_element1.cut()
            my_page.my_element2.paste()

        """
        first = Keys.COMMAND if platform.system().lower() == "darwin" else Keys.CONTROL
        try:
            self._if_force_relocate()
            self._present_cache.send_keys(first, 'x')
        except ELEMENT_REFERENCE_EXCEPTION:
            self.present.send_keys(first, 'x')
        return self

    def copy(self) -> Self:
        """
        Selenium API
        Send keys "COMMAND/CONTROL + C" to the element.

        Usage::

            my_page.my_element1.copy()
            my_page.my_element2.paste()

        """
        first = Keys.COMMAND if platform.system().lower() == "darwin" else Keys.CONTROL
        try:
            self._if_force_relocate()
            self._present_cache.send_keys(first, 'c')
        except ELEMENT_REFERENCE_EXCEPTION:
            self.present.send_keys(first, 'c')
        return self

    def paste(self) -> Self:
        """
        Selenium API
        Send keys "COMMAND/CONTROL + V" to the element.

        Usage::

            my_page.my_element1.copy()
            my_page.my_element2.paste()

        """
        first = Keys.COMMAND if platform.system().lower() == "darwin" else Keys.CONTROL
        try:
            self._if_force_relocate()
            self._present_cache.send_keys(first, 'v')
        except ELEMENT_REFERENCE_EXCEPTION:
            self.present.send_keys(first, 'v')
        return self

    def arrow_left(self, times: int = 1) -> Self:
        """
        Selenium API
        Send keys "ARROW_LEFT" to the element.

        Args:
            - times: The input times of key.

        Usage::

            my_page.my_element.arrow_left(3)

        """
        try:
            self._if_force_relocate()
            self._present_cache.send_keys(Keys.ARROW_LEFT * times)
        except ELEMENT_REFERENCE_EXCEPTION:
            self.present.send_keys(Keys.ARROW_LEFT * times)
        return self

    def arrow_right(self, times: int = 1) -> Self:
        """
        Selenium API
        Send keys "ARROW_RIGHT" to the element.

        Args:
            - times: The input times of key.

        Usage::

            my_page.my_element.arrow_right(3)

        """
        try:
            self._if_force_relocate()
            self._present_cache.send_keys(Keys.ARROW_RIGHT * times)
        except ELEMENT_REFERENCE_EXCEPTION:
            self.present.send_keys(Keys.ARROW_RIGHT * times)
        return self

    def arrow_up(self, times: int = 1) -> Self:
        """
        Selenium API
        Send keys "ARROW_UP" to the element.

        Args:
            - times: The input times of key.

        Usage::

            my_page.my_element.arrow_up(3)

        """
        try:
            self._if_force_relocate()
            self._present_cache.send_keys(Keys.ARROW_UP * times)
        except ELEMENT_REFERENCE_EXCEPTION:
            self.present.send_keys(Keys.ARROW_UP * times)
        return self

    def arrow_down(self, times: int = 1) -> Self:
        """
        Selenium API
        Send keys "ARROW_DOWN" to the element.

        Args:
            - times: The input times of key.

        Usage::

            my_page.my_element.arrow_down(3)

        """
        try:
            self._if_force_relocate()
            self._present_cache.send_keys(Keys.ARROW_DOWN * times)
        except ELEMENT_REFERENCE_EXCEPTION:
            self.present.send_keys(Keys.ARROW_DOWN * times)
        return self

    def backspace(self, times: int = 1) -> Self:
        """
        Selenium API
        Send keys BACKSPACE to the element.

        Args:
            - times: The input times of key.

        Usage::

            my_page.my_element.backspace(3).input('123456').enter()

        """
        try:
            self._if_force_relocate()
            self._present_cache.send_keys(Keys.BACKSPACE * times)
        except ELEMENT_REFERENCE_EXCEPTION:
            self.present.send_keys(Keys.BACKSPACE * times)
        return self

    def delete(self, times: int = 1) -> Self:
        """
        Selenium API
        Send keys DELETE to the element.

        Args:
            - times: The input times of key.

        Usage::

            my_page.my_element.delete(3)

        """
        try:
            self._if_force_relocate()
            self._present_cache.send_keys(Keys.DELETE * times)
        except ELEMENT_REFERENCE_EXCEPTION:
            self.present.send_keys(Keys.DELETE * times)
        return self

    def tab(self, times: int = 1) -> Self:
        """
        Selenium API
        Send keys TAB to the element.

        Args:
            - times: The input times of key.

        Usage::

            my_page.my_element.tab(2)

        """
        try:
            self._if_force_relocate()
            self._present_cache.send_keys(Keys.TAB * times)
        except ELEMENT_REFERENCE_EXCEPTION:
            self.present.send_keys(Keys.TAB * times)
        return self

    def space(self, times: int = 1) -> Self:
        """
        Selenium API
        Send keys SPACE to the element.

        Args:
            - times: The input times of key.

        Usage::

            my_page.my_element.space(4)

        """
        try:
            self._if_force_relocate()
            self._present_cache.send_keys(Keys.SPACE * times)
        except ELEMENT_REFERENCE_EXCEPTION:
            self.present.send_keys(Keys.SPACE * times)
        return self
