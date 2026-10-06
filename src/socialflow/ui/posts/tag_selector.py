from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from socialflow.domain.post.tag import Tag


class TagSelector(QWidget):
    """UI control for selecting and creating post tags."""

    tag_created = Signal(Tag)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._available_tags: tuple[Tag, ...] = ()
        self._selected_tags: tuple[Tag, ...] = ()
        self._tag_checkboxes: list[QCheckBox] = []

        self.tag_input = QLineEdit(self)
        self.tag_input.setPlaceholderText("Enter a tag")

        self.add_button = QPushButton("Add tag", self)
        self.clear_button = QPushButton("Clear tags", self)

        self.status_label = QLabel("No tags selected.", self)
        self.selected_tags_label = QLabel("", self)
        self.selected_tags_label.setWordWrap(True)

        layout = QVBoxLayout()
        self.available_tags_layout = QVBoxLayout()
        layout.addLayout(self.available_tags_layout)
        layout.addWidget(self.tag_input)
        layout.addWidget(self.add_button)
        layout.addWidget(self.clear_button)
        layout.addWidget(self.status_label)
        layout.addWidget(self.selected_tags_label)

        self.setLayout(layout)

        self.add_button.clicked.connect(self._add_tag)
        self.clear_button.clicked.connect(self._clear_tags)

    def available_tags(self) -> tuple[Tag, ...]:
        """Return the currently available tags."""
        return self._available_tags

    def selected_tags(self) -> tuple[Tag, ...]:
        """Return the currently selected tags."""
        return self._selected_tags

    def set_selected_tags(
            self,
            tags: tuple[Tag, ...],
    ) -> None:
        """Replace the currently selected tags."""
        self._selected_tags = tags

        for index, available_tag in enumerate(self._available_tags):
            self._tag_checkboxes[index].setChecked(
                available_tag in tags
            )

        self._update_selection_display()

    def set_creation_enabled(self, enabled: bool) -> None:
        """Set whether new tags can be created."""
        self.tag_input.setEnabled(enabled)
        self.add_button.setEnabled(enabled)

    def _refresh_available_tags(self) -> None:
        """Refresh controls for available tags."""
        while self.available_tags_layout.count():
            item = self.available_tags_layout.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

        self._tag_checkboxes.clear()

        for tag in self._available_tags:
            checkbox = QCheckBox(tag.name, self)
            checkbox.toggled.connect(
                lambda checked, selected_tag=tag: (
                    self._set_tag_selected(
                        tag=selected_tag,
                        selected=checked,
                    )
                )
            )

            self._tag_checkboxes.append(checkbox)
            self.available_tags_layout.addWidget(checkbox)

    def set_available_tags(
        self,
        tags: tuple[Tag, ...],
    ) -> None:
        """Set the tags available for selection."""
        self._available_tags = tags
        self._refresh_available_tags()

    def _set_tag_selected(
        self,
        tag: Tag,
        selected: bool,
    ) -> None:
        """Update selection for an available tag."""
        if selected:
            if tag not in self._selected_tags:
                self._selected_tags += (tag,)
        else:
            self._selected_tags = tuple(
                selected_tag
                for selected_tag in self._selected_tags
                if selected_tag != tag
            )

        self._update_selection_display()

    def _add_tag(self) -> None:
        """Add the entered tag to the current selection."""
        name = self.tag_input.text().strip()

        if not name:
            return

        tag = Tag(name=name)
        available_tag_index = self._available_tag_index(tag)

        if tag not in self._selected_tags:
            self._selected_tags += (tag,)

        if available_tag_index is not None:
            self._tag_checkboxes[
                available_tag_index
            ].setChecked(True)
        else:
            self.tag_created.emit(tag)

        self.tag_input.clear()
        self._update_selection_display()

    def _available_tag_index(self, tag: Tag) -> int | None:
        """Return the index of an available tag when present."""
        for index, available_tag in enumerate(self._available_tags):
            if available_tag == tag:
                return index

        return None

    def remove_tag(self, tag: Tag) -> None:
        """Remove one tag from the current selection."""
        self._selected_tags = tuple(
            selected_tag
            for selected_tag in self._selected_tags
            if selected_tag != tag
        )

        available_tag_index = self._available_tag_index(tag)

        if available_tag_index is not None:
            self._tag_checkboxes[
                available_tag_index
            ].setChecked(False)

        self._update_selection_display()

    def _clear_tags(self) -> None:
        """Remove all currently selected tags."""
        self._selected_tags = ()

        for checkbox in self._tag_checkboxes:
            checkbox.setChecked(False)

        self._update_selection_display()

    def _update_selection_display(self) -> None:
        """Refresh the selected-tag display."""
        if not self._selected_tags:
            self.status_label.setText("No tags selected.")
            self.selected_tags_label.clear()
            return

        self.status_label.setText(
            f"{len(self._selected_tags)} tag(s) selected."
        )
        self.selected_tags_label.setText(
            ", ".join(tag.name for tag in self._selected_tags)
        )