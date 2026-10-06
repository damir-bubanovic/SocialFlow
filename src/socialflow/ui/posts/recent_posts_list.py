from PySide6.QtWidgets import QListWidget, QListWidgetItem

from socialflow.domain.publishing.publication import Publication


class RecentPostsList(QListWidget):
    """Display recent publication history."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._publications: tuple[Publication, ...] = ()

    def set_publications(
        self,
        publications: tuple[Publication, ...],
    ) -> None:
        """Replace the displayed publication history."""
        self.clear()
        self._publications = publications

        for publication in publications:
            item = QListWidgetItem(
                self._format_publication(publication)
            )
            self.addItem(item)

    def selected_publication(self) -> Publication | None:
        """Return the currently selected publication."""
        row = self.currentRow()

        if row < 0 or row >= len(self._publications):
            return None

        return self._publications[row]

    @staticmethod
    def _format_publication(publication: Publication) -> str:
        """Return display text for a publication."""
        published_at = publication.published_at.strftime(
            "%d %b %Y %H:%M"
        )

        destination = publication.account.destination.value.title()

        return (
            f"{published_at} · {destination}\n"
            f"{publication.account.name} — {publication.post.text}"
        )