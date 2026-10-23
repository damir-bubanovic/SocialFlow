from datetime import datetime

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

