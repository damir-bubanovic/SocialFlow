
from PySide6.QtWidgets import QDialog

from socialflow.domain.post.remote_media import RemoteMedia
from socialflow.domain.publishing.destination import (
    PublishingDestination,
)
from socialflow.ui.posts.remote_media_selection_dialog import (
    RemoteMediaSelectionDialog,
)


def make_media(
    media_id: int = 123,
    title: str = "Example photo",
) -> RemoteMedia:
    return RemoteMedia(
        remote_id=media_id,
        destination=PublishingDestination.WORDPRESS,
        source_url=f"https://example.com/uploads/{media_id}.jpg",
        title=title,
    )


def test_dialog_starts_without_selection(qtbot):
    dialog = RemoteMediaSelectionDialog()
    qtbot.addWidget(dialog)

    assert dialog.media_list.count() == 0
    assert dialog.selected_media() is None
    assert dialog.selected_media_id() is None
    assert not dialog.select_button.isEnabled()


def test_dialog_displays_media(qtbot):
    dialog = RemoteMediaSelectionDialog()
    qtbot.addWidget(dialog)

    dialog.show_media((
        make_media(123, "Example photo"),
        make_media(456, "Banner"),
    ))

    assert dialog.media_list.count() == 2
    assert dialog.media_list.item(0).text() == (
        "Example photo (ID 123)"
    )
    assert dialog.media_list.item(1).text() == (
        "Banner (ID 456)"
    )
    assert dialog.selected_media_id() is None
    assert not dialog.select_button.isEnabled()


def test_dialog_selects_media(qtbot):
    dialog = RemoteMediaSelectionDialog()
    qtbot.addWidget(dialog)

    media = make_media(456, "Banner")
    dialog.show_media((make_media(), media))

    dialog.media_list.setCurrentRow(1)

    assert dialog.selected_media() == media
    assert dialog.selected_media_id() == 456
    assert dialog.select_button.isEnabled()


def test_dialog_accepts_selected_media(qtbot):
    dialog = RemoteMediaSelectionDialog()
    qtbot.addWidget(dialog)

    dialog.show_media((make_media(123),))
    dialog.media_list.setCurrentRow(0)
    dialog.select_button.click()

    assert dialog.result() == QDialog.DialogCode.Accepted
    assert dialog.selected_media_id() == 123


def test_dialog_does_not_accept_without_selection(qtbot):
    dialog = RemoteMediaSelectionDialog()
    qtbot.addWidget(dialog)

    dialog.show_media((make_media(),))
    dialog._accept_selected()

    assert dialog.result() != QDialog.DialogCode.Accepted


def test_dialog_shows_loading(qtbot):
    dialog = RemoteMediaSelectionDialog()
    qtbot.addWidget(dialog)

    dialog.show_media((make_media(),))
    dialog.show_loading()

    assert dialog.media_list.count() == 0
    assert not dialog.select_button.isEnabled()
    assert "Loading" in dialog.status_label.text()


def test_dialog_shows_empty_results(qtbot):
    dialog = RemoteMediaSelectionDialog()
    qtbot.addWidget(dialog)

    dialog.show_media(())

    assert dialog.media_list.count() == 0
    assert not dialog.select_button.isEnabled()
    assert "No WordPress images" in dialog.status_label.text()


def test_dialog_shows_error(qtbot):
    dialog = RemoteMediaSelectionDialog()
    qtbot.addWidget(dialog)

    dialog.show_media((make_media(),))
    dialog.show_error("Connection failed")

    assert dialog.media_list.count() == 0
    assert dialog.selected_media_id() is None
    assert not dialog.select_button.isEnabled()
    assert "Connection failed" in dialog.status_label.text()


def test_dialog_handles_untitled_media(qtbot):
    dialog = RemoteMediaSelectionDialog()
    qtbot.addWidget(dialog)

    dialog.show_media((make_media(title=""),))

    assert dialog.media_list.item(0).text() == (
        "Untitled image (ID 123)"
    )
