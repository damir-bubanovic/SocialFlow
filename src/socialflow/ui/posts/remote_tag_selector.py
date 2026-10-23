
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from socialflow.domain.post.remote_tag import RemoteTag


class RemoteTagSelector(QWidget):
    """Select WordPress tags by name while preserving their remote IDs."""

    selection_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._available_tags: tuple[RemoteTag, ...] = ()
        self._selected_ids: tuple[int, ...] = ()

        self.tags_list = QListWidget(self)
        self.tags_list.setEnabled(False)
        self.tags_list.itemChanged.connect(self._on_item_changed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.tags_list)

    def set_available_tags(
        self,
        tags: tuple[RemoteTag, ...],
    ) -> None:
        """Refresh tag names without losing the selected IDs."""
        self._available_tags = tags
        self._rebuild_items()

    def set_selected_ids(
        self,
        tag_ids: tuple[int, ...],
    ) -> None:
        """Select the IDs already assigned to a remote post."""
        self._selected_ids = tuple(dict.fromkeys(tag_ids))
        self._rebuild_items()

    def selected_ids(self) -> tuple[int, ...]:
        """Return the selected WordPress tag IDs."""
        return self._selected_ids

    def available_tags(self) -> tuple[RemoteTag, ...]:
        """Return the available remote tags."""
        return self._available_tags

    def _rebuild_items(self) -> None:
        """Build checkable names and preserve unknown assigned IDs."""
        self.tags_list.blockSignals(True)

        try:
            self.tags_list.clear()

            known_ids = {
                tag.remote_id
                for tag in self._available_tags
            }

            for tag in self._available_tags:
                self._add_item(
                    tag.name,
                    tag.remote_id,
                    tag.remote_id in self._selected_ids,
                )

            for tag_id in self._selected_ids:
                if tag_id not in known_ids:
                    self._add_item(
                        f"Unknown WordPress tag (ID {tag_id})",
                        tag_id,
                        True,
                    )
        finally:
            self.tags_list.blockSignals(False)

    def _add_item(
        self,
        name: str,
        tag_id: int,
        selected: bool,
    ) -> None:
        item = QListWidgetItem(name)
        item.setData(Qt.ItemDataRole.UserRole, tag_id)
        item.setFlags(
            item.flags() | Qt.ItemFlag.ItemIsUserCheckable
        )
        item.setCheckState(
            Qt.CheckState.Checked
            if selected
            else Qt.CheckState.Unchecked
        )
        self.tags_list.addItem(item)

    def _on_item_changed(self, item: QListWidgetItem) -> None:
        """Update selected IDs after the user changes a checkbox."""
        tag_id = item.data(Qt.ItemDataRole.UserRole)
        selected = list(self._selected_ids)

        if item.checkState() == Qt.CheckState.Checked:
            if tag_id not in selected:
                selected.append(tag_id)
        else:
            selected = [
                existing_id
                for existing_id in selected
                if existing_id != tag_id
            ]

        updated = tuple(selected)

        if updated != self._selected_ids:
            self._selected_ids = updated
            self.selection_changed.emit()
