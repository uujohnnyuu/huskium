# Author: Johnny Chou
# Email: johnny071531@gmail.com
# PyPI: https://pypi.org/project/huskium/
# GitHub: https://github.com/uujohnnyuu/huskium


class NoSuchCacheException(Exception):
    """
    Typically used internally in Element.
    If no cache exists, this exception is raised to trigger element relocation.
    """

    def __init__(self, message: str = 'No cache available, please relocate the element in except.'):
        self.message = message
        super().__init__(message)
