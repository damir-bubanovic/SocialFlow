from datetime import datetime

from socialflow.domain.post.remote_post import RemotePost
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.ui.posts.remote_posts_panel import RemotePostsPanel


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