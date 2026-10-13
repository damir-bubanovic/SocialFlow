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

    return log_file