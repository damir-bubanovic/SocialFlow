import logging
from logging.handlers import RotatingFileHandler

from socialflow.infrastructure.logging_config import (
    configure_logging,
)


def test_configure_logging_creates_log_file(tmp_path) -> None:
    log_directory = tmp_path / "logs"

    log_file = configure_logging(log_directory)

    assert log_directory.is_dir()
    assert log_file.exists()


def test_configure_logging_writes_application_errors(tmp_path) -> None:
    log_file = configure_logging(tmp_path / "logs")

    logger = logging.getLogger(
        "socialflow.application.publishing.publish_post"
    )

    logger.error("Publishing failed: ConnectionError")

    for handler in logging.getLogger("socialflow").handlers:
        handler.flush()

    content = log_file.read_text(encoding="utf-8")

    assert "Publishing failed: ConnectionError" in content


def test_configure_logging_avoids_duplicate_handlers(tmp_path) -> None:
    log_directory = tmp_path / "logs"

    configure_logging(log_directory)
    configure_logging(log_directory)

    logger = logging.getLogger("socialflow")

    matching_handlers = [
        handler
        for handler in logger.handlers
        if isinstance(handler, RotatingFileHandler)
        and handler.baseFilename == str(
            (log_directory / "socialflow.log").resolve()
        )
    ]

    assert len(matching_handlers) == 1

def test_configure_logging_replaces_handler_when_directory_changes(
    tmp_path,
) -> None:
    """Switching log directories must close the previous file handler."""
    first_directory = tmp_path / "first" / "logs"
    second_directory = tmp_path / "second" / "logs"

    first_log = configure_logging(first_directory)

    logger = logging.getLogger("socialflow")

    first_handler = next(
        handler
        for handler in logger.handlers
        if isinstance(handler, RotatingFileHandler)
        and handler.baseFilename == str(first_log.resolve())
    )

    second_log = configure_logging(second_directory)

    active_handlers = [
        handler
        for handler in logger.handlers
        if isinstance(handler, RotatingFileHandler)
    ]

    assert len(active_handlers) == 1
    assert active_handlers[0].baseFilename == str(
        second_log.resolve()
    )

    assert first_handler not in logger.handlers
    assert first_handler.stream is None