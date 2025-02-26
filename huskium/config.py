# Author: Johnny Chou
# Email: johnny071531@gmail.com
# PyPI: https://pypi.org/project/huskium/
# GitHub: https://github.com/uujohnnyuu/huskium


from __future__ import annotations

import logging

from .logging import PrefixFilter


class Log:
    """General log settings."""

    # prefix filter object
    PREFIX_FILTER = PrefixFilter('test')
    """
    Internal debug logging filter.

    Examples:
        ::

            from huskium import Log

            # Finds frames with the prefix "run".
            Log.PREFIX_FILTER.prefix = 'run'

            # Makes the prefix "run" case-sensitive.
            Log.PREFIX_FILTER.lower = False

            # Finds the file (module) frame using the prefix "run".
            Log.PREFIX_FILTER.funcframe = False

    """

    # Deprecation of logstack
    _PREFIX = 'test'
    _LOWER = True

    # basicConfig
    FILENAME = './log.log'
    FILEMODE = 'w'
    FORMAT = '%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d | %(funcName)s | %(message)s'
    DATEFMT = '%Y-%m-%d %H:%M:%S'
    LEVEL = logging.DEBUG
    BASIC_CONFIG = {
        "filename": FILENAME,
        "filemode": FILEMODE,
        "format": FORMAT,
        "datefmt": DATEFMT,
        "level": LEVEL
    }


class Cache:
    """General cache settings."""

    ELEMENT: bool = True
    """`True` (default) to enable cache in `Element`."""


class Appium:
    """General settings for Appium."""

    LOCALHOST: str = 'http://127.0.0.1'
    PORT_4723: str = ':4723'
    WD_HUB: str = '/wd/hub'


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
