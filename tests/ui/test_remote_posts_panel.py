from datetime import datetime
import pytest

from socialflow.domain.post.remote_post import RemotePost
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.ui.posts.remote_posts_panel import RemotePostsPanel
from socialflow.domain.post.remote_tag import RemoteTag
from PySide6.QtCore import Qt


def test_panel_starts_empty(qtbot):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    assert panel.posts_list.count() == 0
    assert "Select a WordPress account" in panel.status_label.text()


def test_panel_shows_loading(qtbot):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    panel.show_loading()

    assert panel.posts_list.count() == 0
    assert panel.status_label.text() == "Loading WordPress posts..."


def test_panel_displays_remote_posts(qtbot):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    post = RemotePost(
        remote_id="123",
        destination=PublishingDestination.WORDPRESS,
        content="Example WordPress post",
        published_at=datetime(2026, 10, 15, 12, 0),
        status="publish",
    )

    panel.show_posts((post,))

    assert panel.posts_list.count() == 1
    assert "Example WordPress post" in panel.posts_list.item(0).text()
    assert "1 remote posts loaded" == panel.status_label.text()


def test_panel_displays_empty_results(qtbot):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    panel.show_posts(())

    assert panel.posts_list.count() == 0
    assert panel.status_label.text() == "No remote posts found."


def test_panel_displays_error(qtbot):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    panel.show_error("Connection failed")

    assert panel.posts_list.count() == 0
    assert "Connection failed" in panel.status_label.text()


def test_panel_displays_remote_tag_names(qtbot) -> None:
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    panel.set_available_remote_tags((
        RemoteTag(remote_id=12, name="Python"),
        RemoteTag(remote_id=34, name="News"),
    ))

    assert panel.remote_tag_selector.tags_list.count() == 2
    assert panel.remote_tag_selector.tags_list.item(0).text() == "Python"
    assert panel.remote_tag_selector.tags_list.item(1).text() == "News"


def test_panel_preserves_post_tag_selection(qtbot) -> None:
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    panel.set_available_remote_tags((
        RemoteTag(remote_id=12, name="Python"),
        RemoteTag(remote_id=34, name="News"),
    ))

    post = RemotePost(
        remote_id="123",
        destination=PublishingDestination.WORDPRESS,
        content="Example",
        published_at=datetime(2026, 10, 15, 12, 0),
        status="publish",
        tag_ids=(34,),
    )

    panel.show_posts((post,))
    panel.posts_list.setCurrentRow(0)

    assert panel.remote_tag_selector.selected_ids() == (34,)
    assert (
        panel.remote_tag_selector.tags_list.item(1).checkState()
        == Qt.CheckState.Checked
    )


def test_panel_updates_unknown_tag_name_after_loading(qtbot) -> None:
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    post = RemotePost(
        remote_id="123",
        destination=PublishingDestination.WORDPRESS,
        content="Example",
        published_at=datetime(2026, 10, 15, 12, 0),
        status="publish",
        tag_ids=(99,),
    )

    panel.show_posts((post,))
    panel.posts_list.setCurrentRow(0)

    assert panel.remote_tag_selector.tags_list.item(0).text() == (
        "Unknown WordPress tag (ID 99)"
    )

    panel.set_available_remote_tags((
        RemoteTag(remote_id=99, name="Announcements"),
    ))

    assert panel.remote_tag_selector.selected_ids() == (99,)
    assert panel.remote_tag_selector.tags_list.item(0).text() == (
        "Announcements"
    )


def test_panel_loads_existing_featured_media_id(qtbot):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    post = RemotePost(
        remote_id="123",
        destination=PublishingDestination.WORDPRESS,
        content="Original content",
        published_at=datetime(2026, 10, 15, 12, 0),
        status="publish",
        featured_media_id=456,
    )

    panel.show_posts((post,))
    panel.posts_list.setCurrentRow(0)

    assert panel.featured_media_input.value() == 456
    assert not panel.featured_media_checkbox.isChecked()
    assert not panel.featured_media_input.isEnabled()
    assert not panel.save_button.isEnabled()


def test_panel_requests_featured_media_update(qtbot):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    post = RemotePost(
        remote_id="123",
        destination=PublishingDestination.WORDPRESS,
        content="Original content",
        published_at=datetime(2026, 10, 15, 12, 0),
        status="publish",
        featured_media_id=456,
    )

    panel.show_posts((post,))
    panel.posts_list.setCurrentRow(0)

    panel.featured_media_checkbox.setChecked(True)
    panel.featured_media_input.setValue(789)

    assert panel.save_button.isEnabled()

    with qtbot.waitSignal(
        panel.save_with_media_requested,
        timeout=1000,
    ) as signal:
        panel.save_button.click()

    assert signal.args == [
        "123",
        "Original content",
        None,
        789,
    ]


