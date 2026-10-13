import logging
from logging.handlers import RotatingFileHandler

from socialflow.infrastructure.logging_config import (
    configure_fallback_logging,
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

def test_fallback_logging_avoids_duplicate_stream_handlers(
    capsys,
) -> None:
    """Repeated fallback configuration must not duplicate warnings."""
    logger = logging.getLogger("socialflow")

    original_handlers = logger.handlers[:]
    original_level = logger.level

    try:
        logger.handlers = []

        configure_fallback_logging()
        configure_fallback_logging()

        logger.warning("Fallback diagnostic test")

        captured = capsys.readouterr()

        assert captured.err.count("Fallback diagnostic test") == 1

    finally:
        for handler in logger.handlers[:]:
            if handler not in original_handlers:
                logger.removeHandler(handler)
                handler.close()

        logger.handlers = original_handlers
        logger.setLevel(original_level)

def test_file_logging_removes_fallback_handler(
    tmp_path,
) -> None:
    """Successful file logging removes the temporary terminal fallback."""
    logger = logging.getLogger("socialflow")

    original_handlers = logger.handlers[:]
    original_level = logger.level

    try:
        logger.handlers = []

        configure_fallback_logging()

        fallback_handlers = [
            handler
            for handler in logger.handlers
            if getattr(handler, "_socialflow_fallback", False)
        ]

        assert len(fallback_handlers) == 1

        log_file = configure_logging(tmp_path / "logs")

        assert log_file.is_file()

        assert not any(
            getattr(handler, "_socialflow_fallback", False)
            for handler in logger.handlers
        )

        assert any(
            isinstance(handler, RotatingFileHandler)
            for handler in logger.handlers
        )

    finally:
        for handler in logger.handlers[:]:
            if handler not in original_handlers:
                logger.removeHandler(handler)
                handler.close()

        logger.handlers = original_handlers
        logger.setLevel(original_level)

def test_fallback_logging_preserves_external_stream_handlers() -> None:
    """Fallback logging must not replace external logging handlers."""
    logger = logging.getLogger("socialflow")

    original_handlers = logger.handlers[:]
    original_level = logger.level

    try:
        logger.handlers = []

        external_handler = logging.StreamHandler()
        logger.addHandler(external_handler)

        configure_fallback_logging()
        configure_fallback_logging()

        fallback_handlers = [
            handler
            for handler in logger.handlers
            if getattr(handler, "_socialflow_fallback", False)
        ]

        assert len(fallback_handlers) == 1
        assert external_handler in logger.handlers

    finally:
        for handler in logger.handlers[:]:
            if handler not in original_handlers:
                logger.removeHandler(handler)
                handler.close()

        logger.handlers = original_handlers
        logger.setLevel(original_level)