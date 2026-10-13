import sys
import logging
from PySide6.QtWidgets import QApplication

from socialflow.infrastructure.logging_config import configure_logging
from socialflow.infrastructure.storage.data_directory import data_directory
from socialflow.ui.main_window import MainWindow
from socialflow.constants import APP_NAME, APP_ORGANIZATION


def create_application() -> MainWindow:
    """Create the main SocialFlow application window."""
    application = QApplication.instance()

    if application is None:
        application = QApplication(sys.argv)

    application.setApplicationName(APP_NAME)
    application.setOrganizationName(APP_ORGANIZATION)

    try:
        configure_logging(data_directory() / "logs")
    except OSError:
        logging.getLogger("socialflow").warning(
            "Persistent logging is unavailable."
        )

    try:
        return MainWindow()
    except Exception as error:
        logging.getLogger("socialflow").error(
            "Main window initialization failed: %s",
            type(error).__name__,
        )
        raise

def run(*, start_event_loop: bool = True) -> int:
    """Start the SocialFlow desktop application."""
    try:
        window = create_application()
        window.show()
    except Exception as error:
        logging.getLogger("socialflow").error(
            "Application startup failed: %s",
            type(error).__name__,
        )
        return 1

    if not start_event_loop:
        return 0

    application = QApplication.instance()

    if application is None:
        return 1

    return application.exec()