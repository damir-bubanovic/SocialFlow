from PySide6.QtWidgets import QMainWindow

from socialflow.ui.main_content import MainContent

from socialflow.constants import (
    APP_NAME,
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_WINDOW_WIDTH,
)


class MainWindow(QMainWindow):
    """Main application window for SocialFlow."""

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle(APP_NAME)
        self.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        self.setCentralWidget(MainContent(self))