from datetime import datetime, timezone
from PySide6.QtCore import Qt
from unittest.mock import Mock

from socialflow.ui.posts.posts_page import PostsPage

from socialflow.domain.post.remote_post import RemotePost
from socialflow.domain.publishing.destination import (
    PublishingDestination,
)
from socialflow.ui.posts.remote_posts_panel import RemotePostsPanel
from socialflow.domain.post.remote_tag import RemoteTag


def make_post(
    remote_id="123",
    content="Original content",
):
    return RemotePost(
        remote_id=remote_id,
        destination=PublishingDestination.WORDPRESS,
        content=content,
        published_at=datetime(
            2026, 10, 15, tzinfo=timezone.utc
        ),
        status="publish",
    )


def test_editor_is_disabled_without_selected_post(qtbot):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    assert not panel.content_editor.isEnabled()
    assert not panel.save_button.isEnabled()


def test_selecting_post_loads_its_content(qtbot):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    panel.show_posts((make_post(),))
    panel.posts_list.setCurrentRow(0)

    assert panel.content_editor.isEnabled()
    assert panel.content_editor.toPlainText() == "Original content"
    assert not panel.save_button.isEnabled()


def test_editing_content_enables_save_button(qtbot):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    panel.show_posts((make_post(),))
    panel.posts_list.setCurrentRow(0)

    panel.content_editor.setPlainText(
        "Ažurirani sadržaj čćžšđ"
    )

    assert panel.save_button.isEnabled()


def test_unchanged_or_empty_content_cannot_be_saved(qtbot):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    panel.show_posts((make_post(),))
    panel.posts_list.setCurrentRow(0)

    assert not panel.save_button.isEnabled()

    panel.content_editor.setPlainText("   ")
    assert not panel.save_button.isEnabled()

    panel.content_editor.setPlainText("Original content")
    assert not panel.save_button.isEnabled()


def test_save_emits_post_id_and_updated_content(qtbot):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)
    panel.show()

    panel.show_posts((make_post(),))
    panel.posts_list.setCurrentRow(0)

    panel.content_editor.setPlainText(
        "Ažurirani sadržaj čćžšđ"
    )

    with qtbot.waitSignal(
        panel.save_requested,
        timeout=1000,
    ) as signal:
        qtbot.mouseClick(
            panel.save_button,
            Qt.MouseButton.LeftButton,
        )

    assert signal.args == [
        "123",
        "Ažurirani sadržaj čćžšđ",
    ]


def test_loading_resets_editor_and_selection(qtbot):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    panel.show_posts((make_post(),))
    panel.posts_list.setCurrentRow(0)

    panel.show_loading()

    assert panel.posts_list.count() == 0
    assert not panel.content_editor.isEnabled()
    assert not panel.save_button.isEnabled()


def test_switching_posts_displays_correct_content(qtbot):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    panel.show_posts((
        make_post(remote_id="123", content="First post"),
        make_post(remote_id="456", content="Second post"),
    ))

    panel.posts_list.setCurrentRow(0)
    assert panel.content_editor.toPlainText() == "First post"

    panel.posts_list.setCurrentRow(1)
    assert panel.content_editor.toPlainText() == "Second post"
    assert not panel.save_button.isEnabled()





def test_selecting_post_displays_existing_tag_ids(qtbot):
    """Selecting a post displays its selected WordPress tags."""
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    post = RemotePost(
        remote_id="123",
        destination=PublishingDestination.WORDPRESS,
        content="Original content",
        published_at=datetime(
            2026, 10, 15, tzinfo=timezone.utc
        ),
        status="publish",
        tag_ids=(12, 34),
    )

    panel.show_posts((post,))
    panel.posts_list.setCurrentRow(0)

    assert panel.remote_tag_selector.tags_list.isEnabled()
    assert panel.remote_tag_selector.selected_ids() == (12, 34)
    assert not panel.save_button.isEnabled()



