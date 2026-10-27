from datetime import datetime, timezone

from socialflow.domain.post.remote_post import RemotePost
from socialflow.domain.publishing.destination import (
    PublishingDestination,
)
from socialflow.ui.posts.remote_trashed_posts_panel import (
    RemoteTrashedPostsPanel,
)


def make_post(
    remote_id: str = "42",
    title: str = "Trashed article",
) -> RemotePost:
    return RemotePost(
        remote_id=remote_id,
        destination=PublishingDestination.WORDPRESS,
        content="Post content",
        published_at=datetime.now(timezone.utc),
        status="trash",
        title=title,
    )


def test_panel_starts_without_a_selected_account(qtbot):
    panel = RemoteTrashedPostsPanel()
    qtbot.addWidget(panel)

    assert not panel.refresh_button.isEnabled()
    assert not panel.restore_button.isEnabled()
    assert panel.selected_post() is None


def test_panel_displays_trashed_posts(qtbot):
    panel = RemoteTrashedPostsPanel()
    qtbot.addWidget(panel)

    post = make_post()
    panel.show_posts((post,))

    assert panel.posts_list.count() == 1
    assert "Trashed article" in panel.posts_list.item(0).text()
    assert panel.refresh_button.isEnabled()
    assert not panel.restore_button.isEnabled()

    panel.posts_list.setCurrentRow(0)

    assert panel.selected_post() == post
    assert panel.restore_button.isEnabled()


def test_panel_emits_restore_request_for_selected_post(qtbot):
    panel = RemoteTrashedPostsPanel()
    qtbot.addWidget(panel)

    panel.show_posts((make_post(),))
    panel.posts_list.setCurrentRow(0)

    with qtbot.waitSignal(
        panel.restore_requested,
        timeout=1000,
    ) as signal:
        panel.restore_button.click()

    assert signal.args == ["42"]


def test_panel_does_not_restore_without_selection(qtbot):
    panel = RemoteTrashedPostsPanel()
    qtbot.addWidget(panel)

    panel.show_posts((make_post(),))

    assert not panel.restore_button.isEnabled()
    assert panel.selected_post() is None


def test_loading_clears_stale_selection(qtbot):
    panel = RemoteTrashedPostsPanel()
    qtbot.addWidget(panel)

    panel.show_posts((make_post(),))
    panel.posts_list.setCurrentRow(0)

    panel.show_loading()

    assert panel.posts_list.count() == 0
    assert panel.selected_post() is None
    assert not panel.restore_button.isEnabled()
    assert not panel.refresh_button.isEnabled()


def test_empty_trash_allows_refresh(qtbot):
    panel = RemoteTrashedPostsPanel()
    qtbot.addWidget(panel)

    panel.show_posts(())

    assert panel.posts_list.count() == 0
    assert panel.refresh_button.isEnabled()
    assert not panel.restore_button.isEnabled()
    assert "empty" in panel.status_label.text().lower()


def test_error_allows_retry(qtbot):
    panel = RemoteTrashedPostsPanel()
    qtbot.addWidget(panel)

    panel.show_error("Access denied")

    assert "Access denied" in panel.status_label.text()
    assert panel.refresh_button.isEnabled()
    assert not panel.restore_button.isEnabled()


def test_restore_busy_state_disables_actions(qtbot):
    panel = RemoteTrashedPostsPanel()
    qtbot.addWidget(panel)

    panel.show_posts((make_post(),))
    panel.posts_list.setCurrentRow(0)

    panel.set_restoring(True)

    assert not panel.refresh_button.isEnabled()
    assert not panel.restore_button.isEnabled()
    assert not panel.posts_list.isEnabled()

    panel.set_restoring(False)

    assert panel.refresh_button.isEnabled()
    assert panel.restore_button.isEnabled()
    assert panel.posts_list.isEnabled()


def test_refresh_button_emits_request(qtbot):
    panel = RemoteTrashedPostsPanel()
    qtbot.addWidget(panel)

    panel.show_posts(())

    with qtbot.waitSignal(
        panel.refresh_requested,
        timeout=1000,
    ):
        panel.refresh_button.click()


def test_show_empty_clears_previous_posts(qtbot):
    panel = RemoteTrashedPostsPanel()
    qtbot.addWidget(panel)

    panel.show_posts((make_post(),))
    panel.posts_list.setCurrentRow(0)

    panel.show_empty()

    assert panel.posts_list.count() == 0
    assert panel.selected_post() is None
    assert not panel.refresh_button.isEnabled()
    assert not panel.restore_button.isEnabled()


def test_untitled_post_uses_fallback_label(qtbot):
    panel = RemoteTrashedPostsPanel()
    qtbot.addWidget(panel)

    panel.show_posts((make_post(title=""),))

    assert "(Untitled)" in panel.posts_list.item(0).text()