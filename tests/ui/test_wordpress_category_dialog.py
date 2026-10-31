
from unittest.mock import patch

from PySide6.QtWidgets import QDialog, QMessageBox

from socialflow.domain.post.remote_category import RemoteCategory
from socialflow.ui.dialogs.wordpress_category_dialog import (
    WordPressCategoryDialog,
)


def categories():
    return (
        RemoteCategory(10, "Technology"),
        RemoteCategory(20, "Python", parent_id=10),
        RemoteCategory(30, "Tutorials"),
    )


def test_dialog_starts_with_top_level_parent(qtbot):
    dialog = WordPressCategoryDialog(categories())
    qtbot.addWidget(dialog)

    assert dialog.category_name() == ""
    assert dialog.parent_category_id() == 0
    assert dialog.is_confirmed() is False


def test_dialog_returns_normalized_name(qtbot):
    dialog = WordPressCategoryDialog()
    qtbot.addWidget(dialog)

    dialog.name_input.setText("  Software  ")

    assert dialog.category_name() == "Software"


def test_dialog_supports_subcategory_parent(qtbot):
    dialog = WordPressCategoryDialog(categories())
    qtbot.addWidget(dialog)

    index = dialog.parent_dropdown.findData(10)
    assert index >= 0

    dialog.parent_dropdown.setCurrentIndex(index)

    assert dialog.parent_category_id() == 10


def test_dialog_lists_all_available_parent_categories(qtbot):
    dialog = WordPressCategoryDialog(categories())
    qtbot.addWidget(dialog)

    ids = {
        dialog.parent_dropdown.itemData(index)
        for index in range(dialog.parent_dropdown.count())
    }

    assert ids == {0, 10, 20, 30}


def test_empty_name_cannot_be_confirmed(qtbot):
    dialog = WordPressCategoryDialog(categories())
    qtbot.addWidget(dialog)

    with patch.object(QMessageBox, "warning") as warning:
        dialog._confirm_creation()

    warning.assert_called_once()
    assert dialog.is_confirmed() is False
    assert dialog.result() != QDialog.DialogCode.Accepted


def test_duplicate_top_level_category_is_rejected(qtbot):
    dialog = WordPressCategoryDialog(categories())
    qtbot.addWidget(dialog)
    dialog.name_input.setText(" technology ")

    with patch.object(QMessageBox, "warning") as warning:
        dialog._confirm_creation()

    warning.assert_called_once()
    assert dialog.is_confirmed() is False


def test_duplicate_subcategory_is_rejected(qtbot):
    dialog = WordPressCategoryDialog(categories())
    qtbot.addWidget(dialog)

    dialog.name_input.setText("python")
    dialog.parent_dropdown.setCurrentIndex(
        dialog.parent_dropdown.findData(10)
    )

    with patch.object(QMessageBox, "warning") as warning:
        dialog._confirm_creation()

    warning.assert_called_once()
    assert dialog.is_confirmed() is False


def test_same_name_under_different_parent_is_allowed(qtbot):
    dialog = WordPressCategoryDialog(categories())
    qtbot.addWidget(dialog)

    dialog.name_input.setText("Python")

    with patch.object(
        QMessageBox,
        "question",
        return_value=QMessageBox.StandardButton.Yes,
    ):
        dialog._confirm_creation()

    assert dialog.is_confirmed() is True
    assert dialog.result() == QDialog.DialogCode.Accepted
    assert dialog.parent_category_id() == 0


def test_confirmation_accepts_new_subcategory(qtbot):
    dialog = WordPressCategoryDialog(categories())
    qtbot.addWidget(dialog)

    dialog.name_input.setText("Advanced Python")
    dialog.parent_dropdown.setCurrentIndex(
        dialog.parent_dropdown.findData(20)
    )

    with patch.object(
        QMessageBox,
        "question",
        return_value=QMessageBox.StandardButton.Yes,
    ) as question:
        dialog._confirm_creation()

    question.assert_called_once()
    assert dialog.category_name() == "Advanced Python"
    assert dialog.parent_category_id() == 20
    assert dialog.is_confirmed() is True
    assert dialog.result() == QDialog.DialogCode.Accepted


def test_confirmation_rejection_does_not_accept(qtbot):
    dialog = WordPressCategoryDialog(categories())
    qtbot.addWidget(dialog)
    dialog.name_input.setText("New Category")

    with patch.object(
        QMessageBox,
        "question",
        return_value=QMessageBox.StandardButton.No,
    ):
        dialog._confirm_creation()

    assert dialog.is_confirmed() is False
    assert dialog.result() != QDialog.DialogCode.Accepted


def test_cancel_does_not_confirm(qtbot):
    dialog = WordPressCategoryDialog(categories())
    qtbot.addWidget(dialog)

    dialog.reject()

    assert dialog.is_confirmed() is False
    assert dialog.result() == QDialog.DialogCode.Rejected
