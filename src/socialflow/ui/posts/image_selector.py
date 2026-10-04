from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
    QFrame,
)

from socialflow.application.images.image_validator import ImageValidator
from socialflow.domain.post.image_attachment import ImageAttachment


class ImageSelector(QWidget):
    """UI control for selecting images to attach to a post."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._images: tuple[ImageAttachment, ...] = ()

        self.select_button = QPushButton("Add images", self)
        self.clear_button = QPushButton("Clear images", self)
        self.status_label = QLabel("No images selected.", self)
        self.error_label = QLabel("", self)
        self.error_label.setWordWrap(True)
        self.filenames_label = QLabel("", self)
        self.filenames_label.setWordWrap(True)
        self.preview_layout = QHBoxLayout()

        layout = QVBoxLayout()
        layout.addWidget(self.select_button)
        layout.addWidget(self.clear_button)
        layout.addWidget(self.status_label)
        layout.addWidget(self.error_label)
        layout.addWidget(self.filenames_label)
        layout.addLayout(self.preview_layout)

        self.setLayout(layout)

        self.select_button.clicked.connect(self._select_images)
        self.clear_button.clicked.connect(self._clear_images)

    def selected_images(self) -> tuple[ImageAttachment, ...]:
        """Return the currently selected image attachments."""
        return self._images

    def _select_images(self) -> None:
        """Open a file dialog and store the selected image files."""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select images",
            "",
            "Images (*.jpg *.jpeg *.png *.webp)",
        )

        if not file_paths:
            return

        self.error_label.clear()

        new_images = []

        for file_path in file_paths:
            try:
                attachment = ImageAttachment(path=Path(file_path))
                ImageValidator.validate(attachment)
            except ValueError as error:
                self.error_label.setText(str(error))
                continue

            new_images.append(attachment)

        new_images = tuple(new_images)

        existing_paths = {
            image.path for image in self._images
        }

        self._images += tuple(
            image
            for image in new_images
            if image.path not in existing_paths
        )

        self._update_selection_display()

    def remove_image(self, image: ImageAttachment) -> None:
        """Remove one image from the current selection."""
        self._images = tuple(
            selected_image
            for selected_image in self._images
            if selected_image != image
        )

        self._update_selection_display()

    def _clear_images(self) -> None:
        """Remove all currently selected image attachments."""
        self._images = ()
        self._update_selection_display()

    def _update_selection_display(self) -> None:
        """Refresh selection status, filenames, and previews."""
        if not self._images:
            self.status_label.setText("No images selected.")
            self.filenames_label.clear()
            self._clear_previews()
            return

        self.status_label.setText(
            f"{len(self._images)} image(s) selected."
        )
        self.filenames_label.setText(
            "\n".join(image.filename for image in self._images)
        )
        self._refresh_previews()

    def _refresh_previews(self) -> None:
        """Display thumbnail previews for the selected images."""
        self._clear_previews()

        for image in self._images:
            pixmap = QPixmap(str(image.path))

            if pixmap.isNull():
                continue

            thumbnail = pixmap.scaled(
                120,
                120,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

            preview_container = QFrame(self)
            preview_container.setProperty("image_path", str(image.path))

            preview_container_layout = QVBoxLayout(preview_container)

            preview = QLabel(preview_container)
            preview.setPixmap(thumbnail)

            remove_button = QPushButton("Remove", preview_container)
            remove_button.clicked.connect(
                lambda checked=False, selected_image=image: self.remove_image(
                    selected_image
                )
            )

            preview_container_layout.addWidget(preview)
            preview_container_layout.addWidget(remove_button)

            self.preview_layout.addWidget(preview_container)

    def _clear_previews(self) -> None:
        """Remove all currently displayed image previews."""
        while self.preview_layout.count():
            item = self.preview_layout.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.deleteLater()