def test_loading_clears_displayed_tag_ids(qtbot):
    """Loading new posts clears the previous tag selection."""
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    post = RemotePost(
        remote_id="123",
        destination=PublishingDestination.WORDPRESS,
        content="Original content",
        published_at=datetime(
            2026, 10, 15, tzinfo=timezone.utc
        ),
        status="publish",
        tag_ids=(12, 34),
    )

    panel.show_posts((post,))
    panel.posts_list.setCurrentRow(0)

    assert panel.remote_tag_selector.selected_ids() == (12, 34)

    panel.show_loading()

    assert panel.remote_tag_selector.selected_ids() == ()
    assert not panel.remote_tag_selector.tags_list.isEnabled()
    assert not panel.save_button.isEnabled()


def test_tag_only_change_emits_tag_aware_save(qtbot):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    post = RemotePost(
        remote_id="123",
        destination=PublishingDestination.WORDPRESS,
        content="Original content",
        published_at=datetime(
            2026, 10, 15, tzinfo=timezone.utc
        ),
        status="publish",
        tag_ids=(12, 34),
    )

    panel.show_posts((post,))
    panel.posts_list.setCurrentRow(0)

    assert not panel.save_button.isEnabled()

    panel.remote_tag_selector.set_selected_ids((12, 56))
    panel._update_save_button()

    assert panel.save_button.isEnabled()

    with qtbot.waitSignal(
        panel.save_with_tags_requested,
        timeout=1000,
    ) as signal:
        panel.save_button.click()

    assert signal.args == [
        "123",
        "Original content",
        (12, 56),
    ]


def test_clearing_all_tags_emits_empty_tuple(qtbot):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    post = RemotePost(
        remote_id="123",
        destination=PublishingDestination.WORDPRESS,
        content="Original content",
        published_at=datetime(
            2026, 10, 15, tzinfo=timezone.utc
        ),
        status="publish",
        tag_ids=(12, 34),
    )

    panel.show_posts((post,))
    panel.posts_list.setCurrentRow(0)

    panel.remote_tag_selector.set_selected_ids(())
    panel._update_save_button()

    assert panel.save_button.isEnabled()

    with qtbot.waitSignal(
        panel.save_with_tags_requested,
        timeout=1000,
    ) as signal:
        panel.save_button.click()

    assert signal.args == [
        "123",
        "Original content",
        (),
    ]



def test_invalid_tags_disable_save(qtbot):
    """An unchanged tag selection cannot trigger a save."""
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    post = RemotePost(
        remote_id="123",
        destination=PublishingDestination.WORDPRESS,
        content="Original content",
        published_at=datetime(
            2026, 10, 15, tzinfo=timezone.utc
        ),
        status="publish",
        tag_ids=(12, 34),
    )

    panel.show_posts((post,))
    panel.posts_list.setCurrentRow(0)

    panel.remote_tag_selector.set_selected_ids((34, 12))
    panel._update_save_button()

    assert panel.remote_tag_selector.selected_ids() == (34, 12)
    assert not panel.save_button.isEnabled()



def test_content_only_change_preserves_existing_tags(qtbot):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    post = RemotePost(
        remote_id="123",
        destination=PublishingDestination.WORDPRESS,
        content="Original content",
        published_at=datetime(
            2026, 10, 15, tzinfo=timezone.utc
        ),
        status="publish",
        tag_ids=(12, 34),
    )

    panel.show_posts((post,))
    panel.posts_list.setCurrentRow(0)

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


def test_failed_tag_aware_save_restores_both_editors(qtbot):
    """A failed save restores content and tag-selection controls."""
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    post = RemotePost(
        remote_id="123",
        destination=PublishingDestination.WORDPRESS,
        content="Original content",
        published_at=datetime(
            2026, 10, 15, tzinfo=timezone.utc
        ),
        status="publish",
        tag_ids=(12, 34),
    )

    panel.show_posts((post,))
    panel.posts_list.setCurrentRow(0)

    panel.remote_tag_selector.set_selected_ids((12, 56))
    panel._update_save_button()

    assert panel.save_button.isEnabled()

    panel.save_button.click()

    assert not panel.content_editor.isEnabled()
    assert not panel.remote_tag_selector.tags_list.isEnabled()
    assert not panel.save_button.isEnabled()

    panel.restore_editing()

    assert panel.content_editor.isEnabled()
    assert panel.remote_tag_selector.tags_list.isEnabled()
    assert panel.remote_tag_selector.selected_ids() == (12, 56)
    assert panel.save_button.isEnabled()



