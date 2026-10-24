from unittest.mock import Mock

import struct
import zlib
from PySide6.QtNetwork import QNetworkReply

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

def make_png_bytes() -> bytes:
    """Create a small valid RGB PNG using the standard library."""
    width = 8
    height = 8

    pixel = bytes((51, 102, 153))
    row = b"\x00" + pixel * width
    compressed = zlib.compress(row * height)

    def chunk(chunk_type: bytes, data: bytes) -> bytes:
        payload = chunk_type + data
        return (
            struct.pack(">I", len(data))
            + payload
            + struct.pack(">I", zlib.crc32(payload) & 0xFFFFFFFF)
        )

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(
            b"IHDR",
            struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0),
        )
        + chunk(b"IDAT", compressed)
        + chunk(b"IEND", b"")
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


def test_dialog_displays_selected_image_details(qtbot):
    dialog = RemoteMediaSelectionDialog()
    qtbot.addWidget(dialog)

    dialog.show_media((
        make_media(123, "Example photo"),
        make_media(456, "Banner"),
    ))

    assert dialog.details_label.text() == "No image selected."

    dialog.media_list.setCurrentRow(1)

    assert dialog.details_label.text() == (
        "Title: Banner\n"
        "Media ID: 456\n"
        "URL: https://example.com/uploads/456.jpg"
    )


def test_dialog_updates_details_when_selection_changes(qtbot):
    dialog = RemoteMediaSelectionDialog()
    qtbot.addWidget(dialog)

    dialog.show_media((
        make_media(123, "Example photo"),
        make_media(456, "Banner"),
    ))

    dialog.media_list.setCurrentRow(0)
    assert "Media ID: 123" in dialog.details_label.text()

    dialog.media_list.setCurrentRow(1)
    assert "Media ID: 456" in dialog.details_label.text()
    assert "Media ID: 123" not in dialog.details_label.text()

    dialog.media_list.clearSelection()
    dialog.media_list.setCurrentRow(-1)

    assert dialog.details_label.text() == "No image selected."
    assert not dialog.select_button.isEnabled()


def test_dialog_clears_details_during_loading_and_error(qtbot):
    dialog = RemoteMediaSelectionDialog()
    qtbot.addWidget(dialog)

    dialog.show_media((make_media(123),))
    dialog.media_list.setCurrentRow(0)

    assert "Media ID: 123" in dialog.details_label.text()

    dialog.show_loading()

    assert dialog.details_label.text() == "No image selected."

    dialog.show_error("Connection failed")

    assert dialog.details_label.text() == "No image selected."
    assert not dialog.select_button.isEnabled()

def test_dialog_preview_starts_empty(qtbot):
    dialog = RemoteMediaSelectionDialog()
    qtbot.addWidget(dialog)

    assert dialog.preview_label.text() == "No preview available."
    assert dialog.preview_label.pixmap().isNull()


def test_dialog_clears_preview_when_loading(qtbot):
    dialog = RemoteMediaSelectionDialog()
    qtbot.addWidget(dialog)

    dialog.show_media((make_media(123),))
    dialog.media_list.setCurrentRow(0)

    assert dialog.preview_label.text() == "Loading preview..."

    dialog.show_loading()

    assert dialog.preview_label.text() == "No preview available."
    assert dialog.preview_label.pixmap().isNull()


def test_dialog_cancels_preview_when_selection_cleared(qtbot):
    dialog = RemoteMediaSelectionDialog()
    qtbot.addWidget(dialog)

    dialog.show_media((make_media(123),))
    dialog.media_list.setCurrentRow(0)

    dialog.media_list.setCurrentRow(-1)

    assert dialog.preview_label.text() == "No preview available."
    assert dialog._thumbnail_reply is None

def test_dialog_cancels_thumbnail_request_on_reject(qtbot):
    dialog = RemoteMediaSelectionDialog()
    qtbot.addWidget(dialog)

    initial_request_id = dialog._thumbnail_request_id

    dialog.reject()

    assert dialog.result() == QDialog.DialogCode.Rejected
    assert dialog._thumbnail_request_id == initial_request_id + 1
    assert dialog._thumbnail_reply is None

def test_dialog_displays_successful_thumbnail(qtbot):
    dialog = RemoteMediaSelectionDialog()
    qtbot.addWidget(dialog)

    dialog.show_media((make_media(123),))
    dialog.media_list.setCurrentRow(0)

    request_id = dialog._thumbnail_request_id

    reply = Mock()
    reply.error.return_value = QNetworkReply.NetworkError.NoError
    reply.readAll.return_value = make_png_bytes()

    dialog._on_thumbnail_finished(reply, request_id, 123)

    assert not dialog.preview_label.pixmap().isNull()
    assert dialog.preview_label.text() == ""
    reply.deleteLater.assert_called_once_with()


def test_dialog_handles_invalid_thumbnail_data(qtbot):
    dialog = RemoteMediaSelectionDialog()
    qtbot.addWidget(dialog)

    dialog.show_media((make_media(123),))
    dialog.media_list.setCurrentRow(0)

    request_id = dialog._thumbnail_request_id

    reply = Mock()
    reply.error.return_value = QNetworkReply.NetworkError.NoError
    reply.readAll.return_value = b"not an image"

    dialog._on_thumbnail_finished(reply, request_id, 123)

    assert dialog.preview_label.text() == "Preview unavailable."
    assert dialog.preview_label.pixmap().isNull()
    reply.deleteLater.assert_called_once_with()


def test_dialog_handles_thumbnail_network_error(qtbot):
    dialog = RemoteMediaSelectionDialog()
    qtbot.addWidget(dialog)

    dialog.show_media((make_media(123),))
    dialog.media_list.setCurrentRow(0)

    request_id = dialog._thumbnail_request_id

    reply = Mock()
    reply.error.return_value = (
        QNetworkReply.NetworkError.ConnectionRefusedError
    )

    dialog._on_thumbnail_finished(reply, request_id, 123)

    assert dialog.preview_label.text() == "Preview unavailable."
    assert dialog.preview_label.pixmap().isNull()
    reply.readAll.assert_not_called()
    reply.deleteLater.assert_called_once_with()


def test_dialog_ignores_stale_thumbnail_response(qtbot):
    dialog = RemoteMediaSelectionDialog()
    qtbot.addWidget(dialog)

    dialog.show_media((
        make_media(123),
        make_media(456),
    ))

    dialog.media_list.setCurrentRow(0)
    stale_request_id = dialog._thumbnail_request_id

    dialog.media_list.setCurrentRow(1)

    reply = Mock()

    dialog._on_thumbnail_finished(reply, stale_request_id, 123)

    assert dialog.selected_media_id() == 456
    assert dialog.preview_label.text() == "Loading preview..."
    reply.readAll.assert_not_called()
    reply.deleteLater.assert_called_once_with()

def test_dialog_clears_previous_thumbnail_on_new_selection(qtbot):
    dialog = RemoteMediaSelectionDialog()
    qtbot.addWidget(dialog)

    dialog.show_media((
        make_media(123),
        make_media(456),
    ))

    dialog.media_list.setCurrentRow(0)

    reply = Mock()
    reply.error.return_value = QNetworkReply.NetworkError.NoError
    reply.readAll.return_value = make_png_bytes()

    dialog._on_thumbnail_finished(
        reply,
        dialog._thumbnail_request_id,
        123,
    )

    assert not dialog.preview_label.pixmap().isNull()

    dialog.media_list.setCurrentRow(1)

    assert dialog.preview_label.text() == "Loading preview..."
    assert dialog.preview_label.pixmap().isNull()