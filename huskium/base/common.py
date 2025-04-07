# Author: Johnny Chou
# Email: johnny071531@gmail.com
# PyPI: https://pypi.org/project/huskium/
# GitHub: https://github.com/uujohnnyuu/huskium


class _Name:
    _page = '_page'
    _present_cache = '_present_cache'
    _visible_cache = '_visible_cache'
    _clickable_cache = '_clickable_cache'
    _select_cache = '_select_cache'
    _caches = [_present_cache, _visible_cache, _clickable_cache, _select_cache]


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
