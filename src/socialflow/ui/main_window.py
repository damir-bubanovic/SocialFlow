from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QMainWindow

from socialflow.constants import (
    APP_NAME,
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_WINDOW_WIDTH,
)
from socialflow.ui.main_content import MainContent


class MainWindow(QMainWindow):
    """Main application window for SocialFlow."""

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle(APP_NAME)
        self.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)

        self.main_content = MainContent(self)
        self.setCentralWidget(self.main_content)

        self._close_pending = False

        self.main_content.accounts_page.verification_finished.connect(
            self._finish_pending_close
        )
        self.main_content.posts_page.publishing_finished.connect(
            self._finish_pending_close
        )


    def closeEvent(self, event: QCloseEvent) -> None:
        """Defer closing until background operations finish."""
        main_content = getattr(self, "main_content", None)

        if main_content is None:
            super().closeEvent(event)
            return

        accounts_page = getattr(main_content, "accounts_page", None)
        posts_page = getattr(main_content, "posts_page", None)

        if accounts_page is None or posts_page is None:
            super().closeEvent(event)
            return

        if (
            accounts_page.verification_is_running
            or posts_page.publishing_is_running
        ):
            self._close_pending = True
            event.ignore()
            return

        self._close_pending = False
        accounts_page.shutdown()
        posts_page.shutdown()
        super().closeEvent(event)

    def _finish_pending_close(self) -> None:
        """Close when all background operations have finished."""
        if not self._close_pending:
            return

        if (
            self.main_content.accounts_page.verification_is_running
            or self.main_content.posts_page.publishing_is_running
        ):
            return

        self.close()
