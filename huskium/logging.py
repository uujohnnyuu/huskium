# Author: Johnny Chou
# Email: johnny071531@gmail.com
# PyPI: https://pypi.org/project/huskium/
# GitHub: https://github.com/uujohnnyuu/huskium


import inspect
import logging
import os


# Filter
class BasePrefixFilter(logging.Filter):

    def __init__(
        self,
        prefix: str | None = None,
        lower: bool = True,
        torecord: bool = False
    ):
        """
        The base prefix filter.

        Args:
            prefix: The frame prefix.
            lower: `True` for case-insensitive; `False` for case-sensitive.
            torecord: Whether to save the `LogRecord` info.
        """
        super().__init__()
        self._prefix = prefix
        self._lower = lower
        self._torecord = torecord
        self._record: logging.LogRecord | None = None

    @property
    def prefix(self):
        return self._prefix

    @prefix.setter
    def prefix(self, value):
        if not isinstance(value, (str, type(None))):
            raise TypeError(f'"prefix" should be "str" or "None", not {type(value).__name__}')
        self._prefix = value

    @property
    def lower(self):
        return self._lower

    @lower.setter
    def lower(self, value):
        if not isinstance(value, bool):
            raise TypeError(f'"lower" should be "bool", not {type(value).__name__}')
        self._lower = value

    @property
    def torecord(self):
        return self._torecord

    @torecord.setter
    def torecord(self, value):
        if not isinstance(value, bool):
            raise TypeError(f'"torecord" should be "bool", not {type(value).__name__}')
        self._torecord = value

    @property
    def record(self):
        return self._record


class PrefixFilter(BasePrefixFilter):
    """
    Displays logs of frame whose names start with the target prefix.

    Examples:
        ::

            import logging
            from huskium import PrefixFilter

            # Create a filter object with prefix = 'test'.
            filter = PrefixFilter('test')

            # Set up logging with filter.
            logging.getLogger().addFilter(filter)

            # All logging will follow the filter logic,
            # recording logs from frames with the prefix 'test'.
            logging.info(...)

    """

    def __init__(
        self,
        prefix: str | None = None,
        lower: bool = True,
        torecord: bool = False,
        funcframe: bool = True
    ):
        """
        Args:
            prefix: The frame prefix.
            lower: `True` for case-insensitive; `False` for case-sensitive.
            isrecord: Whether to save the `LogRecord` info.
            funcframe: `True` to filter function frames;
                `False` to filter file (module) frames.
        """
        super().__init__(prefix, lower, torecord)
        self._funcframe = funcframe
        self._func = FuncPrefixFilter()
        self._file = FilePrefixFilter()

    @property
    def funcframe(self):
        return self._funcframe

    @funcframe.setter
    def funcframe(self, value):
        if not isinstance(value, bool):
            raise TypeError(f'"funcframe" should be "bool", not {type(value).__name__}')
        self._funcframe = value

    def filter(self, record):
        f = self._func if self._funcframe else self._file
        f._prefix = self._prefix
        f._lower = self._lower
        f._torecord = self._torecord
        result = f.filter(record)
        self._record = f._record
        return result


class FuncPrefixFilter(BasePrefixFilter):
    """
    Displays logs of function frame whose names start with the target prefix.

    Examples:
        ::

            import logging
            from huskium import FuncPrefixFilter

            # Create a filter object with prefix = 'test'.
            filter = FuncPrefixFilter('test')

            # Set up logging with filter.
            logging.getLogger().addFilter(filter)

            # All logging will follow the filter logic,
            # recording logs from function frames with the prefix 'test'.
            logging.info(...)

    """

    def filter(self, record):

        self._record = None

        if not self._prefix:
            return True

        prefix = self._prefix.lower() if self._lower else self._prefix
        # Do not use inspect.stack() as it is costly.
        frame = inspect.currentframe()
        while frame:
            funcname = original_funcname = frame.f_code.co_name
            if self._lower:
                funcname = funcname.lower()
            if funcname.startswith(prefix):
                record.filename = os.path.basename(frame.f_code.co_filename)
                record.lineno = frame.f_lineno
                record.funcName = original_funcname
                break
            frame = frame.f_back

        if self._torecord:
            self._record = record

        return True


class FilePrefixFilter(BasePrefixFilter):
    """
    Displays logs of file frame whose names start with the target prefix.

    Examples:
        ::

            import logging
            from huskium import FilePrefixFilter

            # Create a filter object with prefix = 'test'.
            filter = FilePrefixFilter('test')

            # Set up logging with filter.
            logging.getLogger().addFilter(filter)

            # All logging will follow the filter logic,
            # recording logs from file frames with the prefix 'test'.
            logging.info(...)

    """

    def filter(self, record):

        self._record = None

        if not self._prefix:
            return True

        prefix = self._prefix.lower() if self._lower else self._prefix
        # Do not use inspect.stack() as it is costly.
        frame = inspect.currentframe()
        while frame:
            filename = original_filename = os.path.basename(frame.f_code.co_filename)
            if self._lower:
                filename = filename.lower()
            if filename.startswith(prefix):
                record.filename = original_filename
                record.lineno = frame.f_lineno
                record.funcName = frame.f_code.co_name
                break
            frame = frame.f_back

        if self._torecord:
            self._record = record

        return True


# Adapter
class PageElementLoggerAdapter(logging.LoggerAdapter):
    """Mainly used in internal `Page` and `Element(s)` debug log adapter."""

    def __init__(self, logger, instance):
        """
        Args:
            logger: The module logger object.
            instance: The class instance in the module.
        """
        super().__init__(
            logger,
            {
                "petype": type(instance).__name__,
                "remark": getattr(instance, 'remark', 'remark')
            }
        )

    def process(self, msg, kwargs):
        return f'{self.extra["petype"]}({self.extra["remark"]}): {msg}', kwargs


class LogConfig:
    """General log configuration."""

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
