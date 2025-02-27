# Author: Johnny Chou
# Email: johnny071531@gmail.com
# PyPI: https://pypi.org/project/huskium/
# GitHub: https://github.com/uujohnnyuu/huskium


"""
Expected Conditions Extension (ECEX)

Overview:
    ECEX extends official `expected_conditions (EC)` module.

Locator Handling:
    The `locator` follows the same structure as `EC`.

Index Feature:
    The `index` allows using the `find_elements(*locator)[index]` pattern.
    If `index` is `None`, `find_element(*locator)` is used instead.

Exception Handling:
    ECEX separates methods for locators and WebElements to enable more robust
    exception handling.
"""


from __future__ import annotations

from typing import Callable, Literal

from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException

from ..types import AppiumWebDriver, WebDriver, WebElement


def _find_element_by(
    driver: WebDriver,
    locator: tuple[str, str],
    index: int | None
) -> WebElement:
    """
    Internal `find_element` using the `index` pattern.
    If an `IndexError` occurs, handle it as a `NoSuchElementException`.
    """
    if index is None:
        return driver.find_element(*locator)
    try:
        return driver.find_elements(*locator)[index]
    except IndexError as exc:
        raise NoSuchElementException from exc


def _find_elements_by(
    driver: WebDriver,
    locator: tuple[str, str]
) -> list[WebElement]:
    """
    Internal `find_elements` using the `NoSuchElementException` pattern.
    If the returned elements is `[]`, raise `NoSuchElementException`.
    """
    elements = driver.find_elements(*locator)
    if elements == []:
        raise NoSuchElementException
    return elements


def presence_of_element_located(
    locator: tuple[str, str],
    index: int | None
) -> Callable[[WebDriver], WebElement]:
    """
    Checks whether the element can be found using the locator and index.

    Args:
        locator: `(by, value)`.
        index: `None` for `find_element()`; `int` for `find_elements()[index]`.

    Returns:
        WebElement:
            The `WebElement` if found.

    Raises:
        NoSuchElementException: Raised if the element cannot be found.
            Ignored by default in `WebDriverWait`.
    """

    def _predicate(driver: WebDriver):
        return _find_element_by(driver, locator, index)

    return _predicate


def presence_of_all_elements_located(
    locator: tuple[str, str]
) -> Callable[[WebDriver], list[WebElement]]:
    """
    Checks whether at least one element can be found using the locator.

    Args:
        locator: `(by, value)`.

    Returns:
        list[WebElement]:
            The list of `WebElement` if found,
            or the empty list `[]` if not found.
    """

    def _predicate(driver: WebDriver):
        return driver.find_elements(*locator)

    return _predicate


def absence_of_element_located(
    locator: tuple[str, str],
    index: int | None
) -> Callable[[WebDriver], bool]:
    """
    Checks Whether the element **CANNOT be found** using the locator and index.

    Args:
        locator: `(by, value)`
        index: `None` for `find_element()`; `int` for `find_elements()[index]`.

    Returns:
        bool:
            `True` if the element **CANNOT be found**, `False` otherwise.
    """

    def _predicate(driver: WebDriver):
        try:
            _find_element_by(driver, locator, index)
            return False
        except NoSuchElementException:
            return True

    return _predicate


def absence_of_all_elements_located(
    locator: tuple[str, str]
) -> Callable[[WebDriver], bool]:
    """
    Checks Whether all elements **CANNOT be found** using the locator.

    Args:
        locator: `(by, value)`

    Returns:
        bool:
            `True` if all elements **CANNOT be found**, `False` otherwise.
    """

    def _predicate(driver: WebDriver):
        return not driver.find_elements(*locator)

    return _predicate