def test_successful_remote_post_update_refreshes_posts():
    """A completed successful update reloads remote posts."""
    page = Mock()
    account = Mock()

    page._remote_post_updating_shutting_down = False
    page._remote_posts_generation = 1
    page._remote_post_updating_generation = 1
    page._remote_post_updating_account = account
    page._loaded_remote_posts_account = account
    page._remote_post_update_succeeded = True

    PostsPage._on_remote_post_update_finished(page)

    assert page._remote_post_updating_generation is None
    assert page._remote_post_updating_account is None
    assert page._remote_post_update_succeeded is False

    page.remote_posts_panel.status_label.setText.assert_called_once_with(
        "WordPress post updated successfully."
    )
    page._refresh_remote_posts.assert_called_once_with()
    page.remote_posts_panel.restore_editing.assert_not_called()


def test_failed_remote_post_update_restores_editing():
    """A failed update keeps the remote post editable."""
    page = Mock()
    account = Mock()

    page._remote_post_updating_shutting_down = False
    page._remote_posts_generation = 1
    page._remote_post_updating_generation = 1
    page._remote_post_updating_account = account
    page._loaded_remote_posts_account = account
    page._remote_post_update_succeeded = False

    PostsPage._on_remote_post_update_finished(page)

    assert page._remote_post_updating_generation is None
    assert page._remote_post_updating_account is None
    assert page._remote_post_update_succeeded is False

    page._refresh_remote_posts.assert_not_called()
    page.remote_posts_panel.restore_editing.assert_called_once_with()


def test_checking_remote_tag_enables_save(qtbot):
    """Checking a tag enables saving and preserves WordPress IDs."""
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    panel.set_available_remote_tags((
        RemoteTag(remote_id=12, name="Python"),
        RemoteTag(remote_id=34, name="News"),
    ))

    post = RemotePost(
        remote_id="123",
        destination=PublishingDestination.WORDPRESS,
        content="Original content",
        published_at=datetime(
            2026, 10, 15, tzinfo=timezone.utc
        ),
        status="publish",
        tag_ids=(12,),
    )

    panel.show_posts((post,))
    panel.posts_list.setCurrentRow(0)

    assert not panel.save_button.isEnabled()

    item = panel.remote_tag_selector.tags_list.item(1)
    item.setCheckState(Qt.CheckState.Checked)

    assert panel.remote_tag_selector.selected_ids() == (12, 34)
    assert panel.save_button.isEnabled()

    with qtbot.waitSignal(
        panel.save_with_tags_requested,
        timeout=1000,
    ) as signal:
        panel.save_button.click()

    assert signal.args == [
        "123",
        "Original content",
        (12, 34),
    ]


def test_unchecking_remote_tag_enables_save(qtbot):
    """Unchecking a tag removes its WordPress ID from the save."""
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    panel.set_available_remote_tags((
        RemoteTag(remote_id=12, name="Python"),
        RemoteTag(remote_id=34, name="News"),
    ))

    post = RemotePost(
        remote_id="123",
        destination=PublishingDestination.WORDPRESS,
        content="Original content",
        published_at=datetime(
            2026, 10, 15, tzinfo=timezone.utc
        ),
        status="publish",
        tag_ids=(12, 34),
    )

    panel.show_posts((post,))
    panel.posts_list.setCurrentRow(0)

    item = panel.remote_tag_selector.tags_list.item(1)
    item.setCheckState(Qt.CheckState.Unchecked)

    assert panel.remote_tag_selector.selected_ids() == (12,)
    assert panel.save_button.isEnabled()

    with qtbot.waitSignal(
        panel.save_with_tags_requested,
        timeout=1000,
    ) as signal:
        panel.save_button.click()

    assert signal.args == [
        "123",
        "Original content",
        (12,),
    ]


