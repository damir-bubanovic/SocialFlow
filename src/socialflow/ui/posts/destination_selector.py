from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QWidget

from socialflow.domain.publishing.destination import PublishingDestination


class DestinationSelector(QWidget):
    """Controls for selecting publishing destinations."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.facebook = self._create_checkbox(
            PublishingDestination.FACEBOOK
        )
        self.instagram = self._create_checkbox(
            PublishingDestination.INSTAGRAM
        )
        self.wordpress = self._create_checkbox(
            PublishingDestination.WORDPRESS
        )

        layout = QHBoxLayout()
        layout.addWidget(self.facebook)
        layout.addWidget(self.instagram)
        layout.addWidget(self.wordpress)
        layout.addStretch()

        self.setLayout(layout)

    def selected_destinations(
        self,
    ) -> tuple[PublishingDestination, ...]:
        """Return the selected publishing destinations."""
        destinations: list[PublishingDestination] = []

        if self.facebook.isChecked():
            destinations.append(PublishingDestination.FACEBOOK)

        if self.instagram.isChecked():
            destinations.append(PublishingDestination.INSTAGRAM)

        if self.wordpress.isChecked():
            destinations.append(PublishingDestination.WORDPRESS)

        return tuple(destinations)

    def _create_checkbox(
        self,
        destination: PublishingDestination,
    ) -> QCheckBox:
        """Create a checkbox for a publishing destination."""
        checkbox = QCheckBox(destination.display_name, self)
        return checkbox