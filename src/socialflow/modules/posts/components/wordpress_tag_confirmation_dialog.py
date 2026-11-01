from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QVBoxLayout,
)

from socialflow.modules.posts.models.remote_tag_creation_plan import (
    RemoteTagCreationPlan,
)


class WordPressTagConfirmationDialog(QDialog):
    """Ask permission before creating missing WordPress tags."""

    def __init__(
        self,
        plan: RemoteTagCreationPlan,
        parent=None,
    ) -> None:
        super().__init__(parent)

        self.setWindowTitle("Create WordPress Tags")
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)

        message = QLabel(
            "The following tags do not exist on WordPress.\n"
            "Do you want to create them?"
        )
        message.setWordWrap(True)
        layout.addWidget(message)

        tag_list = QLabel(
            "\n".join(
                f"• {name}"
                for name in plan.tag_names
            )
        )
        tag_list.setWordWrap(True)
        layout.addWidget(tag_list)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Yes
            | QDialogButtonBox.StandardButton.No
        )

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)