def test_unchecking_all_remote_tags_emits_empty_tuple(qtbot):
    """Removing every selected tag submits an empty tuple."""
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    panel.set_available_remote_tags((
        RemoteTag(remote_id=12, name="Python"),
        RemoteTag(remote_id=34, name="News"),
    ))

    post = RemotePost(
        remote_id="123",
        destination=PublishingDestination.WORDPRESS,
        content="Original content",
        published_at=datetime(
            2026, 10, 15, tzinfo=timezone.utc
        ),
        status="publish",
        tag_ids=(12, 34),
    )

    panel.show_posts((post,))
    panel.posts_list.setCurrentRow(0)

    for index in range(panel.remote_tag_selector.tags_list.count()):
        panel.remote_tag_selector.tags_list.item(index).setCheckState(
            Qt.CheckState.Unchecked
        )

    assert panel.remote_tag_selector.selected_ids() == ()
    assert panel.save_button.isEnabled()

    with qtbot.waitSignal(
        panel.save_with_tags_requested,
        timeout=1000,
    ) as signal:
        panel.save_button.click()

    assert signal.args == [
        "123",
        "Original content",
        (),
    ]


def test_restoring_original_tag_selection_disables_save(qtbot):
    """Reversing a tag change disables Save when content is unchanged."""
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    panel.set_available_remote_tags((
        RemoteTag(remote_id=12, name="Python"),
        RemoteTag(remote_id=34, name="News"),
    ))

    post = RemotePost(
        remote_id="123",
        destination=PublishingDestination.WORDPRESS,
        content="Original content",
        published_at=datetime(
            2026, 10, 15, tzinfo=timezone.utc
        ),
        status="publish",
        tag_ids=(12,),
    )

    panel.show_posts((post,))
    panel.posts_list.setCurrentRow(0)

    item = panel.remote_tag_selector.tags_list.item(1)

    item.setCheckState(Qt.CheckState.Checked)
    assert panel.save_button.isEnabled()

    item.setCheckState(Qt.CheckState.Unchecked)

    assert panel.remote_tag_selector.selected_ids() == (12,)
    assert not panel.save_button.isEnabled()


def test_unknown_existing_tag_can_be_removed(qtbot):
    """A tag missing from the WordPress catalog can still be removed."""
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    panel.set_available_remote_tags((
        RemoteTag(remote_id=12, name="Python"),
    ))

    post = RemotePost(
        remote_id="123",
        destination=PublishingDestination.WORDPRESS,
        content="Original content",
        published_at=datetime(
            2026, 10, 15, tzinfo=timezone.utc
        ),
        status="publish",
        tag_ids=(12, 99),
    )

    panel.show_posts((post,))
    panel.posts_list.setCurrentRow(0)

    unknown_item = panel.remote_tag_selector.tags_list.item(1)

    assert unknown_item.text() == (
        "Unknown WordPress tag (ID 99)"
    )

    unknown_item.setCheckState(Qt.CheckState.Unchecked)

    assert panel.remote_tag_selector.selected_ids() == (12,)
    assert panel.save_button.isEnabled()

    with qtbot.waitSignal(
        panel.save_with_tags_requested,
        timeout=1000,
    ) as signal:
        panel.save_button.click()

    assert signal.args == [
        "123",
        "Original content",
        (12,),
    ]


def test_late_remote_tag_loading_preserves_selected_ids(qtbot):
    """Loading tag names later preserves the post's assigned IDs."""
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    post = RemotePost(
        remote_id="123",
        destination=PublishingDestination.WORDPRESS,
        content="Original content",
        published_at=datetime(
            2026, 10, 15, tzinfo=timezone.utc
        ),
        status="publish",
        tag_ids=(12, 34),
    )

    panel.show_posts((post,))
    panel.posts_list.setCurrentRow(0)

    assert panel.remote_tag_selector.selected_ids() == (12, 34)
    assert not panel.save_button.isEnabled()

    panel.set_available_remote_tags((
        RemoteTag(remote_id=12, name="Python"),
        RemoteTag(remote_id=34, name="Tutorials"),
        RemoteTag(remote_id=56, name="News"),
    ))

    selector = panel.remote_tag_selector

    assert selector.selected_ids() == (12, 34)
    assert selector.tags_list.count() == 3

    assert selector.tags_list.item(0).text() == "Python"
    assert selector.tags_list.item(1).text() == "Tutorials"
    assert selector.tags_list.item(2).text() == "News"

    assert selector.tags_list.item(0).checkState() == (
        Qt.CheckState.Checked
    )
    assert selector.tags_list.item(1).checkState() == (
        Qt.CheckState.Checked
    )
    assert selector.tags_list.item(2).checkState() == (
        Qt.CheckState.Unchecked
    )

    assert not panel.save_button.isEnabled()