def visibility_of_element_located(
    locator: tuple[str, str],
    index: int | None
) -> Callable[[WebDriver], WebElement | Literal[False]]:
    """
    Checks Whether the element can be visible using the locator and index.

    Args:
        locator: `(by, value)`
        index: `None` for `find_element()`; `int` for `find_elements()[index]`.

    Returns:
        (WebElement | False):
            `WebElement` if the found element is visible, `False` otherwise.

    Raises:
        NoSuchElementException: Raised if the element cannot be found.
            Ignored by default in `WebDriverWait`.
        StaleElementReferenceException: Raised if the found element is stale.
            Optionally Ignored in `WebDriverWait`.
    """

    def _predicate(driver: WebDriver):
        element = _find_element_by(driver, locator, index)
        return element if element.is_displayed() else False

    return _predicate


def visibility_of_element(
    element: WebElement
) -> Callable[[WebDriver], WebElement | Literal[False]]:
    """
    Checks Whether the element can be visible using the present element.

    Args:
        element: The present element.

    Returns:
        (WebElement | False):
            `WebElement` if the present element is visible, `False` otherwise.

    Raises:
        StaleElementReferenceException: Raised if the present element is stale.
            Can be optionally caught and handled by relocating it using
            `visibility_of_element_located()` in an external process.
    """

    def _predicate(_):
        return element if element.is_displayed() else False

    return _predicate


def visibility_of_any_elements_located(
    locator: tuple[str, str]
) -> Callable[[WebDriver], list[WebElement]]:
    """
    Checks Whether at least one element can be visible using the locator.

    Args:
        locator (tuple): `(by, value)`

    Returns:
        list[WebElement]:
            The list of `WebElement` if at least one element is visible;
            otherwise, the empty list `[]` if all elements are invisible.

    Raises:
        NoSuchElementException: Raised if any elements cannot be found.
            Ignored by default in `WebDriverWait`.
        StaleElementReferenceException: Raised if any found element is stale.
            Optionally Ignored in `WebDriverWait`.
    """

    def _predicate(driver: WebDriver):
        return [
            element
            for element in _find_elements_by(driver, locator)
            if element.is_displayed()
        ]

    return _predicate


def visibility_of_all_elements_located(
    locator: tuple[str, str]
) -> Callable[[WebDriver], list[WebElement] | Literal[False]]:
    """
    Checks Whether all elements can be visible using the locator.

    Args:
        locator (tuple): `(by, value)`

    Returns:
        (list[WebElement] | False):
            The list of `WebElement` if all elements are visible;
            otherwise, `False` if at least one element is invisible.

    Raises:
        NoSuchElementException: Raised if any element cannot be found.
            Ignored by default in `WebDriverWait`.
        StaleElementReferenceException: Raised if any found element is stale.
            Optionally Ignored in `WebDriverWait`.
    """

    def _predicate(driver: WebDriver):
        elements = _find_elements_by(driver, locator)
        for element in elements:
            if not element.is_displayed():
                return False
        return elements

    return _predicate


def invisibility_of_element_located(
    locator: tuple[str, str],
    index: int | None,
    present: bool = True
) -> Callable[[WebDriver], WebElement | bool]:
    """
    Checks Whether the element can be **invisible or absent**
    using the locator and index.

    Args:
        locator: `(by, value)`
        index: `None` for `find_element()`; `int` for `find_elements()[index]`.
        present: `True` for the element must be present;
            otherwise, it can be absent.

    Returns:
        (WebElement | bool):
            `WebElement` if the element is invisible.
            If `True`, the element is absent and `present` is `False`.
            If `False`, the element is still visible.

    Raises:
        NoSuchElementException: Raised if the element is
            absent and `present` is `True`.
            Ignored by default in `WebDriverWait`.
        StaleElementReferenceException: Raised if the found element is
            stale and `present` is `True`.
            Optionally Ignored in `WebDriverWait`.
    """

    def _predicate(driver: WebDriver):
        try:
            element = _find_element_by(driver, locator, index)
            return element if not element.is_displayed() else False
        except (NoSuchElementException, StaleElementReferenceException):
            if present:
                raise
            return True

    return _predicate