def test_panel_requests_featured_media_removal(qtbot):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    post = RemotePost(
        remote_id="123",
        destination=PublishingDestination.WORDPRESS,
        content="Original content",
        published_at=datetime(2026, 10, 15, 12, 0),
        status="publish",
        featured_media_id=456,
    )

    panel.show_posts((post,))
    panel.posts_list.setCurrentRow(0)

    panel.featured_media_checkbox.setChecked(True)
    panel.featured_media_input.setValue(0)

    with qtbot.waitSignal(
        panel.save_with_media_requested,
        timeout=1000,
    ) as signal:
        panel.save_button.click()

    assert signal.args == [
        "123",
        "Original content",
        None,
        0,
    ]

def test_browse_media_button_enabled_for_selected_post(qtbot):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    assert not panel.browse_media_button.isEnabled()

    post = RemotePost(
        remote_id="123",
        destination=PublishingDestination.WORDPRESS,
        content="Original content",
        published_at=datetime(2026, 10, 15, 12, 0),
        status="publish",
        featured_media_id=456,
    )

    panel.show_posts((post,))
    panel.posts_list.setCurrentRow(0)

    assert panel.browse_media_button.isEnabled()

    with qtbot.waitSignal(
        panel.browse_media_requested,
        timeout=1000,
    ):
        panel.browse_media_button.click()


def test_applying_selected_media_enables_save(qtbot):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    post = RemotePost(
        remote_id="123",
        destination=PublishingDestination.WORDPRESS,
        content="Original content",
        published_at=datetime(2026, 10, 15, 12, 0),
        status="publish",
        featured_media_id=456,
    )

    panel.show_posts((post,))
    panel.posts_list.setCurrentRow(0)

    panel.apply_selected_media(789)

    assert panel.featured_media_checkbox.isChecked()
    assert panel.featured_media_input.value() == 789
    assert panel.save_button.isEnabled()

    with qtbot.waitSignal(
        panel.save_with_media_requested,
        timeout=1000,
    ) as signal:
        panel.save_button.click()

    assert signal.args == [
        "123",
        "Original content",
        None,
        789,
    ]

    assert not panel.browse_media_button.isEnabled()


@pytest.mark.parametrize(
    "media_id",
    [0, -1, True, False, "123", 1.5],
)
def test_applying_invalid_media_id_is_rejected(qtbot, media_id):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    post = RemotePost(
        remote_id="123",
        destination=PublishingDestination.WORDPRESS,
        content="Original content",
        published_at=datetime(2026, 10, 15, 12, 0),
        status="publish",
        featured_media_id=456,
    )

    panel.show_posts((post,))
    panel.posts_list.setCurrentRow(0)

    with pytest.raises(ValueError, match="positive integer"):
        panel.apply_selected_media(media_id)

    assert panel.featured_media_input.value() == 456
    assert not panel.featured_media_checkbox.isChecked()
    assert not panel.save_button.isEnabled()

def test_content_only_save_omits_unchanged_featured_media(qtbot):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    post = RemotePost(
        remote_id="123",
        destination=PublishingDestination.WORDPRESS,
        content="Original content",
        published_at=datetime(2026, 10, 15, 12, 0),
        status="publish",
        featured_media_id=456,
    )

    panel.show_posts((post,))
    panel.posts_list.setCurrentRow(0)

    panel.featured_media_checkbox.setChecked(True)
    panel.featured_media_input.setValue(456)
    panel.content_editor.setPlainText("Updated content")

    assert panel.save_button.isEnabled()

    with qtbot.waitSignal(
        panel.save_requested,
        timeout=1000,
    ) as signal:
        panel.save_button.click()

    assert signal.args == [
        "123",
        "Updated content",
    ]


def test_failed_save_preserves_featured_media_change(qtbot):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    post = RemotePost(
        remote_id="123",
        destination=PublishingDestination.WORDPRESS,
        content="Original content",
        published_at=datetime(2026, 10, 15, 12, 0),
        status="publish",
        featured_media_id=456,
    )

    panel.show_posts((post,))
    panel.posts_list.setCurrentRow(0)

    panel.apply_selected_media(789)

    with qtbot.waitSignal(
        panel.save_with_media_requested,
        timeout=1000,
    ):
        panel.save_button.click()

    assert not panel.save_button.isEnabled()

    panel.restore_editing()

    assert panel.featured_media_checkbox.isChecked()
    assert panel.featured_media_input.value() == 789
    assert panel.featured_media_input.isEnabled()
    assert panel.save_button.isEnabled()