def test_missing_tag_catalog_preserves_editable_existing_tags(qtbot):
    """Unavailable tag names do not prevent editing existing IDs."""
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    post = RemotePost(
        remote_id="123",
        destination=PublishingDestination.WORDPRESS,
        content="Original content",
        published_at=datetime(
            2026, 10, 15, tzinfo=timezone.utc
        ),
        status="publish",
        tag_ids=(12, 34),
    )

    panel.show_posts((post,))
    panel.posts_list.setCurrentRow(0)

    panel.set_available_remote_tags(())

    selector = panel.remote_tag_selector

    assert selector.selected_ids() == (12, 34)
    assert selector.tags_list.isEnabled()
    assert selector.tags_list.count() == 2
    assert selector.tags_list.item(0).text() == (
        "Unknown WordPress tag (ID 12)"
    )
    assert selector.tags_list.item(1).text() == (
        "Unknown WordPress tag (ID 34)"
    )

    selector.tags_list.item(1).setCheckState(
        Qt.CheckState.Unchecked
    )

    assert selector.selected_ids() == (12,)
    assert panel.save_button.isEnabled()

    with qtbot.waitSignal(
        panel.save_with_tags_requested,
        timeout=1000,
    ) as signal:
        panel.save_button.click()

    assert signal.args == [
        "123",
        "Original content",
        (12,),
    ]

def test_save_locks_remote_post_selection(qtbot):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    panel.show_posts((
        make_post(remote_id="123"),
        make_post(remote_id="456"),
    ))
    panel.posts_list.setCurrentRow(0)
    panel.content_editor.setPlainText("Updated content")

    with qtbot.waitSignal(panel.save_requested, timeout=1000):
        panel.save_button.click()

    assert not panel.posts_list.isEnabled()
    assert panel.posts_list.currentRow() == 0
    assert not panel.content_editor.isEnabled()


def test_failed_save_restores_selection_and_unsaved_content(qtbot):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    panel.show_posts((
        make_post(remote_id="123"),
        make_post(remote_id="456"),
    ))
    panel.posts_list.setCurrentRow(0)
    panel.content_editor.setPlainText("Unsaved changes")

    with qtbot.waitSignal(panel.save_requested, timeout=1000):
        panel.save_button.click()

    panel.restore_editing()

    assert panel.posts_list.isEnabled()
    assert panel.posts_list.currentRow() == 0
    assert panel.content_editor.isEnabled()
    assert panel.content_editor.toPlainText() == "Unsaved changes"
    assert panel.save_button.isEnabled()


def test_failed_save_allows_selecting_another_post(qtbot):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    panel.show_posts((
        make_post(remote_id="123"),
        make_post(remote_id="456", content="Second post"),
    ))
    panel.posts_list.setCurrentRow(0)
    panel.content_editor.setPlainText("Unsaved changes")

    with qtbot.waitSignal(panel.save_requested, timeout=1000):
        panel.save_button.click()

    panel.restore_editing()
    panel.posts_list.setCurrentRow(1)

    assert panel.posts_list.currentRow() == 1
    assert panel.content_editor.toPlainText() == "Second post"
    assert not panel.save_button.isEnabled()

def test_status_save_locks_post_selection_and_restores_on_failure(qtbot):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    panel.show_posts((
        make_post(remote_id="123"),
        make_post(remote_id="456"),
    ))
    panel.posts_list.setCurrentRow(0)

    panel.post_status_selector.setCurrentIndex(
        panel.post_status_selector.findData("draft")
    )

    with qtbot.waitSignal(
        panel.save_with_status_requested,
        timeout=1000,
    ) as signal:
        panel.save_button.click()

    assert signal.args == [
        "123",
        "Original content",
        None,
        None,
        "draft",
    ]
    assert not panel.posts_list.isEnabled()
    assert panel.posts_list.currentRow() == 0

    panel.restore_editing()

    assert panel.posts_list.isEnabled()
    assert panel.post_status_selector.isEnabled()
    assert panel.post_status_selector.currentData() == "draft"
    assert panel.save_button.isEnabled()