def invisibility_of_element(
    element: WebElement,
    present: bool = True
) -> Callable[[WebDriver], WebElement | bool]:
    """
    Checks Whether the element can be **invisible or absent**
    using the present element.

    Args:
        element (WebElement): The present element.
        present: `True` for the element must be present;
            otherwise, it can be absent.

    Returns:
        (WebElement | bool):
            `WebElement` if the element is invisible.
            If `True`, the element is stale and `present` is `False`.
            If `False`, the element is still visible.

    Raises:
        StaleElementReferenceException: Raised if the found element is stale.
            Can be optionally caught and handled by relocating it using
            `invisibility_of_element_located()` in an external process.
    """

    def _predicate(_):
        try:
            return element if not element.is_displayed() else False
        except StaleElementReferenceException:
            if present:
                raise
            return True

    return _predicate


def element_located_to_be_clickable(
    locator: tuple[str, str],
    index: int | None
) -> Callable[[WebDriver], WebElement | Literal[False]]:
    """
    Checks Whether the element can be clickable using the locator and index.

    Args:
        locator: `(by, value)`
        index: `None` for `find_element()`; `int` for `find_elements()[index]`.

    Returns:
        (WebElement | False):
            `WebElement` if the found element is clickable, `False` otherwise.

    Raises:
        NoSuchElementException: Raised if the element cannot be found.
            Ignored by default in `WebDriverWait`.
        StaleElementReferenceException: Raised if the found element is stale.
            Optionally Ignored in `WebDriverWait`.
    """

    def _predicate(driver: WebDriver):
        element = _find_element_by(driver, locator, index)
        return element if element.is_displayed() and element.is_enabled() else False

    return _predicate


def element_to_be_clickable(
    element: WebElement
) -> Callable[[WebDriver], WebElement | Literal[False]]:
    """
    Checks Whether the element can be clickable using the present element.

    Args:
        element (WebElement): The present element.

    Returns:
        (WebElement | False):
            `WebElement` if the present element is clickable, `False` otherwise.

    Raises:
        StaleElementReferenceException: Raised if the present element is stale.
            Can be optionally caught and handled by relocating it using
            `element_located_to_be_clickable()` in an external process.
    """

    def _predicate(_):
        return element if element.is_displayed() and element.is_enabled() else False

    return _predicate


def element_located_to_be_unclickable(
    locator: tuple[str, str],
    index: int | None,
    present: bool = True
) -> Callable[[WebDriver], WebElement | bool]:
    """
    Checks Whether the element can be **unclickable or absent**
    using the locator and index.

    Args:
        locator: `(by, value)`
        index: `None` for `find_element()`; `int` for `find_elements()[index]`.
        present: `True` for the element must be present;
            otherwise, it can be absent.

    Returns:
        (WebElement | bool):
            WebElement` if the element is unclickable.
            If `True`, the element is absent and `present` is `False`.
            If `False`, the element is still clickable.

    Raises:
        NoSuchElementException: Raised if the element is
            absent and `present` is `True`.
            Ignored by default in `WebDriverWait`.
        StaleElementReferenceException: Raised if the found element is
            stale and `present` is `True`.
            Optionally Ignored in `WebDriverWait`.
    """

    def _predicate(driver: WebDriver):
        try:
            element = _find_element_by(driver, locator, index)
            return element if not (element.is_displayed() and element.is_enabled()) else False
        except (NoSuchElementException, StaleElementReferenceException):
            if present:
                raise
            return True

    return _predicate


def element_to_be_unclickable(
    element: WebElement,
    present: bool = True
) -> Callable[[WebDriver], WebElement | bool]:
    """
    Checks Whether the element can be **unclickable or absent**
    using the present element.

    Args:
        element (WebElement): The present element.
        present: `True` for the element must be present;
            otherwise, it can be absent.

    Returns:
        (WebElement | bool):
            `WebElement` if the element is unclickable.
            If `True`, the element is stale and `present` is `False`.
            If `False`, the element is still clickable.

    Raises:
        StaleElementReferenceException: Raised if the found element is stale.
            Can be optionally caught and handled by relocating it using
            `element_located_to_be_unclickable()` in an external process.
    """

    def _predicate(_):
        try:
            return element if not (element.is_displayed() and element.is_enabled()) else False
        except StaleElementReferenceException:
            if present:
                raise
            return True

    return _predicate


