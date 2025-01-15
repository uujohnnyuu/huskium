# Author: Johnny Chou
# Email: johnny071531@gmail.com
# PyPI: https://pypi.org/project/huskium/
# GitHub: https://github.com/uujohnnyuu/huskium

# We do not store found elements within the Elements class because
# the results of find_elements can easily change due to platform or operational differences.
# Therefore, searching again each time is more robust and can help avoid unexpected errors.
# If there is a need for repeated use,
# you can construct a custom function or
# inherit from this class to define your own handling.


from __future__ import annotations

from typing import Literal, Self, Type, TypeVar

from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.types import WaitExcTypes

from . import ec_extension as ecex
from .config import Timeout
from .by import ByAttribute
from .page import Page
from .types import WebDriver, WebElement


P = TypeVar('P', bound=Page)


class Elements:

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
            - by:
                - None (default): Initialize an empty descriptor.
                - str: Use `from huskypo import By` for Selenium and Appium locators.
            - value:
                - None (default): Initialize an empty descriptor.
                - str: The locator value.
            - timeout:
                - None (default): Uses `Timeout.DEFAULT` in seconds.
                - int, float: Explicit wait time in seconds.
            - remark:
                - None (default): Auto-generates remark info as
                    `(by="{by}", value="{value}")`.
                - str: Custom remark for identification or logging.
        """
        if by not in ByAttribute.VALUES_WITH_NONE:
            raise ValueError(f'The locator strategy "{by}" is undefined.')
        if not isinstance(value, (str, type(None))):
            raise TypeError(
                'The locator value type should be "str", '
                f'not "{type(value).__name__}".'
            )
        if not isinstance(timeout, (int, float, type(None))):
            raise TypeError(
                'The timeout type should be "int" or "float", '
                f'not "{timeout.__name__}".'
            )
        if not isinstance(remark, (str, type(None))):
            raise TypeError(
                'The remark type should be "str", '
                f'not "{remark.__name__}".'
            )
        self._by = by
        self._value = value
        self._timeout = timeout
        self._remark = remark

    def __get__(self, instance: P, owner: Type[P] | None = None) -> Self:
        """
        Make "Elements" a descriptor of "Page".
        """
        if not isinstance(instance, Page):
            raise TypeError(f'"{self.__class__.__name__}" must be used with a "Page" instance.')
        self._page = instance
        return self

    def __set__(self, instance: P, value: Elements):
        """
        Set dynamic element by `self.elements = Elements(...)` pattern.
        """
        # NOTE Avoid using self.__init__() here, as it may reset the descriptor.
        self.dynamic(
            value.by,
            value.value,
            timeout=value.timeout,
            remark=value.remark
        )

    def dynamic(
        self,
        by: str,
        value: str,
        *,
        timeout: int | float | None = None,
        remark: str | None = None
    ) -> Self:
        """
        In a Page subclass, use a data descriptor to define dynamic elements.
        This is a simplified version of the __set__ method.

        Usage::

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
        # NOTE Avoid using self.__init__() here, as it will reset the descriptor.
        if by not in ByAttribute.VALUES:  # Cannot be None in dynamic.
            raise ValueError(f'The locator strategy "{by}" is undefined.')
        if not isinstance(value, str):  # Cannot be None in dynamic.
            raise TypeError(
                'The locator value type should be "str", '
                f'not "{type(value).__name__}".'
            )
        if not isinstance(timeout, (int, float, type(None))):
            raise TypeError(
                'The timeout type should be "int" or "float", '
                f'not "{timeout.__name__}".'
            )
        if not isinstance(remark, (str, type(None))):
            raise TypeError(
                'The remark type should be "str", '
                f'not "{remark.__name__}".'
            )
        self._by = by
        self._value = value
        self._timeout = timeout
        self._remark = remark
        return self

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
            '"by" and "value" cannot be None when performing elements operations. '
            'Please ensure both are provided with valid values.'
        )

    @property
    def timeout(self):
        """
        If initial timeout is None, return `Timeout.DEFAULT`.
        """
        return Timeout.DEFAULT if self._timeout is None else self._timeout

    @property
    def remark(self):
        """
        If initial remark is None, return (by="{by}", value="{value}").
        """
        return self._remark or f'(by="{self._by}", value="{self._value}")'

    @property
    def driver(self) -> WebDriver:
        """
        Get driver from Page.
        """
        return self._page._driver

    def find_elements(self) -> list[WebElement]:
        """
        Using the traditional `find_elements()` to locate elements.
        Note that if there are no any element found,
        it will return empty list `[]`.
        """
        return self.driver.find_elements(*self.locator)

    def wait(
        self,
        timeout: int | float | None = None,
        ignored_exceptions: WaitExcTypes | None = None
    ) -> WebDriverWait:
        """
        Get an object of WebDriverWait.
        The ignored exceptions include NoSuchElementException and StaleElementReferenceException
        to capture their stacktrace when a TimeoutException occurs.

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
    def wait_timeout(self):
        """
        Get the final waiting timeout of the element.
        If no element action has been executed yet,
        it will return None.
        """
        try:
            return self._wait_timeout
        except AttributeError:
            return None

    def _timeout_message(self, status: str) -> str:
        """
        Waiting for elements "{self.remark}" to become "{status}" timed out
        after {self._wait_timeout} seconds.
        """
        return (
            f'Waiting for elements "{self.remark}" to become "{status}" timed out '
            f'after {self._wait_timeout} seconds.'
        )

    def find(
        self,
        index: int | None = None,
        timeout: int | float | None = None,
        reraise: bool | None = None
    ) -> list[WebElement] | WebElement | Literal[False]:
        """
        Selenium and Appium API.
        Wait for the element or elements to be `present`.

        Args:
            - index:
                - int: It will returns an element by list index of elements.
                - None: It will returns all elements.
            - timeout: Maximum time in seconds to wait for
                the element or elements to become present.
            - reraise: True means reraising TimeoutException; vice versa.

        Returns:
            - list[WebElement]: All elements when index is None.
            - WebElement: Element by list index of elements when index is int.
            - False: No any element is present.
        """
        elements = self.wait_all_present(timeout, reraise)
        if index is not None:
            try:
                return elements[index]
            except TypeError:
                # TypeError: Raised when False[index] is accessed with reraise set to False,
                #   resulting in a reraised TimeoutException.
                # IndexError: Raised when elements exist, but no index is specified.
                raise TimeoutException(self._timeout_message('all present'))
        return elements

    @property
    def all_present(self) -> list[WebElement]:
        """
        The same as `elements.wait_all_present(reraise=True)`.
        """
        return self.wait_all_present(reraise=True)

    @property
    def all_visible(self) -> list[WebElement]:
        """
        The same as `elements.wait_all_visible(reraise=True)`.
        """
        return self.wait_all_visible(reraise=True)

    @property
    def any_visible(self) -> list[WebElement]:
        """
        The same as elements.wait_any_visible(reraise=True).
        """
        return self.wait_any_visible(reraise=True)

    def wait_all_present(
        self,
        timeout: int | float | None = None,
        reraise: bool | None = None
    ) -> list[WebElement] | Literal[False]:
        """
        Waiting for "any elements to become present".
        Note that "all" here means "at least one (any)" for
        the logic of find_elements is to find at least one matched elements.

        Args:
            - timeout: Maximum wait time (in seconds) for the element to reach the expected state.
                Defaults to the element's timeout value if None.
            - reraise: Determines behavior when the element state is not as expected:
                - bool: True to raise a TimeoutException; False to return False.
                - None: Follows `Timeout.RERAISE`.

        Returns:
            - list[WebElement] (Expected): The elements reached the expected status
                before the timeout.
            - False (Unexpected): The elements failed to reach the expected state
                if `reraise` is False.

        Exception:
            - TimeoutException: Raised if `reraise` is True and
                the elements did not reach the expected state within the timeout.
        """
        try:
            return self.wait(timeout).until(
                ecex.presence_of_all_elements_located(self.locator),
                self._timeout_message('any elements are present')
            )
        except TimeoutException:
            if Timeout.reraise(reraise):
                raise
            return False

    def wait_all_absent(
        self,
        timeout: int | float | None = None,
        reraise: bool | None = None
    ) -> bool:
        """
        Waiting for "all elements to become absent".

        Args:
            - timeout: Maximum wait time (in seconds) for the element to reach the expected state.
                Defaults to the element's timeout value if None.
            - reraise: Determines behavior when the element state is not as expected:
                - bool: True to raise a TimeoutException; False to return False.
                - None: Follows `Timeout.RERAISE`.

        Returns:
            - True (Expected): The elements reached the expected status before the timeout.
            - False (Unexpected): The elements failed to reach the expected state
                if `reraise` is False.

        Exception:
            - TimeoutException: Raised if `reraise` is True and
                the elements did not reach the expected state within the timeout.
        """
        try:
            return self.wait(timeout).until(
                ecex.absence_of_all_elements_located(self.locator),
                self._timeout_message('all elements are absent')
            )
        except TimeoutException:
            if Timeout.reraise(reraise):
                raise
            return False

    def wait_all_visible(
        self,
        timeout: int | float | None = None,
        reraise: bool | None = None
    ) -> list[WebElement] | Literal[False]:
        """
        Waiting for "all elements to become visible".

        Args:
            - timeout: Maximum wait time (in seconds) for the element to reach the expected state.
                Defaults to the element's timeout value if None.
            - reraise: Determines behavior when the element state is not as expected:
                - bool: True to raise a TimeoutException; False to return False.
                - None: Follows `Timeout.RERAISE`.

        Returns:
            - list[WebElement] (Expected): The elements reached the expected status
                before the timeout.
            - False (Unexpected): The elements failed to reach the expected state
                if `reraise` is False.

        Exception:
            - TimeoutException: Raised if `reraise` is True and
                the elements did not reach the expected state within the timeout.
        """
        try:
            return self.wait(timeout, StaleElementReferenceException).until(
                ecex.visibility_of_all_elements_located(self.locator),
                self._timeout_message('all elements are visible')
            )
        except TimeoutException:
            if Timeout.reraise(reraise):
                raise
            return False

    def wait_any_visible(
        self,
        timeout: int | float | None = None,
        reraise: bool | None = None
    ) -> list[WebElement] | Literal[False]:
        """
        Waiting for "any elements to become visible".

        Args:
            - timeout: Maximum wait time (in seconds) for the element to reach the expected state.
                Defaults to the element's timeout value if None.
            - reraise: Determines behavior when the element state is not as expected:
                - bool: True to raise a TimeoutException; False to return False.
                - None: Follows `Timeout.RERAISE`.

        Returns:
            - list[WebElement] (Expected): The elements reached the expected status
                before the timeout.
            - False (Unexpected): The elements failed to reach the expected state
                if `reraise` is False.

        Exception:
            - TimeoutException: Raised if `reraise` is True and
                the elements did not reach the expected state within the timeout.
        """
        try:
            return self.wait(timeout, StaleElementReferenceException).until(
                ecex.visibility_of_any_elements_located(self.locator),
                self._timeout_message('any elements are visible')
            )
        except TimeoutException:
            if Timeout.reraise(reraise):
                raise
            return False

    def are_all_present(self, timeout: int | float | None = None) -> bool:
        """
        Selenium and Appium API.
        Whether the all elements are present.

        Args:
            - timeout: Maximum time in seconds to wait for the element to become present.

        Returns:
            - True: All the elements are present before timeout.
            - False: All the elements are still not present after timeout.
        """
        return True if self.wait_all_present(timeout, False) else False

    def are_all_visible(self) -> bool:
        """
        Selenium and Appium API.
        Whether all the elements are visible.

        Returns:
            - True: All the elements are visible.
            - False: At least one element is not visible.
        """
        for element in self.all_present:
            if not element.is_displayed():
                return False
        return True

    def are_any_visible(self) -> bool:
        """
        Selenium and Appium API.
        Whether at least one element is visible.

        Returns:
            - True: At least one element is visible.
            - False: All the elements are not visible.
        """
        return True if [
            element
            for element in self.all_present
            if element.is_displayed()
        ] else False

    @property
    def quantity(self) -> int:
        """
        Selenium and Appium API.
        Get the quantity of all present elements.
        """
        try:
            return len(self.all_present)
        except TimeoutException:
            return 0

    @property
    def all_visible_quantity(self) -> int:
        """
        Selenium and Appium API.
        Get the quantity of all visible elements.
        """
        try:
            return len(self.all_visible)
        except TimeoutException:
            return 0

    @property
    def any_visible_quantity(self) -> int:
        """
        Selenium and Appium API.
        Get the quantity of any visible elements.
        """
        try:
            return len(self.any_visible)
        except TimeoutException:
            return 0

    @property
    def texts(self) -> list[str]:
        """
        Selenium and Appium API.
        Gets texts of all present elements.
        """
        return [element.text for element in self.all_present]

    @property
    def all_visible_texts(self) -> list[str]:
        """
        Selenium and Appium API.
        Gets texts of all visible elements.
        """
        return [element.text for element in self.all_visible]

    @property
    def any_visible_texts(self) -> list[str]:
        """
        Selenium and Appium API.
        WebElements: find_elements(by, value)
        Gets texts of `at least one` visible element.
        """
        return [element.text for element in self.any_visible]

    @property
    def rects(self) -> list[dict[str, int]]:
        """
        Selenium and Appium API.
        Gets locations relative to the view and size of all present elements.
        """
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
    def all_visible_rects(self) -> list[dict[str, int]]:
        """
        Selenium and Appium API.
        Gets locations relative to the view and size of all visible elements.
        """
        return [
            {
                'x': rect['x'],
                'y': rect['y'],
                'width': rect['width'],
                'height': rect['height']
            }
            for element in self.all_visible
            for rect in [element.rect]
        ]

    @property
    def any_visible_rects(self) -> list[dict[str, int]]:
        """
        Selenium and Appium API.
        Gets locations relative to the view and size of any visible elements.
        """
        return [
            {
                'x': rect['x'],
                'y': rect['y'],
                'width': rect['width'],
                'height': rect['height']
            }
            for element in self.any_visible
            for rect in [element.rect]
        ]

    @property
    def locations(self) -> list[dict[str, int]]:
        """
        Selenium and Appium API.
        Gets locations of all present elements.
        """
        return [element.location for element in self.all_present]

    @property
    def all_visible_locations(self) -> list[dict[str, int]]:
        """
        Selenium and Appium API.
        Gets locations of all visible elements.
        """
        return [element.location for element in self.all_visible]

    @property
    def any_visible_locations(self) -> list[dict[str, int]]:
        """
        Selenium and Appium API.
        Gets locations of any visible elements.
        """
        return [element.location for element in self.any_visible]

    @property
    def sizes(self) -> list[dict[str, int]]:
        """
        Selenium and Appium API.
        Gets sizes of all present elements.
        Note that it will rearrange size to {'width': width, 'height': height}
        """
        return [
            {
                'width': size['width'],
                'height': size['height']
            }
            for element in self.all_present
            for size in [element.size]
        ]

    @property
    def all_visible_sizes(self) -> list[dict[str, int]]:
        """
        Selenium and Appium API.
        Gets sizes of all visible elements.
        Note that it will rearrange size to {'width': width, 'height': height}
        """
        return [
            {
                'width': size['width'],
                'height': size['height']
            }
            for element in self.all_visible
            for size in [element.size]
        ]

    @property
    def any_visible_sizes(self) -> list[dict[str, int]]:
        """
        Selenium and Appium API.
        Gets sizes of any visible elements.
        Note that it will rearrange size to {'width': width, 'height': height}
        """
        return [
            {
                'width': size['width'],
                'height': size['height']
            }
            for element in self.any_visible
            for size in [element.size]
        ]

    @property
    def centers(self) -> list[dict[str, int]]:
        """
        Selenium and Appium API.
        Gets center locations relative to the view of all present elements.
        """
        return [
            {
                'x': int(rect['x'] + rect['width'] / 2),
                'y': int(rect['y'] + rect['height'] / 2)
            }
            for element in self.all_present
            for rect in [element.rect]
        ]

    @property
    def all_visible_centers(self) -> list[dict[str, int]]:
        """
        Selenium and Appium API.
        Gets center locations relative to the view of all visible elements.
        """
        return [
            {
                'x': int(rect['x'] + rect['width'] / 2),
                'y': int(rect['y'] + rect['height'] / 2)
            }
            for element in self.all_visible
            for rect in [element.rect]
        ]

    @property
    def any_visible_centers(self) -> list[dict[str, int]]:
        """
        Selenium and Appium API.
        Gets center locations relative to the view of any visible elements.
        """
        return [
            {
                'x': int(rect['x'] + rect['width'] / 2),
                'y': int(rect['y'] + rect['height'] / 2)
            }
            for element in self.any_visible
            for rect in [element.rect]
        ]

    def get_attributes(self, name: str) -> list[str | dict | None]:
        """
        Selenium and Appium API.
        Gets specific attributes or properties of all present elements.
        """
        return [element.get_attribute(name) for element in self.all_present]

    def get_all_visible_attributes(self, name: str) -> list[str | dict | None]:
        """
        Selenium and Appium API.
        Gets specific attributes or properties of all visible elements.
        """
        return [element.get_attribute(name) for element in self.all_visible]

    def get_any_visible_attributes(self, name: str) -> list[str | dict | None]:
        """
        Selenium and Appium API.
        Gets specific attributes or properties of any visible elements.
        """
        return [element.get_attribute(name) for element in self.any_visible]

    def get_properties(self, name: str) -> list[WebElement | bool | dict | str]:
        """
        Selenium API.
        Gets specific properties of all present elements.
        """
        return [element.get_property(name) for element in self.all_present]

    def get_all_visible_properties(self, name: str) -> list[WebElement | bool | dict | str]:
        """
        Selenium API.
        Gets specific properties of all visible elements.
        """
        return [element.get_property(name) for element in self.all_visible]

    def get_any_visible_properties(self, name: str) -> list[WebElement | bool | dict | str]:
        """
        Selenium API.
        Gets specific properties of any visible elements.
        """
        return [element.get_property(name) for element in self.any_visible]

    @property
    def locations_in_view(self) -> list[dict[str, int]]:
        """
        Appium API.
        Gets locations relative to the view of all present elements.
        """
        return [element.location_in_view for element in self.all_present]

    @property
    def all_visible_locations_in_view(self) -> list[dict[str, int]]:
        """
        Appium API.
        Gets locations relative to the view of all visible elements.
        """
        return [element.location_in_view for element in self.all_visible]

    @property
    def any_visible_locations_in_view(self) -> list[dict[str, int]]:
        """
        Appium API.
        Gets locations relative to the view of any visible elements.
        """
        return [element.location_in_view for element in self.any_visible]
