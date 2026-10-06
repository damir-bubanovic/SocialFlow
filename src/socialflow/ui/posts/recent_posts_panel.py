from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from socialflow.application.publishing.list_recent_publications import (
    ListRecentPublications,
)
from socialflow.domain.account.account import Account
from socialflow.domain.publishing.publication import Publication
from socialflow.ui.posts.recent_posts_list import RecentPostsList


class RecentPostsPanel(QWidget):
    """Display recent publication history for an account."""

    publication_selected = Signal(Publication)

    def __init__(
        self,
        list_recent_publications: ListRecentPublications,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._list_recent_publications = list_recent_publications
        self._account: Account | None = None

        self.title = QLabel("Recent posts", self)
        self.recent_posts_list = RecentPostsList(self)

        layout = QVBoxLayout()
        layout.addWidget(self.title)
        layout.addWidget(self.recent_posts_list)

        self.setLayout(layout)

        self.recent_posts_list.itemSelectionChanged.connect(
            self._emit_selected_publication
        )

    def set_account(
        self,
        account: Account | None,
    ) -> None:
        """Display recent publications for an account."""
        self._account = account
        self.refresh()

    def refresh(self) -> None:
        """Refresh publication history for the current account."""
        if self._account is None:
            self.recent_posts_list.set_publications(())
            return

        publications = self._list_recent_publications.execute(
            self._account
        )

        self.recent_posts_list.set_publications(publications)

    def _emit_selected_publication(self) -> None:
        """Emit the publication selected in the history list."""
        publication = self.recent_posts_list.selected_publication()

        if publication is not None:
            self.publication_selected.emit(publication)