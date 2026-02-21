import time
from logging import DEBUG, Formatter, Logger, getLogger
from logging.handlers import RotatingFileHandler
from typing import Union

from restiny.consts import LOG_FILE

_logger: Union[Logger, None] = None


def _setup_logger() -> Logger:
    logger = getLogger('restiny')

    for handler in logger.handlers:
        logger.removeHandler(handler)

    formatter = Formatter(
        fmt='[%(asctime)s][%(levelname)s]: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S %z',
    )
    formatter.converter = time.gmtime
    file_handler = RotatingFileHandler(
        filename=LOG_FILE,
        encoding='utf-8',
        maxBytes=5_000_000,  # 5MB
        backupCount=1,
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.setLevel(DEBUG)

    return logger


def get_logger() -> Logger:
    global _logger
    if _logger:
        return _logger

    _logger = _setup_logger()
    return _logger
