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

from typing import Callable, cast, Literal

from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement


class GenericECEX[WD: WebDriver, WE: WebElement]:

    @staticmethod
    def _find_element_by(
        driver: WD,
        locator: tuple[str, str],
        index: int | None
    ) -> WE:
        """
        Internal `find_element` using the `index` pattern.
        If an `IndexError` occurs, handle it as a `NoSuchElementException`.
        """
        if index is None:
            return cast(WE, driver.find_element(*locator))
        try:
            return cast(WE, driver.find_elements(*locator)[index])
        except IndexError as exc:
            raise NoSuchElementException from exc

    @staticmethod
    def _find_elements_by(
        driver: WD,
        locator: tuple[str, str]
    ) -> list[WE]:
        """
        Internal `find_elements` using the `NoSuchElementException` pattern.
        If the returned elements is `[]`, raise `NoSuchElementException`.
        """
        elements = driver.find_elements(*locator)
        if elements == []:
            raise NoSuchElementException
        return cast(list[WE], elements)

    @staticmethod
    def presence_of_element_located(
        locator: tuple[str, str],
        index: int | None
    ) -> Callable[[WD], WE]:
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

        def _predicate(driver: WD):
            return GenericECEX[WD, WE]._find_element_by(driver, locator, index)

        return _predicate

    @staticmethod
    def presence_of_all_elements_located(
        locator: tuple[str, str]
    ) -> Callable[[WD], list[WE]]:
        """
        Checks whether at least one element can be found using the locator.

        Args:
            locator: `(by, value)`.

        Returns:
            list[WebElement]:
                The list of `WebElement` if found,
                or the empty list `[]` if not found.
        """

        def _predicate(driver: WD):
            return driver.find_elements(*locator)

        return _predicate

    @staticmethod
    def absence_of_element_located(
        locator: tuple[str, str],
        index: int | None
    ) -> Callable[[WD], bool]:
        """
        Checks Whether the element **CANNOT be found** using the locator and index.

        Args:
            locator: `(by, value)`
            index: `None` for `find_element()`; `int` for `find_elements()[index]`.

        Returns:
            bool:
                `True` if the element **CANNOT be found**, `False` otherwise.
        """

        def _predicate(driver: WD):
            try:
                GenericECEX[WD, WE]._find_element_by(driver, locator, index)
                return False
            except NoSuchElementException:
                return True

        return _predicate

    @staticmethod
    def absence_of_all_elements_located(
        locator: tuple[str, str]
    ) -> Callable[[WD], bool]:
        """
        Checks Whether all elements **CANNOT be found** using the locator.

        Args:
            locator: `(by, value)`

        Returns:
            bool:
                `True` if all elements **CANNOT be found**, `False` otherwise.
        """

        def _predicate(driver: WD):
            return not driver.find_elements(*locator)

        return _predicate

    @staticmethod
    def visibility_of_element_located(
        locator: tuple[str, str],
        index: int | None
    ) -> Callable[[WD], WE | Literal[False]]:
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

        def _predicate(driver: WD):
            element = GenericECEX[WD, WE]._find_element_by(driver, locator, index)
            return element if element.is_displayed() else False

        return _predicate

    @staticmethod
    def visibility_of_element(
        element: WE
    ) -> Callable[[WD], WE | Literal[False]]:
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

    @staticmethod
    def visibility_of_any_elements_located(
        locator: tuple[str, str]
    ) -> Callable[[WD], list[WE]]:
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

        def _predicate(driver: WD):
            return [
                element
                for element in GenericECEX[WD, WE]._find_elements_by(driver, locator)
                if element.is_displayed()
            ]

        return _predicate

    @staticmethod
    def visibility_of_all_elements_located(
        locator: tuple[str, str]
    ) -> Callable[[WD], list[WE] | Literal[False]]:
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

        def _predicate(driver: WD):
            elements = GenericECEX[WD, WE]._find_elements_by(driver, locator)
            for element in elements:
                if not element.is_displayed():
                    return False
            return elements

        return _predicate

    @staticmethod
    def invisibility_of_element_located(
        locator: tuple[str, str],
        index: int | None,
        present: bool = True
    ) -> Callable[[WD], WE | bool]:
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

        def _predicate(driver: WD):
            try:
                element = GenericECEX[WD, WE]._find_element_by(driver, locator, index)
                return element if not element.is_displayed() else False
            except (NoSuchElementException, StaleElementReferenceException):
                if present:
                    raise
                return True

        return _predicate

    @staticmethod
    def invisibility_of_element(
        element: WE,
        present: bool = True
    ) -> Callable[[WD], WE | bool]:
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

    @staticmethod
    def element_located_to_be_clickable(
        locator: tuple[str, str],
        index: int | None
    ) -> Callable[[WD], WE | Literal[False]]:
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

        def _predicate(driver: WD):
            element = GenericECEX[WD, WE]._find_element_by(driver, locator, index)
            return element if element.is_displayed() and element.is_enabled() else False

        return _predicate

    @staticmethod
    def element_to_be_clickable(
        element: WE
    ) -> Callable[[WD], WE | Literal[False]]:
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

    @staticmethod
    def element_located_to_be_unclickable(
        locator: tuple[str, str],
        index: int | None,
        present: bool = True
    ) -> Callable[[WD], WE | bool]:
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

        def _predicate(driver: WD):
            try:
                element = GenericECEX[WD, WE]._find_element_by(driver, locator, index)
                return element if not (element.is_displayed() and element.is_enabled()) else False
            except (NoSuchElementException, StaleElementReferenceException):
                if present:
                    raise
                return True

        return _predicate

    @staticmethod
    def element_to_be_unclickable(
        element: WE,
        present: bool = True
    ) -> Callable[[WD], WE | bool]:
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

    @staticmethod
    def element_located_to_be_selected(
        locator: tuple[str, str],
        index: int | None
    ) -> Callable[[WD], WE | Literal[False]]:
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

        def _predicate(driver: WD):
            element = GenericECEX[WD, WE]._find_element_by(driver, locator, index)
            return element if element.is_selected() else False

        return _predicate

    @staticmethod
    def element_to_be_selected(
        element: WE
    ) -> Callable[[WD], WE | Literal[False]]:
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

    @staticmethod
    def element_located_to_be_unselected(
        locator: tuple[str, str],
        index: int | None
    ) -> Callable[[WD], WE | Literal[False]]:
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

        def _predicate(driver: WD):
            element = GenericECEX[WD, WE]._find_element_by(driver, locator, index)
            return element if not element.is_selected() else False

        return _predicate

    @staticmethod
    def element_to_be_unselected(
        element: WE
    ) -> Callable[[WD], WE | Literal[False]]:
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


class ECEX(GenericECEX[WebDriver, WebElement]):
    pass
