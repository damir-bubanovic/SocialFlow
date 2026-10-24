from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QPixmap
from PySide6.QtNetwork import (
    QNetworkAccessManager,
    QNetworkReply,
    QNetworkRequest,
)

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
        self._network_manager = QNetworkAccessManager(self)
        self._thumbnail_reply: QNetworkReply | None = None
        self._thumbnail_request_id = 0

        self.setWindowTitle("Select WordPress featured image")
        self.resize(540, 420)

        self.status_label = QLabel(self)
        self.media_list = QListWidget(self)

        self.details_label = QLabel(self)
        self.details_label.setWordWrap(True)
        self.details_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.preview_label = QLabel("No preview available.", self)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumHeight(160)
        self.preview_label.setMaximumHeight(220)

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
        layout.addWidget(self.preview_label)
        layout.addWidget(self.details_label)
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
        self._cancel_thumbnail_request()
        self.preview_label.clear()
        self.preview_label.setText("No preview available.")
        self._media = ()
        self.media_list.clear()
        self.media_list.setEnabled(False)
        self.select_button.setEnabled(False)
        self.details_label.setText("No image selected.")

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
        """Update confirmation state, details, and preview."""
        valid_selection = (
                self.media_list.isEnabled()
                and 0 <= row < len(self._media)
        )

        self.select_button.setEnabled(valid_selection)

        if not valid_selection:
            self._cancel_thumbnail_request()
            self.preview_label.clear()
            self.preview_label.setText("No preview available.")
            self.details_label.setText("No image selected.")
            return

        media = self._media[row]
        title = media.title.strip() or "Untitled image"

        self.details_label.setText(
            f"Title: {title}\n"
            f"Media ID: {media.remote_id}\n"
            f"URL: {media.source_url}"
        )

        self._load_thumbnail(media)

    def _accept_selected(self, *_args: object) -> None:
        """Accept the dialog only when an image is selected."""
        if self.selected_media() is not None:
            self.accept()

    def done(self, result: int) -> None:
        """Cancel pending thumbnail downloads before closing."""
        self._cancel_thumbnail_request()
        super().done(result)

    def _cancel_thumbnail_request(self) -> None:
        """Invalidate and cancel any previous thumbnail download."""
        self._thumbnail_request_id += 1

        reply = self._thumbnail_reply
        self._thumbnail_reply = None

        if reply is not None:
            reply.abort()
            reply.deleteLater()

    def _load_thumbnail(self, media: RemoteMedia) -> None:
        """Start loading a preview without blocking the UI."""
        self._cancel_thumbnail_request()

        url = media.thumbnail_url or media.source_url

        if not url:
            self.preview_label.setText("No preview available.")
            return

        self.preview_label.clear()
        self.preview_label.setText("Loading preview...")

        request_id = self._thumbnail_request_id
        request = QNetworkRequest(QUrl(url))
        reply = self._network_manager.get(request)
        self._thumbnail_reply = reply

        reply.finished.connect(
            lambda: self._on_thumbnail_finished(
                reply,
                request_id,
                media.remote_id,
            )
        )

    def _on_thumbnail_finished(
            self,
            reply: QNetworkReply,
            request_id: int,
            media_id: int,
    ) -> None:
        """Show a thumbnail only if its selection is still current."""
        if request_id != self._thumbnail_request_id:
            reply.deleteLater()
            return

        self._thumbnail_reply = None

        selected = self.selected_media()

        if selected is None or selected.remote_id != media_id:
            reply.deleteLater()
            return

        if reply.error() != QNetworkReply.NetworkError.NoError:
            self.preview_label.setText("Preview unavailable.")
            reply.deleteLater()
            return

        pixmap = QPixmap()
        if not pixmap.loadFromData(reply.readAll()):
            self.preview_label.setText("Preview unavailable.")
            reply.deleteLater()
            return

        scaled = pixmap.scaled(
            300,
            200,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.preview_label.setPixmap(scaled)
        reply.deleteLater()