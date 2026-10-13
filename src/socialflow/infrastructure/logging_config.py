import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


LOGGER_NAME = "socialflow"
LOG_FILENAME = "socialflow.log"

MAX_LOG_SIZE = 2 * 1024 * 1024
BACKUP_COUNT = 3


def configure_logging(log_directory: Path) -> Path:
    """Configure rotating application logs without duplicate handlers."""
    log_directory.mkdir(parents=True, exist_ok=True)
    log_file = log_directory / LOG_FILENAME

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)

    for handler in logger.handlers[:]:
        if not isinstance(handler, RotatingFileHandler):
            continue

        if Path(handler.baseFilename) == log_file.resolve():
            _remove_fallback_handlers(logger)
            return log_file

        logger.removeHandler(handler)
        handler.close()

    handler = RotatingFileHandler(
        log_file,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )

    handler.setLevel(logging.INFO)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)s | "
            "%(name)s | %(message)s"
        )
    )

    logger.addHandler(handler)
    _remove_fallback_handlers(logger)

    return log_file

def _remove_fallback_handlers(logger: logging.Logger) -> None:
    """Remove terminal fallback handlers after file logging recovers."""
    for handler in logger.handlers[:]:
        if not getattr(handler, "_socialflow_fallback", False):
            continue

        logger.removeHandler(handler)
        handler.close()

def configure_fallback_logging() -> None:
    """Configure terminal logging when persistent logging fails."""
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)

    for handler in logger.handlers:
        if getattr(handler, "_socialflow_fallback", False):
            return

    handler = logging.StreamHandler()
    handler._socialflow_fallback = True
    handler.setLevel(logging.WARNING)
    handler.setFormatter(
        logging.Formatter(
            "%(levelname)s | %(name)s | %(message)s"
        )
    )

    logger.addHandler(handler)