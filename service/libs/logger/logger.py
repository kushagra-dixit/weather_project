import logging
import sys

# Sets the logging level for all the logger of the module
LOG_LEVEL = logging.INFO


class CustomFormatter(logging.Formatter):
    """
    Modify the way logging messages are displayed according to the logging level
    """

    error_format = (
        "%(asctime)s — %(name)s — %(levelname)s "
        "— %(funcName)s:%(lineno)d — %(message)s"
    )
    debug_format = (
        "%(asctime)s — %(name)s — %(levelname)s "
        "— %(funcName)s:%(lineno)d — %(message)s"
    )
    info_format = "%(asctime)s — %(name)s — %(levelname)s — %(message)s"

    def __init__(self) -> None:
        super().__init__(
            fmt="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            style="%",
        )

    # We are overriding a python builtin to customize our formatter.
    # Thus we need to disable a flake8 rule.
    def format(self, record):  # noqa

        # Save the original format configured by the user
        # when the logger formatter was instantiated
        format_orig = self._style._fmt

        if record.levelno == logging.DEBUG:
            self._style._fmt = CustomFormatter.debug_format

        elif record.levelno == logging.INFO:
            self._style._fmt = CustomFormatter.info_format

        elif record.levelno > logging.INFO:
            self._style._fmt = CustomFormatter.error_format

        # Call the original formatter class to do the grunt work
        result = logging.Formatter.format(self, record)

        # Restore the original format configured by the user
        self._style._fmt = format_orig

        return result


class Logger:
    def __new__(cls, name):
        logger = super(Logger, cls).__new__(cls)
        logger = logging.getLogger(name)
        Logger.initialize_logger_format(logger)
        return logger

    @staticmethod
    def initialize_logger_format(logger):
        formatter = CustomFormatter()

        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(LOG_LEVEL)
