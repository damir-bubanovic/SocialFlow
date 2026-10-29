from datetime import datetime, timezone

import pytest

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


def test_selected_post_displays_read_only_details(qtbot):
    panel = RemoteTrashedPostsPanel()
    qtbot.addWidget(panel)

    post = RemotePost(
        remote_id="123",
        destination=PublishingDestination.WORDPRESS,
        content="This is the trashed post content.",
        published_at=datetime(
            2026, 10, 28, 14, 30, tzinfo=timezone.utc
        ),
        status="trash",
        title="My trashed article",
        tag_ids=(12, 34),
        featured_media_id=56,
    )

    panel.show_posts((post,))
    panel.posts_list.setCurrentRow(0)

    details = panel.details_text.toPlainText()

    assert "Title: My trashed article" in details
    assert "Post ID: 123" in details
    assert "Status: trash" in details
    assert "Date: 2026-10-28 14:30" in details
    assert "Tags (IDs): 12, 34" in details
    assert "Featured media ID: 56" in details
    assert "This is the trashed post content." in details
    assert panel.details_text.isReadOnly()


def test_selecting_another_post_updates_details(qtbot):
    panel = RemoteTrashedPostsPanel()
    qtbot.addWidget(panel)

    panel.show_posts((
        make_post(remote_id="1", title="First article"),
        make_post(remote_id="2", title="Second article"),
    ))

    panel.posts_list.setCurrentRow(0)
    assert "Title: First article" in panel.details_text.toPlainText()

    panel.posts_list.setCurrentRow(1)

    details = panel.details_text.toPlainText()
    assert "Title: Second article" in details
    assert "Post ID: 2" in details
    assert "First article" not in details


def test_clearing_selection_removes_post_details(qtbot):
    panel = RemoteTrashedPostsPanel()
    qtbot.addWidget(panel)

    panel.show_posts((make_post(),))
    panel.posts_list.setCurrentRow(0)

    assert panel.details_text.toPlainText()

    panel.posts_list.clearSelection()
    panel.posts_list.setCurrentRow(-1)

    assert panel.selected_post() is None
    assert panel.details_text.toPlainText() == ""
    assert not panel.restore_button.isEnabled()


@pytest.mark.parametrize(
    "reset_method",
    ["show_empty", "show_loading", "show_error"],
)
def test_reset_clears_stale_post_details(qtbot, reset_method):
    panel = RemoteTrashedPostsPanel()
    qtbot.addWidget(panel)

    panel.show_posts((make_post(),))
    panel.posts_list.setCurrentRow(0)

    assert "Trashed article" in panel.details_text.toPlainText()

    if reset_method == "show_error":
        panel.show_error("Connection failed")
    else:
        getattr(panel, reset_method)()

    assert panel.details_text.toPlainText() == ""
    assert panel.selected_post() is None
    assert not panel.restore_button.isEnabled()


def test_restoring_keeps_details_read_only_and_disables_actions(qtbot):
    panel = RemoteTrashedPostsPanel()
    qtbot.addWidget(panel)

    panel.show_posts((make_post(),))
    panel.posts_list.setCurrentRow(0)

    original_details = panel.details_text.toPlainText()

    panel.set_restoring(True)

    assert panel.details_text.isReadOnly()
    assert panel.details_text.toPlainText() == original_details
    assert not panel.restore_button.isEnabled()
    assert not panel.refresh_button.isEnabled()
    assert not panel.posts_list.isEnabled()

    panel.set_restoring(False)

    assert panel.restore_button.isEnabled()
    assert panel.refresh_button.isEnabled()
    assert panel.posts_list.isEnabled()