def test_featured_image_save_locks_selection_and_restores_on_failure(
    qtbot,
):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    panel.show_posts((
        make_post(remote_id="123"),
        make_post(remote_id="456"),
    ))
    panel.posts_list.setCurrentRow(0)

    panel.featured_media_checkbox.setChecked(True)
    panel.featured_media_input.setValue(789)

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
    assert not panel.posts_list.isEnabled()
    assert panel.posts_list.currentRow() == 0

    panel.restore_editing()

    assert panel.posts_list.isEnabled()
    assert panel.featured_media_checkbox.isEnabled()
    assert panel.featured_media_input.isEnabled()
    assert panel.featured_media_input.value() == 789
    assert panel.save_button.isEnabled()

def test_successful_refresh_resets_locked_selection(qtbot):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    panel.show_posts((
        make_post(remote_id="123"),
        make_post(remote_id="456"),
    ))
    panel.posts_list.setCurrentRow(0)
    panel.content_editor.setPlainText("Updated content")

    with qtbot.waitSignal(
        panel.save_requested,
        timeout=1000,
    ):
        panel.save_button.click()

    assert not panel.posts_list.isEnabled()

    panel.show_loading()

    assert panel.posts_list.count() == 0
    assert panel.posts_list.isEnabled()
    assert panel.posts_list.currentRow() == -1
    assert not panel.save_button.isEnabled()

    panel.show_posts((
        make_post(remote_id="123", content="Updated content"),
        make_post(remote_id="456"),
    ))

    assert panel.posts_list.isEnabled()
    assert panel.posts_list.count() == 2
    assert panel.posts_list.currentRow() == -1
    assert not panel.save_button.isEnabled()

    panel.posts_list.setCurrentRow(0)

    assert panel.content_editor.toPlainText() == "Updated content"
    assert not panel.save_button.isEnabled()

def test_account_switch_clears_locked_remote_post_selection(qtbot):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    panel.show_posts((
        make_post(remote_id="123"),
        make_post(remote_id="456"),
    ))
    panel.posts_list.setCurrentRow(0)
    panel.content_editor.setPlainText("Unsaved changes")

    with qtbot.waitSignal(panel.save_requested, timeout=1000):
        panel.save_button.click()

    assert not panel.posts_list.isEnabled()

    # The account-switch path clears the previous account's posts.
    panel.show_empty()

    assert panel.posts_list.count() == 0
    assert panel.posts_list.currentRow() == -1
    assert panel.posts_list.isEnabled()
    assert panel.content_editor.toPlainText() == ""
    assert not panel.content_editor.isEnabled()
    assert not panel.save_button.isEnabled()

def test_new_account_posts_are_selectable_after_locked_save(qtbot):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    panel.show_posts((
        make_post(remote_id="123", content="First account post"),
    ))
    panel.posts_list.setCurrentRow(0)
    panel.content_editor.setPlainText("Unsaved first account changes")

    with qtbot.waitSignal(panel.save_requested, timeout=1000):
        panel.save_button.click()

    assert not panel.posts_list.isEnabled()

    panel.show_loading()
    panel.show_posts((
        make_post(remote_id="456", content="Second account post"),
    ))

    assert panel.posts_list.isEnabled()
    assert panel.posts_list.count() == 1
    assert panel.posts_list.currentRow() == -1

    panel.posts_list.setCurrentRow(0)

    assert panel.content_editor.toPlainText() == "Second account post"
    assert panel.content_editor.isEnabled()
    assert not panel.save_button.isEnabled()

def test_loading_error_clears_locked_remote_post_editor(qtbot):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    panel.show_posts((
        make_post(remote_id="123"),
    ))
    panel.posts_list.setCurrentRow(0)
    panel.content_editor.setPlainText("Unsaved changes")

    with qtbot.waitSignal(panel.save_requested, timeout=1000):
        panel.save_button.click()

    assert not panel.posts_list.isEnabled()

    panel.show_error("WordPress request failed")

    assert panel.posts_list.count() == 0
    assert panel.posts_list.currentRow() == -1
    assert panel.posts_list.isEnabled()
    assert panel.content_editor.toPlainText() == ""
    assert not panel.content_editor.isEnabled()
    assert not panel.save_button.isEnabled()
    assert "WordPress request failed" in panel.status_label.text()

