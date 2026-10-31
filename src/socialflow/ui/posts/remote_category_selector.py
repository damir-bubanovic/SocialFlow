
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from socialflow.domain.post.remote_category import RemoteCategory


class RemoteCategorySelector(QWidget):
    """Multi-select WordPress categories with parent-child display."""

    selection_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._available_categories: tuple[RemoteCategory, ...] = ()
        self._selected_ids: tuple[int, ...] = ()

        self.category_dropdown = QComboBox(self)
        self.category_dropdown.addItem("Select categories...")

        self.categories_list = QListWidget(self)
        self.categories_list.setEnabled(True)
        self.categories_list.setMaximumHeight(160)
        self.categories_list.itemChanged.connect(
            self._on_item_changed
        )

        self.category_dropdown.setModel(
            self.categories_list.model()
        )
        self.category_dropdown.setView(self.categories_list)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.category_dropdown)

        self._rebuild_items()

    def set_available_categories(
        self,
        categories: tuple[RemoteCategory, ...],
    ) -> None:
        self._available_categories = categories
        self._rebuild_items()

    def available_categories(self) -> tuple[RemoteCategory, ...]:
        return self._available_categories

    def set_selected_ids(
        self,
        category_ids: tuple[int, ...],
    ) -> None:
        self._selected_ids = tuple(dict.fromkeys(category_ids))
        self._rebuild_items()

    def selected_ids(self) -> tuple[int, ...]:
        return self._selected_ids

    def _ordered_categories(self) -> tuple[tuple[RemoteCategory, int], ...]:
        """Arrange categories by hierarchy without recursive cycles."""
        by_parent: dict[int, list[RemoteCategory]] = {}

        for category in self._available_categories:
            by_parent.setdefault(category.parent_id, []).append(
                category
            )

        for siblings in by_parent.values():
            siblings.sort(
                key=lambda sibling: (
                    sibling.name.casefold(),
                    sibling.remote_id,
                )
            )

        ordered: list[tuple[RemoteCategory, int]] = []
        visited: set[int] = set()

        def visit(node: RemoteCategory, depth: int) -> None:
            if node.remote_id in visited:
                return

            visited.add(node.remote_id)
            ordered.append((node, depth))

            for child in by_parent.get(node.remote_id, []):
                visit(child, depth + 1)

        known_ids = {
            category.remote_id
            for category in self._available_categories
        }

        for category in self._available_categories:
            if category.parent_id not in known_ids:
                visit(category, 0)

        # Handles malformed remote hierarchies without infinite loops.
        for category in self._available_categories:
            visit(category, 0)

        return tuple(ordered)

    def _rebuild_items(self) -> None:
        self.categories_list.blockSignals(True)

        try:
            self.categories_list.clear()

            known_ids = {
                category.remote_id
                for category in self._available_categories
            }

            for category, depth in self._ordered_categories():
                self._add_item(
                    category.name,
                    category.remote_id,
                    category.remote_id in self._selected_ids,
                    depth,
                )

            for category_id in self._selected_ids:
                if category_id not in known_ids:
                    self._add_item(
                        f"Unknown WordPress category (ID {category_id})",
                        category_id,
                        True,
                        0,
                    )
        finally:
            self.categories_list.blockSignals(False)

        self._update_summary()

    def _add_item(
        self,
        name: str,
        category_id: int,
        selected: bool,
        depth: int,
    ) -> None:
        item = QListWidgetItem(
            "    " * depth + name
        )
        item.setData(
            Qt.ItemDataRole.UserRole,
            category_id,
        )
        item.setFlags(
            item.flags() | Qt.ItemFlag.ItemIsUserCheckable
        )
        item.setCheckState(
            Qt.CheckState.Checked
            if selected
            else Qt.CheckState.Unchecked
        )
        self.categories_list.addItem(item)

    def _update_summary(self) -> None:
        count = len(self._selected_ids)

        if count == 0:
            summary = "Select categories..."
        elif count == 1:
            summary = "1 category selected"
        else:
            summary = f"{count} categories selected"

        # The combo uses the list's model, so update its
        # display text without inserting a selectable row.
        self.category_dropdown.setEditable(True)
        self.category_dropdown.lineEdit().setReadOnly(True)
        self.category_dropdown.lineEdit().setText(summary)

    def _on_item_changed(self, item: QListWidgetItem) -> None:
        category_id = item.data(Qt.ItemDataRole.UserRole)
        selected = list(self._selected_ids)

        if item.checkState() == Qt.CheckState.Checked:
            if category_id not in selected:
                selected.append(category_id)
        else:
            selected = [
                existing_id
                for existing_id in selected
                if existing_id != category_id
            ]

        updated = tuple(selected)

        if updated != self._selected_ids:
            self._selected_ids = updated
            self._update_summary()
            self.selection_changed.emit()
