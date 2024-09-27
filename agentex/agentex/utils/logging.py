import logging
import sys
from typing import Sequence

LOG_FORMAT: str = "%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] - %(message)s"

__all__: Sequence[str] = ("make_logger", "LOG_FORMAT")


def make_logger(name: str) -> logging.Logger:
    log_level = logging.INFO

    if name is None or not isinstance(name, str) or len(name) == 0:
        raise ValueError("Name must be a non-empty string.")

    logger = logging.getLogger(name)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(stream_handler)
    logger.setLevel(log_level)

    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception
    return logger
