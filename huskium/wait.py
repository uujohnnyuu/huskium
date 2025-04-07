# Author: Johnny Chou
# Email: johnny071531@gmail.com
# PyPI: https://pypi.org/project/huskium/
# GitHub: https://github.com/uujohnnyuu/huskium


from typing import Iterable, Type

from selenium.webdriver.support.wait import IGNORED_EXCEPTIONS, WebDriverWait


class Wait(WebDriverWait):
    """
    Extended WebDriverWait with customizable timeout and ignored_exceptions.
    """

    @property
    def timeout(self):
        return self._timeout

    @timeout.setter
    def timeout(self, value: int | float | None):
        if value is None:
            return
        if not isinstance(value, int | float):
            raise TypeError(f'The "timeout" must be int or float, got {type(value).__name__}')
        self._timeout = value

    @property
    def ignored_exceptions(self):
        return self._ignored_exceptions

    @ignored_exceptions.setter
    def ignored_exceptions(self, value: Type[Exception] | Iterable[Type[Exception]] | None):
        if value is None:
            self._ignored_exceptions = IGNORED_EXCEPTIONS
            return
        if isinstance(value, type) and issubclass(value, Exception):
            value = (value,)
        elif not (
            isinstance(value, Iterable)
            and all(isinstance(v, type) and issubclass(v, Exception) for v in value)
        ):
            raise TypeError(
                'The "ignored_exceptions" must be an Exception type or an iterable of Exception types, '
                f'got {type(value).__name__}.'
            )
        self._ignored_exceptions = IGNORED_EXCEPTIONS + tuple(value)
