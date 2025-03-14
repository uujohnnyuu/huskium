# Author: Johnny Chou
# Email: johnny071531@gmail.com
# PyPI: https://pypi.org/project/huskium/
# GitHub: https://github.com/uujohnnyuu/huskium


from typing import Type

from selenium.common.exceptions import StaleElementReferenceException

from ..exception import NoSuchCacheException
from ..types import WebDriver
from .by import ByAttribute


# exception
ELEMENT_REFERENCE_EXCEPTIONS = (NoSuchCacheException, StaleElementReferenceException)
EXTENDED_IGNORED_EXCEPTIONS = (StaleElementReferenceException,)


# Page, Element, Elements
class _Name:
    _page = '_page'
    _present_cache = '_present_cache'
    _visible_cache = '_visible_cache'
    _clickable_cache = '_clickable_cache'
    _select_cache = '_select_cache'
    _caches = [_present_cache, _visible_cache, _clickable_cache, _select_cache]


class _Verify:

    @staticmethod
    def page(
        driver: WebDriver,
        timeout: int | float,
        reraise: bool,
        remark: str
    ) -> None:
        _Verify.driver(driver)
        _Verify.page_timeout(timeout)
        _Verify.reraise(reraise)
        _Verify.page_remark(remark)

    @staticmethod
    def element(
        by: str | None,
        value: str | None,
        index: int | None,
        timeout: int | float | None,
        cache: bool | None,
        remark: str | None
    ) -> None:
        _Verify.by(by)
        _Verify.value(value)
        _Verify.index(index)
        _Verify.timeout(timeout)
        _Verify.cache(cache)
        _Verify.remark(remark)

    @staticmethod
    def elements(
        by: str | None,
        value: str | None,
        timeout: int | float | None,
        remark: str | None
    ) -> None:
        _Verify.by(by)
        _Verify.value(value)
        _Verify.timeout(timeout)
        _Verify.remark(remark)

    @staticmethod
    def descriptor_get(
        instance: object,
        owner: Type,
        page: Type
    ) -> None:
        _Verify.descriptor_instance(instance, page)
        _Verify.descriptor_owner(owner, page)

    @staticmethod
    def descriptor_set(
        instance: object,
        page: Type,
        value: object,
        element: Type
    ) -> None:
        _Verify.descriptor_instance(instance, page)
        _Verify.descriptor_value(value, element)

    @staticmethod
    def driver(value: WebDriver) -> None:
        if not isinstance(value, WebDriver):
            raise TypeError(f'The "driver" must be "WebDriver", got {type(value).__name__}.')

    @staticmethod
    def page_timeout(value: int | float) -> None:
        if not isinstance(value, int | float):
            raise TypeError(f'The "timeout" must be "int" or "float", got {type(value).__name__}.')

    @staticmethod
    def reraise(value: bool) -> None:
        if not isinstance(value, bool):
            raise TypeError(f'The "reraise" must be "bool", got {type(value).__name__}.')

    @staticmethod
    def page_remark(value: str) -> None:
        if not isinstance(value, str):
            raise TypeError(f'The "remark" must be "str", got {type(value).__name__}.')

    @staticmethod
    def by(value: str | None) -> None:
        if value not in ByAttribute.VALUES_WITH_NONE:
            raise ValueError(f'The set "by" strategy "{value}" is undefined.')

    @staticmethod
    def value(value_: str | None) -> None:
        if not isinstance(value_, str | None):
            raise TypeError(f'The set "value" must be str, got {type(value_).__name__}.')

    @staticmethod
    def index(value: int | None) -> None:
        if not isinstance(value, int | None):
            raise TypeError(f'The set "index" must be int, got {type(value).__name__}.')

    @staticmethod
    def timeout(value: int | float | None) -> None:
        if not isinstance(value, int | float | None):
            raise TypeError(f'The set "timeout" must be int or float, got {type(value).__name__}.')

    @staticmethod
    def cache(value: bool | None) -> None:
        if not isinstance(value, bool | None):
            raise TypeError(f'The set "cache" must be bool, got {type(value).__name__}.')

    @staticmethod
    def remark(value: str | None) -> None:
        if not isinstance(value, str | None):
            raise TypeError(f'The set "remark" must be str, got {type(value).__name__}.')

    @staticmethod
    def descriptor_instance(instance: object, page: Type) -> None:
        if not isinstance(instance, page):
            raise TypeError(f'Element must be used within Page, got {type(instance).__name__}.')

    @staticmethod
    def descriptor_owner(owner: Type, page: Type) -> None:
        if not issubclass(owner, page):
            raise TypeError(f'Element must be used in a Page subclass, got {owner.__name__}.')

    @staticmethod
    def descriptor_value(value: object, element: Type) -> None:
        if not isinstance(value, element):
            raise TypeError(f'Assigned value must be an Element, got {type(value).__name__}.')


class Offset:
    """
    All Offset attributes store `(start_x, start_y, end_x, end_y)`.
    Used in `Page` and `Element` to set the `offset` action for
    `swipe_by` and `flick_by`.
    """

    UP: tuple = (0.5, 0.75, 0.5, 0.25)
    """Swipe up (bottom to top)."""

    DOWN: tuple = (0.5, 0.25, 0.5, 0.75)
    """Swipe down (top to bottom)."""

    LEFT: tuple = (0.75, 0.5, 0.25, 0.5)
    """Swipe left (right to left)."""

    RIGHT: tuple = (0.25, 0.5, 0.75, 0.5)
    """Swipe right (left to right)."""

    UPPER_LEFT: tuple = (0.75, 0.75, 0.25, 0.25)
    """Swipe upper left (lower right to upper left)."""

    UPPER_RIGHT: tuple = (0.25, 0.75, 0.75, 0.25)
    """Swipe upper right (lower left to upper right)."""

    LOWER_LEFT: tuple = (0.75, 0.25, 0.25, 0.75)
    """Swipe lower left (upper right to lower left)."""

    LOWER_RIGHT: tuple = (0.25, 0.25, 0.75, 0.75)
    """Swipe lower right (upper left to lower right)."""


class Area:
    """
    All Area attributes store `(x, y, width, height)`.
    Used in `Page` and `Element` to set the `area` action for
    `swipe_by` and `flick_by`.
    """

    FULL: tuple = (0.0, 0.0, 1.0, 1.0)
    """Full window size."""
