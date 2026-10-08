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
        self.missing_images_warning = QLabel(self)
        self.missing_images_warning.setWordWrap(True)
        self.missing_images_warning.setStyleSheet("color: #b45309;")
        self.missing_images_warning.hide()

        layout = QVBoxLayout()
        layout.addWidget(self.title)
        layout.addWidget(self.recent_posts_list)
        layout.addWidget(self.missing_images_warning)

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
        self.missing_images_warning.clear()
        self.missing_images_warning.hide()

        if self._account is None:
            self.recent_posts_list.set_publications(())
            return

        publications = self._list_recent_publications.execute(
            self._account
        )

        self.recent_posts_list.set_publications(publications)

    def _emit_selected_publication(self) -> None:
        """Emit the selected publication and update image warnings."""
        publication = self.recent_posts_list.selected_publication()

        self.missing_images_warning.clear()
        self.missing_images_warning.hide()

        if publication is None:
            return

        missing_images = (
            self._list_recent_publications.missing_images_for_publication(
                publication.id
            )
        )

        if missing_images:
            count = len(missing_images)
            image_word = "image" if count == 1 else "images"

            self.missing_images_warning.setText(
                f"Warning: {count} missing {image_word} "
                "for this publication."
            )
            self.missing_images_warning.show()

        self.publication_selected.emit(publication)