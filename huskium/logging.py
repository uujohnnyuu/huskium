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
        islower: bool = True,
        torecord: bool = False
    ):
        """
        Args:
            prefix: The frame prefix.
            islower: `True` for case-insensitive; `False` for case-sensitive.
            torecord: Whether to save the `LogRecord` info.
        """
        super().__init__()
        self._set_prefix(prefix)
        self._set_islower(islower)
        self._set_torecord(torecord)
        self._record: logging.LogRecord | None = None

    @staticmethod
    def _verify(name, value, instance):
        if not isinstance(value, instance):
            raise TypeError(f'"{name}" must be "{instance}", not {type(value).__name__}')

    def _set_prefix(self, value: str | None):
        self._verify('prefix', value, (str, type(None)))
        self._prefix = value

    @property
    def prefix(self):
        return self._prefix

    def _set_islower(self, value: bool):
        self._verify('islower', value, bool)
        self._islower = value

    @property
    def islower(self):
        return self._islower

    def _set_torecord(self, value: bool):
        self._verify('torecord', value, bool)
        self._torecord = value

    @property
    def torecord(self):
        return self._torecord

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
        islower: bool = True,
        isfunc: bool = True,
        torecord: bool = False
    ):
        """
        Args:
            prefix: The frame prefix.
            islower: `True` for case-insensitive; `False` for case-sensitive.
            isfunc: `True` to filter function frames;
                `False` to filter file (module) frames.
            torecord: Whether to save the `LogRecord` info.
        """
        super().__init__(prefix, islower, torecord)
        self._set_isfunc(isfunc)
        self._set_prefixfilter()

    def _set_isfunc(self, value):
        self._verify('isfunc', value, bool)
        self._isfunc = value

    @property
    def isfunc(self):
        return self._isfunc

    def _set_prefixfilter(self):
        if self._isfunc:
            self._prefixfilter = FuncPrefixFilter(self._prefix, self._islower, self._torecord)
        else:
            self._prefixfilter = FilePrefixFilter(self._prefix, self._islower, self._torecord)

    @property
    def prefixfilter(self):
        return self._prefixfilter

    def reset(
        self,
        prefix: str | None = None,
        islower: bool = True,
        isfunc: bool = True,
        torecord: bool = False
    ):
        """Reset all filter settings."""
        self._set_prefix(prefix)
        self._set_islower(islower)
        self._set_isfunc(isfunc)
        self._set_torecord(torecord)
        self._set_prefixfilter()

    def reset_prefix(self, value: str | None):
        self._set_prefix(value)
        self._set_prefixfilter()

    def reset_islower(self, value: bool):
        self._set_islower(value)
        self._set_prefixfilter()

    def reset_isfunc(self, value: bool):
        self._set_isfunc(value)
        self._set_prefixfilter()

    def reset_torecord(self, value: bool):
        self._set_torecord(value)
        self._set_prefixfilter()

    def filter(self, record):
        self._prefixfilter.filter(record)
        self._record = self._prefixfilter._record
        return True


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
        if self._prefix:
            prefix = self._prefix.lower() if self._islower else self._prefix
            # Do not use inspect.stack() as it is costly.
            frame = inspect.currentframe()
            while frame:
                funcname = original_funcname = frame.f_code.co_name
                if self._islower:
                    funcname = funcname.lower()
                if funcname.startswith(prefix):
                    record.filename = os.path.basename(frame.f_code.co_filename)
                    record.lineno = frame.f_lineno
                    record.funcName = original_funcname
                    break
                frame = frame.f_back
        self._record = record if self._torecord else None
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
        if self._prefix:
            prefix = self._prefix.lower() if self._islower else self._prefix
            # Do not use inspect.stack() as it is costly.
            frame = inspect.currentframe()
            while frame:
                filename = original_filename = os.path.basename(frame.f_code.co_filename)
                if self._islower:
                    filename = filename.lower()
                if filename.startswith(prefix):
                    record.filename = original_filename
                    record.lineno = frame.f_lineno
                    record.funcName = frame.f_code.co_name
                    break
                frame = frame.f_back
        self._record = record if self._torecord else None
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
    """Using `PREFIX_FILTER.reset_()` to reset the internal debug log config."""

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
