# Author: Johnny Chou
# Email: johnny071531@gmail.com
# PyPI: https://pypi.org/project/huskium/
# GitHub: https://github.com/uujohnnyuu/huskium


import inspect
import logging
import os


# Filter
class PrefixFilter(logging.Filter):
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
        funcframe: bool = True,
        isrecord: bool = False
    ):
        """
        Args:
            prefix: The frame prefix.
            lower: `True` for case-insensitive; `False` for case-sensitive.
            funcframe: `True` to filter function frames;
                `False` to filter file (module) frames.
            isrecord: Whether to save the `LogRecord` info.
        """
        super().__init__()
        self.prefix = prefix
        self.lower = lower
        self.funcframe = funcframe
        self.isrecord = isrecord
        self.record: logging.LogRecord | None = None
        self._func = FuncPrefixFilter()
        self._file = FilePrefixFilter()

    def filter(self, record):
        f = self._func if self.funcframe else self._file
        f.prefix = self.prefix
        f.lower = self.lower
        f.isrecord = self.isrecord
        result = f.filter(record)
        self.record = f.record
        return result


class FuncPrefixFilter(logging.Filter):
    """
    Displays logs of function frame whose names start with the target prefix.
    """

    def __init__(
        self,
        prefix: str | None = None,
        lower: bool = True,
        isrecord: bool = False
    ):
        """
        Args:
            prefix: The frame prefix.
            lower: `True` for case-insensitive; `False` for case-sensitive.
            isrecord: Whether to save the `LogRecord` info.

        Examples:
            ::

                logger = logging.getLogger()
                filter = FuncPrefixFilter('test', isrecord=True)
                logger.addFilter(filter)

                # If isrecord=True, you can access the record object's
                # attributes directly after calling the log.
                logger.info('some message')
                funcname = filter.record.funcName
                assert some_condition, funcname

        """
        super().__init__()
        self.prefix = prefix
        self.lower = lower
        self.isrecord = isrecord
        self.record: logging.LogRecord | None = None

    def filter(self, record):
        self.record = None
        if self.prefix:
            prefix = self.prefix.lower() if self.lower else self.prefix
            # Do not use inspect.stack() as it is costly.
            frame = inspect.currentframe()
            while frame:
                funcname = original_funcname = frame.f_code.co_name
                if self.lower:
                    funcname = funcname.lower()
                if funcname.startswith(prefix):
                    record.filename = os.path.basename(frame.f_code.co_filename)
                    record.lineno = frame.f_lineno
                    record.funcName = original_funcname
                    break
                frame = frame.f_back
        if self.isrecord:
            self.record = record
        return True


class FilePrefixFilter(logging.Filter):
    """
    Displays logs of file frame whose names start with the target prefix.
    """

    def __init__(
        self,
        prefix: str | None = None,
        lower: bool = True,
        isrecord: bool = False
    ):
        """
        Args:
            prefix: The frame prefix.
            lower: `True` for case-insensitive; `False` for case-sensitive.
            isrecord: Whether to save the `LogRecord` info.
        """
        super().__init__()
        self.prefix = prefix
        self.lower = lower
        self.isrecord = isrecord
        self.record: logging.LogRecord | None = None

    def filter(self, record):
        self.record = None
        if self.prefix:
            prefix = self.prefix.lower() if self.lower else self.prefix
            # Do not use inspect.stack() as it is costly.
            frame = inspect.currentframe()
            while frame:
                filename = original_filename = os.path.basename(frame.f_code.co_filename)
                if self.lower:
                    filename = filename.lower()
                if filename.startswith(prefix):
                    record.filename = original_filename
                    record.lineno = frame.f_lineno
                    record.funcName = frame.f_code.co_name
                    break
                frame = frame.f_back
        if self.isrecord:
            self.record = record
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