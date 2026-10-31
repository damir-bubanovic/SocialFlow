
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from socialflow.domain.post.remote_category import RemoteCategory


class WordPressCategoryDialog(QDialog):
    """Collect and confirm a new WordPress category."""

    def __init__(
        self,
        categories: tuple[RemoteCategory, ...] = (),
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.setWindowTitle("Add WordPress Category")
        self.setMinimumWidth(380)

        self._categories = categories
        self._confirmed = False

        layout = QVBoxLayout(self)

        description = QLabel(
            "Create a WordPress category or subcategory."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        form = QFormLayout()

        self.name_input = QLineEdit(self)
        self.name_input.setPlaceholderText("Category name")
        form.addRow("Name:", self.name_input)

        self.parent_dropdown = QComboBox(self)
        self.parent_dropdown.addItem(
            "None (top-level category)",
            userData=0,
        )

        for category in sorted(
            categories,
            key=lambda item: (
                item.name.casefold(),
                item.remote_id,
            ),
        ):
            self.parent_dropdown.addItem(
                category.name,
                userData=category.remote_id,
            )

        form.addRow("Parent category:", self.parent_dropdown)
        layout.addLayout(form)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )

        self.buttons.button(
            QDialogButtonBox.StandardButton.Ok
        ).setText("Review creation")

        self.buttons.accepted.connect(self._confirm_creation)
        self.buttons.rejected.connect(self.reject)

        layout.addWidget(self.buttons)

    def category_name(self) -> str:
        return self.name_input.text().strip()

    def parent_category_id(self) -> int:
        return int(
            self.parent_dropdown.currentData(
                Qt.ItemDataRole.UserRole
            )
        )

    def is_confirmed(self) -> bool:
        return self._confirmed

    def _confirm_creation(self) -> None:
        name = self.category_name()

        if not name:
            QMessageBox.warning(
                self,
                "Category name required",
                "Enter a category name before continuing.",
            )
            self.name_input.setFocus()
            return

        parent_id = self.parent_category_id()

        for existing in self._categories:
            if (
                existing.parent_id == parent_id
                and existing.name.casefold() == name.casefold()
            ):
                QMessageBox.warning(
                    self,
                    "Category already exists",
                    "A category with this name already exists "
                    "under the selected parent.",
                )
                return

        parent_name = "None (top-level)"

        for existing in self._categories:
            if existing.remote_id == parent_id:
                parent_name = existing.name
                break

        answer = QMessageBox.question(
            self,
            "Confirm WordPress category creation",
            f"Create this category on WordPress?\n\n"
            f"Name: {name}\n"
            f"Parent: {parent_name}",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer == QMessageBox.StandardButton.Yes:
            self._confirmed = True
            self.accept()
