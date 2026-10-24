
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from socialflow.domain.post.remote_media import RemoteMedia


class RemoteMediaSelectionDialog(QDialog):
    """Select an existing image from a remote media library."""

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._media: tuple[RemoteMedia, ...] = ()

        self.setWindowTitle("Select WordPress featured image")
        self.resize(540, 420)

        self.status_label = QLabel(self)
        self.media_list = QListWidget(self)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel,
            self,
        )

        self.select_button = self.button_box.button(
            QDialogButtonBox.StandardButton.Ok
        )
        self.select_button.setText("Use selected image")
        self.select_button.setEnabled(False)

        layout = QVBoxLayout(self)
        layout.addWidget(self.status_label)
        layout.addWidget(self.media_list)
        layout.addWidget(self.button_box)

        self.media_list.currentRowChanged.connect(
            self._update_selection
        )
        self.media_list.itemDoubleClicked.connect(
            self._accept_selected
        )
        self.button_box.accepted.connect(
            self._accept_selected
        )
        self.button_box.rejected.connect(self.reject)

        self.show_empty()

    def _clear_media(self) -> None:
        """Clear existing media and disable selection."""
        self._media = ()
        self.media_list.clear()
        self.media_list.setEnabled(False)
        self.select_button.setEnabled(False)

    def show_loading(self) -> None:
        """Display the loading state."""
        self._clear_media()
        self.status_label.setText(
            "Loading WordPress media library..."
        )

    def show_media(
        self,
        media: tuple[RemoteMedia, ...],
    ) -> None:
        """Display available images without selecting one."""
        self._clear_media()
        self._media = media

        for item in media:
            title = item.title.strip() or "Untitled image"
            list_item = QListWidgetItem(
                f"{title} (ID {item.remote_id})"
            )
            list_item.setData(
                Qt.ItemDataRole.UserRole,
                item.remote_id,
            )
            list_item.setToolTip(item.source_url)
            self.media_list.addItem(list_item)

        self.media_list.setEnabled(bool(media))
        self.status_label.setText(
            f"{len(media)} images available."
            if media
            else "No WordPress images found."
        )

    def show_error(self, message: str) -> None:
        """Display a retrieval failure."""
        self._clear_media()
        self.status_label.setText(
            f"Unable to load WordPress media: {message}"
        )

    def show_empty(self) -> None:
        """Reset the dialog to its initial state."""
        self._clear_media()
        self.status_label.setText(
            "Choose an image from the WordPress Media Library."
        )

    def selected_media(self) -> RemoteMedia | None:
        """Return the selected media, if any."""
        row = self.media_list.currentRow()

        if not 0 <= row < len(self._media):
            return None

        return self._media[row]

    def selected_media_id(self) -> int | None:
        """Return the selected WordPress media ID."""
        media = self.selected_media()
        return media.remote_id if media is not None else None

    def _update_selection(self, row: int) -> None:
        """Enable confirmation only for a valid selection."""
        self.select_button.setEnabled(
            self.media_list.isEnabled()
            and 0 <= row < len(self._media)
        )

    def _accept_selected(self, *_args: object) -> None:
        """Accept the dialog only when an image is selected."""
        if self.selected_media() is not None:
            self.accept()
