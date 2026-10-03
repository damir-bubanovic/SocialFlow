import sys

from PySide6.QtWidgets import QApplication

from socialflow.ui.main_window import MainWindow
from socialflow.constants import APP_NAME, APP_ORGANIZATION


def create_application() -> MainWindow:
    """Create the main SocialFlow application window."""
    application = QApplication.instance()

    if application is None:
        application = QApplication(sys.argv)

    application.setApplicationName(APP_NAME)
    application.setOrganizationName(APP_ORGANIZATION)

    return MainWindow()

def run(*, start_event_loop: bool = True) -> int:
    """Start the SocialFlow desktop application."""
    window = create_application()
    window.show()

    if not start_event_loop:
        return 0

    application = QApplication.instance()

    if application is None:
        return 1

    return application.exec()