def element_located_to_be_selected(
    locator: tuple[str, str],
    index: int | None
) -> Callable[[WebDriver], WebElement | Literal[False]]:
    """
    Checks Whether the element can be selected using the locator and index.

    Args:
        locator: `(by, value)`
        index: `None` for `find_element()`; `int` for `find_elements()[index]`.

    Returns:
        (WebElement | False):
            `WebElement` if the found element is selected, `False` otherwise.

    Raises:
        NoSuchElementException: Raised if the element cannot be found.
            Ignored by default in `WebDriverWait`.
        StaleElementReferenceException: Raised if the found element is stale.
            Optionally Ignored in `WebDriverWait`.
    """

    def _predicate(driver: WebDriver):
        element = _find_element_by(driver, locator, index)
        return element if element.is_selected() else False

    return _predicate


def element_to_be_selected(
    element: WebElement
) -> Callable[[WebDriver], WebElement | Literal[False]]:
    """
    Checks Whether the element can be selected using the present element.

    Args:
        element (WebElement): The present element.

    Returns:
        (WebElement | False):
            `WebElement` if the present element is selected, `False` otherwise.

    Raises:
        StaleElementReferenceException: Raised if the present element is stale.
            Can be optionally caught and handled by relocating it using
            `element_located_to_be_selected()` in an external process.
    """

    def _predicate(_):
        return element if element.is_selected() else False

    return _predicate


def element_located_to_be_unselected(
    locator: tuple[str, str],
    index: int | None
) -> Callable[[WebDriver], WebElement | Literal[False]]:
    """
    Checks Whether the element can be unselected using the locator and index.

    Args:
        locator: `(by, value)`
        index: `None` for `find_element()`; `int` for `find_elements()[index]`.

    Returns:
        (WebElement | False):
            WebElement` if the found element is unselected, `False` otherwise.

    Raises:
        NoSuchElementException: Raised if the element cannot be found.
            Ignored by default in `WebDriverWait`.
        StaleElementReferenceException: Raised if the found element is stale.
            Optionally Ignored in `WebDriverWait`.
    """

    def _predicate(driver: WebDriver):
        element = _find_element_by(driver, locator, index)
        return element if not element.is_selected() else False

    return _predicate


def element_to_be_unselected(
    element: WebElement
) -> Callable[[WebDriver], WebElement | Literal[False]]:
    """
    Checks Whether the element can be unselected using the present element.

    Args:
        element: The present element.

    Returns:
        (WebElement | False):
            `WebElement` if the present element is unselected,
            `False` otherwise.

    Raises:
        StaleElementReferenceException: Raised if the present element is stale.
            Can be optionally caught and handled by relocating it using
            `element_located_to_be_unselected()` in an external process.
    """

    def _predicate(_):
        return element if not element.is_selected() else False

    return _predicate


def webview_is_present(
    switch: bool = True,
    index: int = -1
) -> Callable[[AppiumWebDriver], list[str] | Literal[False]]:
    """
    Whether `WEBVIEW` context is present.

    Args:
        switch: Switch to the `WEBVIEW` context
            when it exists and `switch` is `True`.
        index: Switch to the specified context index,
            defaulting to the most recently appeared.

    Returns:
        (list[str] | False):
            All current contexts `list[str]` when a `WEBVIEW` exists;
            otherwise, `False` when no `WEBVIEW` exists.
    """

    def _predicate(driver: AppiumWebDriver):
        contexts = driver.contexts
        if any('WEBVIEW' in context for context in contexts):
            if switch:
                driver.switch_to.context(contexts[index])
            return contexts
        return False

    return _predicate
