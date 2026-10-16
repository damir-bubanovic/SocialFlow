from PySide6.QtWidgets import QDialog, QDialogButtonBox

from socialflow.domain.post.tag import Tag
from socialflow.infrastructure.wordpress.wordpress_tag_creation_plan import (
    WordPressTagCreationPlan,
)
from socialflow.ui.dialogs.wordpress_tag_confirmation_dialog import (
    WordPressTagConfirmationDialog,
)


def test_dialog_displays_missing_tags(qtbot):
    plan = WordPressTagCreationPlan(
        missing_tags=(
            Tag("Python"),
            Tag("SocialFlow"),
        ),
    )

    dialog = WordPressTagConfirmationDialog(plan)
    qtbot.addWidget(dialog)

    labels = dialog.findChildren(
        __import__("PySide6.QtWidgets", fromlist=["QLabel"]).QLabel
    )

    text = " ".join(label.text() for label in labels)

    assert "Python" in text
    assert "SocialFlow" in text


def test_dialog_accepts_confirmation(qtbot):
    plan = WordPressTagCreationPlan(
        missing_tags=(Tag("Python"),),
    )

    dialog = WordPressTagConfirmationDialog(plan)
    qtbot.addWidget(dialog)

    buttons = dialog.findChild(QDialogButtonBox)
    assert buttons is not None

    buttons.button(
        QDialogButtonBox.StandardButton.Yes
    ).click()

    assert dialog.result() == QDialog.DialogCode.Accepted


def test_dialog_rejects_cancellation(qtbot):
    plan = WordPressTagCreationPlan(
        missing_tags=(Tag("Python"),),
    )

    dialog = WordPressTagConfirmationDialog(plan)
    qtbot.addWidget(dialog)

    buttons = dialog.findChild(QDialogButtonBox)
    assert buttons is not None

    buttons.button(
        QDialogButtonBox.StandardButton.No
    ).click()

    assert dialog.result() == QDialog.DialogCode.Rejected