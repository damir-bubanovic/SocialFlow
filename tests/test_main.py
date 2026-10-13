import pytest
import logging
from PySide6.QtWidgets import QApplication

from socialflow.main import create_application, run
from socialflow.ui.main_window import MainWindow


def test_create_application_creates_main_window(qtbot) -> None:
    application = QApplication.instance()

    window = create_application()

    qtbot.addWidget(window)

    assert application is not None
    assert application.applicationName() == "SocialFlow"
    assert application.organizationName() == "SocialFlow"
    assert isinstance(window, MainWindow)

def test_create_application_configures_logging(
    monkeypatch,
    tmp_path,
    qtbot,
) -> None:
    """Initialize logging in the application data directory."""
    from socialflow.infrastructure.logging_config import LOG_FILENAME

    monkeypatch.setattr(
        "socialflow.main.data_directory",
        lambda: tmp_path,
    )

    window = create_application()
    qtbot.addWidget(window)

    log_file = tmp_path / "logs" / LOG_FILENAME

    assert log_file.is_file()

def test_run_shows_main_window(monkeypatch, qtbot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)

    monkeypatch.setattr(
        "socialflow.main.create_application",
        lambda: window,
    )

    exit_code = run(start_event_loop=False)

    assert window.isVisible()
    assert exit_code == 0

def test_create_application_continues_when_logging_fails(
    monkeypatch,
    qtbot,
) -> None:
    """A logging filesystem error must not prevent startup."""

    def failing_logging_configuration(_log_directory):
        raise PermissionError("Access denied to log directory")

    monkeypatch.setattr(
        "socialflow.main.configure_logging",
        failing_logging_configuration,
    )

    window = create_application()
    qtbot.addWidget(window)

    assert isinstance(window, MainWindow)

def test_create_application_propagates_main_window_failure(
    monkeypatch,
    tmp_path,
    caplog,
) -> None:
    """Main window failures propagate without duplicate logging."""

    def failing_main_window():
        raise RuntimeError("Sensitive initialization details")

    monkeypatch.setattr(
        "socialflow.main.data_directory",
        lambda: tmp_path,
    )

    monkeypatch.setattr(
        "socialflow.main.MainWindow",
        failing_main_window,
    )

    with caplog.at_level(logging.ERROR, logger="socialflow"):
        with pytest.raises(RuntimeError):
            create_application()

    assert not [
        record
        for record in caplog.records
        if record.name == "socialflow"
        and record.levelno >= logging.ERROR
    ]

def test_run_returns_nonzero_when_application_creation_fails(
    monkeypatch,
    caplog,
) -> None:
    """Application creation failure must produce a nonzero exit code."""

    def failing_create_application():
        raise RuntimeError("Sensitive startup details")

    monkeypatch.setattr(
        "socialflow.main.create_application",
        failing_create_application,
    )

    with caplog.at_level(logging.ERROR, logger="socialflow"):
        exit_code = run(start_event_loop=False)

    assert exit_code == 1
    assert "Application startup failed: RuntimeError" in caplog.text
    assert "Sensitive startup details" not in caplog.text

def test_run_logs_main_window_failure_exactly_once(
    monkeypatch,
    tmp_path,
    caplog,
) -> None:
    """Main window initialization failure produces one sanitized error."""

    def failing_main_window():
        raise RuntimeError("Sensitive initialization details")

    monkeypatch.setattr(
        "socialflow.main.data_directory",
        lambda: tmp_path,
    )

    monkeypatch.setattr(
        "socialflow.main.MainWindow",
        failing_main_window,
    )

    with caplog.at_level(logging.ERROR, logger="socialflow"):
        exit_code = run(start_event_loop=False)

    error_records = [
        record
        for record in caplog.records
        if record.name == "socialflow"
        and record.levelno >= logging.ERROR
    ]

    assert exit_code == 1
    assert len(error_records) == 1
    assert (
        error_records[0].getMessage()
        == "Application startup failed: RuntimeError"
    )
    assert "Sensitive initialization details" not in caplog.text

def test_run_returns_nonzero_when_window_show_fails(
    monkeypatch,
    caplog,
) -> None:
    """Window display failure must produce a nonzero exit code."""

    class FailingWindow:
        def show(self):
            raise RuntimeError("Sensitive display details")

        def close(self):
            pass

    monkeypatch.setattr(
        "socialflow.main.create_application",
        FailingWindow,
    )

    with caplog.at_level(logging.ERROR, logger="socialflow"):
        exit_code = run(start_event_loop=False)

    assert exit_code == 1
    assert "Application startup failed: RuntimeError" in caplog.text
    assert "Sensitive display details" not in caplog.text

def test_run_closes_window_when_show_fails(
    monkeypatch,
    caplog,
) -> None:
    """Close an initialized window if displaying it fails."""

    class FailingWindow:
        def __init__(self):
            self.close_called = False

        def show(self):
            raise RuntimeError("Sensitive display details")

        def close(self):
            self.close_called = True

    window = FailingWindow()

    monkeypatch.setattr(
        "socialflow.main.create_application",
        lambda: window,
    )

    with caplog.at_level(logging.ERROR, logger="socialflow"):
        exit_code = run(start_event_loop=False)

    assert exit_code == 1
    assert window.close_called
    assert "Application startup failed: RuntimeError" in caplog.text
    assert "Sensitive display details" not in caplog.text

def test_run_handles_window_cleanup_failure(
    monkeypatch,
    caplog,
) -> None:
    """Cleanup failure must not mask the original startup failure."""

    class FailingWindow:
        def show(self):
            raise RuntimeError("Sensitive display details")

        def close(self):
            raise RuntimeError("Sensitive cleanup details")

    monkeypatch.setattr(
        "socialflow.main.create_application",
        FailingWindow,
    )

    with caplog.at_level(logging.WARNING, logger="socialflow"):
        exit_code = run(start_event_loop=False)

    assert exit_code == 1

    messages = [
        record.getMessage()
        for record in caplog.records
        if record.name == "socialflow"
    ]

    assert messages.count("Startup window cleanup failed.") == 1
    assert messages.count("Application startup failed: RuntimeError") == 1

    assert "Sensitive display details" not in caplog.text
    assert "Sensitive cleanup details" not in caplog.text