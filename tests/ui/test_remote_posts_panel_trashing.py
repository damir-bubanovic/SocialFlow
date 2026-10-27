
"""Regression tests for the WordPress Move to Trash UI."""

from datetime import datetime

from PySide6.QtCore import Qt

from socialflow.domain.post.remote_post import RemotePost
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.ui.posts.remote_posts_panel import RemotePostsPanel


def make_post(remote_id: str = "42") -> RemotePost:
    return RemotePost(
        remote_id=remote_id,
        destination=PublishingDestination.WORDPRESS,
        content="Example WordPress content",
        published_at=datetime(2026, 10, 15, 12, 0),
        status="publish",
        title="Example title",
    )


def make_panel(qtbot) -> RemotePostsPanel:
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)
    return panel


def test_trash_button_disabled_without_selection(qtbot):
    panel = make_panel(qtbot)

    assert not panel.trash_button.isEnabled()

    panel.show_posts((make_post(),))

    assert panel.posts_list.currentRow() == -1
    assert not panel.trash_button.isEnabled()

    panel.posts_list.setCurrentRow(0)

    assert panel.trash_button.isEnabled()


def test_trash_button_emits_selected_remote_id(qtbot):
    panel = make_panel(qtbot)
    panel.show_posts((make_post("42"), make_post("99")))
    panel.posts_list.setCurrentRow(1)

    with qtbot.waitSignal(panel.trash_requested, timeout=1000) as signal:
        qtbot.mouseClick(
            panel.trash_button,
            Qt.MouseButton.LeftButton,
        )

    assert signal.args == ["99"]


def test_trash_request_ignored_without_selection(qtbot):
    panel = make_panel(qtbot)
    panel.show_posts((make_post(),))

    received_ids = []
    panel.trash_requested.connect(received_ids.append)

    panel._request_trash()

    assert received_ids == []


def test_clearing_selection_disables_trash(qtbot):
    panel = make_panel(qtbot)
    panel.show_posts((make_post(),))
    panel.posts_list.setCurrentRow(0)

    assert panel.trash_button.isEnabled()

    panel.posts_list.setCurrentRow(-1)

    assert not panel.trash_button.isEnabled()


def test_trash_operation_disables_editing(qtbot):
    panel = make_panel(qtbot)
    panel.show_posts((make_post(),))
    panel.posts_list.setCurrentRow(0)

    panel.set_trashing(True)

    assert not panel.posts_list.isEnabled()
    assert not panel.post_title_editor.isEnabled()
    assert not panel.content_editor.isEnabled()
    assert not panel.excerpt_editor.isEnabled()
    assert not panel.post_status_selector.isEnabled()
    assert not panel.remote_tag_selector.tags_list.isEnabled()
    assert not panel.featured_media_checkbox.isEnabled()
    assert not panel.browse_media_button.isEnabled()
    assert not panel.save_button.isEnabled()
    assert not panel.trash_button.isEnabled()


def test_failed_trash_restores_selected_post(qtbot):
    panel = make_panel(qtbot)
    panel.show_posts((make_post(),))
    panel.posts_list.setCurrentRow(0)

    panel.set_trashing(True)
    panel.set_trashing(False)

    assert panel.posts_list.isEnabled()
    assert panel.post_title_editor.isEnabled()
    assert panel.content_editor.isEnabled()
    assert panel.excerpt_editor.isEnabled()
    assert panel.trash_button.isEnabled()


def test_save_operation_disables_trash(qtbot):
    panel = make_panel(qtbot)
    panel.show_posts((make_post(),))
    panel.posts_list.setCurrentRow(0)

    panel.content_editor.setPlainText("Updated WordPress content")

    assert panel.save_button.isEnabled()
    assert panel.trash_button.isEnabled()

    panel._request_save()

    assert not panel.save_button.isEnabled()
    assert not panel.trash_button.isEnabled()
    assert not panel.posts_list.isEnabled()


def test_reloading_posts_clears_previous_selection(qtbot):
    panel = make_panel(qtbot)
    panel.show_posts((make_post("42"),))
    panel.posts_list.setCurrentRow(0)

    assert panel.trash_button.isEnabled()

    panel.show_loading()
    panel.show_posts((make_post("99"),))

    assert panel.posts_list.currentRow() == -1
    assert not panel.trash_button.isEnabled()

    panel.posts_list.setCurrentRow(0)

    assert panel.trash_button.isEnabled()


def test_error_and_empty_state_disable_trash(qtbot):
    panel = make_panel(qtbot)
    panel.show_posts((make_post(),))
    panel.posts_list.setCurrentRow(0)

    panel.show_error("Connection failed")

    assert not panel.trash_button.isEnabled()

    panel.show_posts((make_post(),))
    panel.posts_list.setCurrentRow(0)

    panel.show_empty()

    assert not panel.trash_button.isEnabled()
    assert panel.posts_list.count() == 0


def test_failed_save_restores_trash_button(qtbot):
    panel = make_panel(qtbot)
    panel.show_posts((make_post(),))
    panel.posts_list.setCurrentRow(0)

    panel.content_editor.setPlainText("Updated content")
    panel._request_save()

    assert not panel.trash_button.isEnabled()

    panel.restore_editing()

    assert panel.trash_button.isEnabled()
    assert panel.save_button.isEnabled()