def test_remote_post_editor_recovers_after_loading_error(qtbot):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    panel.show_error("Temporary WordPress failure")

    panel.show_loading()
    panel.show_posts((
        make_post(remote_id="456", content="Recovered post"),
    ))

    assert panel.posts_list.isEnabled()
    assert panel.posts_list.count() == 1

    panel.posts_list.setCurrentRow(0)

    assert panel.content_editor.isEnabled()
    assert panel.content_editor.toPlainText() == "Recovered post"
    assert not panel.save_button.isEnabled()

    panel.content_editor.setPlainText("Edited recovered post")

    assert panel.save_button.isEnabled()

def test_clearing_account_discards_unsaved_status_change(qtbot):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    panel.show_posts((
        make_post(remote_id="123"),
    ))
    panel.posts_list.setCurrentRow(0)

    draft_index = panel.post_status_selector.findData("draft")
    assert draft_index >= 0

    panel.post_status_selector.setCurrentIndex(draft_index)
    assert panel.save_button.isEnabled()

    panel.show_empty()

    assert panel.posts_list.count() == 0
    assert panel.posts_list.isEnabled()
    assert not panel.post_status_selector.isEnabled()
    assert not panel.save_button.isEnabled()

    panel.show_posts((
        make_post(remote_id="456"),
    ))
    panel.posts_list.setCurrentRow(0)

    assert panel.post_status_selector.currentData() == "publish"
    assert not panel.save_button.isEnabled()

def test_late_save_failure_does_not_restore_cleared_account(qtbot):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    panel.show_posts((
        make_post(remote_id="123"),
    ))
    panel.posts_list.setCurrentRow(0)
    panel.content_editor.setPlainText("Unsaved changes")

    with qtbot.waitSignal(panel.save_requested, timeout=1000):
        panel.save_button.click()

    assert not panel.posts_list.isEnabled()

    panel.show_empty()

    # Simulate a delayed failure callback from the previous save.
    panel.restore_editing()

    assert panel.posts_list.count() == 0
    assert panel.posts_list.currentRow() == -1
    assert panel.content_editor.toPlainText() == ""
    assert not panel.content_editor.isEnabled()
    assert not panel.post_status_selector.isEnabled()
    assert not panel.save_button.isEnabled()


def test_late_save_failure_does_not_restore_editor_during_loading(qtbot):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    panel.show_posts((
        make_post(remote_id="123"),
    ))
    panel.posts_list.setCurrentRow(0)
    panel.content_editor.setPlainText("Updated content")

    with qtbot.waitSignal(panel.save_requested, timeout=1000):
        panel.save_button.click()

    panel.show_loading()

    # A delayed save failure must not restore the old post.
    panel.restore_editing()

    assert panel.posts_list.count() == 0
    assert panel.posts_list.currentRow() == -1
    assert panel.content_editor.toPlainText() == ""
    assert not panel.content_editor.isEnabled()
    assert not panel.save_button.isEnabled()
    assert panel.status_label.text() == "Loading WordPress posts..."


def test_late_save_failure_does_not_restore_editor_after_load_error(qtbot):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    panel.show_posts((
        make_post(remote_id="123"),
    ))
    panel.posts_list.setCurrentRow(0)
    panel.content_editor.setPlainText("Updated content")

    with qtbot.waitSignal(panel.save_requested, timeout=1000):
        panel.save_button.click()

    panel.show_error("WordPress connection failed")

    # Simulate a delayed failure callback from the previous save.
    panel.restore_editing()

    assert panel.posts_list.count() == 0
    assert panel.posts_list.currentRow() == -1
    assert panel.content_editor.toPlainText() == ""
    assert not panel.content_editor.isEnabled()
    assert not panel.post_status_selector.isEnabled()
    assert not panel.save_button.isEnabled()
    assert "WordPress connection failed" in panel.status_label.text()