# Author: Johnny Chou
# Email: johnny071531@gmail.com
# PyPI: https://pypi.org/project/huskium/
# GitHub: https://github.com/uujohnnyuu/huskium


from __future__ import annotations

from functools import wraps

from .selenium import GenericElement, GenericElements


def dynamic(func):
    """
    Dynamic element decorator for page objects.
    Applies to any dynamic elements that return an `Element` or `Elements`.

    Examples:
        ::

            from huskium import dynamic

            @dynamic
            def my_element(self, par):
                return Element(By.IOS_PREDICATE, 'name CONTAINS "{par}"')

            # You can NOT set the dynamic element without the dynamic decorator,
            # as it will not trigger the descriptor. The following is incorrect:
            def my_element(self, par):
                return Element(By.IOS_PREDICATE, 'name CONTAINS "{par}"')

    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        target = func(self, *args, **kwargs)
        if isinstance(target, GenericElement | GenericElements):
            return target.__get__(self, type(self))
        raise TypeError(
            f'The decorated function "{func.__name__}" must returns an Element or Elements object.'
        )

    return wrapper
