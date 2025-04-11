# Author: Johnny Chou
# Email: johnny071531@gmail.com
# PyPI: https://pypi.org/project/huskium/
# GitHub: https://github.com/uujohnnyuu/huskium


from __future__ import annotations

from typing import TypeAlias
from typing_extensions import TypeVar

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement


WD = TypeVar('WD', bound=WebDriver, default=WebDriver)
WE = TypeVar('WE', bound=WebElement, default=WebElement)

TupleCoordinate: TypeAlias = tuple[int, int, int, int] | tuple[float, float, float, float]
Coordinate: TypeAlias = TupleCoordinate | dict[str, int] | dict[str, float]
