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
        title="Example WordPress title",
        published_at=datetime(2026, 10, 15, 12, 0),
        status="publish",
    )

    panel.show_posts((post,))

    assert panel.posts_list.count() == 1
    assert "Example WordPress title" in panel.posts_list.item(0).text()
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

@pytest.mark.parametrize(
    ("status", "expected_label"),
    (
        ("publish", "Published"),
        ("draft", "Draft"),
        ("pending", "Pending review"),
        ("private", "Private"),
    ),
)
def test_panel_loads_wordpress_post_status(
    qtbot,
    status,
    expected_label,
):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    post = RemotePost(
        remote_id="123",
        destination=PublishingDestination.WORDPRESS,
        content="Original content",
        published_at=datetime(2026, 10, 15, 12, 0),
        status=status,
    )

    panel.show_posts((post,))
    panel.posts_list.setCurrentRow(0)

    assert panel.post_status_selector.isEnabled()
    assert panel.post_status_selector.currentData() == status
    assert panel.post_status_selector.currentText() == expected_label
    assert not panel.save_button.isEnabled()


def test_panel_enables_save_when_wordpress_status_changes(qtbot):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    post = RemotePost(
        remote_id="123",
        destination=PublishingDestination.WORDPRESS,
        content="Original content",
        published_at=datetime(2026, 10, 15, 12, 0),
        status="publish",
    )

    panel.show_posts((post,))
    panel.posts_list.setCurrentRow(0)

    panel.post_status_selector.setCurrentIndex(
        panel.post_status_selector.findData("draft")
    )

    assert panel.post_status_selector.currentData() == "draft"
    assert panel.save_button.isEnabled()


def test_panel_disables_unknown_wordpress_status(qtbot):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    post = RemotePost(
        remote_id="123",
        destination=PublishingDestination.WORDPRESS,
        content="Original content",
        published_at=datetime(2026, 10, 15, 12, 0),
        status="future",
    )

    panel.show_posts((post,))
    panel.posts_list.setCurrentRow(0)

    assert not panel.post_status_selector.isEnabled()
    assert not panel.save_button.isEnabled()

@pytest.mark.parametrize(
    "status",
    ("draft", "pending", "private", "publish"),
)
def test_panel_emits_status_only_save(qtbot, status):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    initial_status = "draft" if status == "publish" else "publish"

    post = RemotePost(
        remote_id="123",
        destination=PublishingDestination.WORDPRESS,
        content="Original content",
        published_at=datetime(2026, 10, 15, 12, 0),
        status=initial_status,
    )

    panel.show_posts((post,))
    panel.posts_list.setCurrentRow(0)

    panel.post_status_selector.setCurrentIndex(
        panel.post_status_selector.findData(status)
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
        status,
    ]
    assert not panel.post_status_selector.isEnabled()
    assert not panel.save_button.isEnabled()

def test_panel_emits_status_with_content_tags_and_media(qtbot):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    post = RemotePost(
        remote_id="123",
        destination=PublishingDestination.WORDPRESS,
        content="Original content",
        published_at=datetime(2026, 10, 15, 12, 0),
        status="publish",
        tag_ids=(10,),
        featured_media_id=456,
    )

    panel.show_posts((post,))
    panel.posts_list.setCurrentRow(0)

    panel.set_available_remote_tags((
        RemoteTag(remote_id=10, name="Original"),
        RemoteTag(remote_id=20, name="Additional"),
    ))

    panel.content_editor.setPlainText("Updated content")
    panel.remote_tag_selector.tags_list.item(1).setCheckState(
        Qt.CheckState.Checked
    )
    panel.apply_selected_media(789)
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
        "Updated content",
        (10, 20),
        789,
        "draft",
    ]


def test_panel_restores_status_after_failed_save(qtbot):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    post = RemotePost(
        remote_id="123",
        destination=PublishingDestination.WORDPRESS,
        content="Original content",
        published_at=datetime(2026, 10, 15, 12, 0),
        status="publish",
    )

    panel.show_posts((post,))
    panel.posts_list.setCurrentRow(0)

    panel.post_status_selector.setCurrentIndex(
        panel.post_status_selector.findData("draft")
    )

    with qtbot.waitSignal(
        panel.save_with_status_requested,
        timeout=1000,
    ):
        panel.save_button.click()

    panel.restore_editing()

    assert panel.post_status_selector.isEnabled()
    assert panel.post_status_selector.currentData() == "draft"
    assert panel.save_button.isEnabled()



def test_my_posts_displays_selected_post_category_ids(qtbot):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    post = RemotePost(
        remote_id="123",
        destination=PublishingDestination.WORDPRESS,
        content="Example content",
        published_at=datetime(2026, 10, 31, 12, 0),
        status="publish",
        category_ids=(10, 20),
    )

    panel.show_posts((post,))
    panel.posts_list.setCurrentRow(0)

    assert panel.remote_category_selector.selected_ids() == (10, 20)
    assert not panel.remote_category_selector.isEnabled()


def test_my_posts_clears_categories_when_selection_is_removed(qtbot):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    post = RemotePost(
        remote_id="123",
        destination=PublishingDestination.WORDPRESS,
        content="Example content",
        published_at=datetime(2026, 10, 31, 12, 0),
        status="publish",
        category_ids=(10, 20),
    )

    panel.show_posts((post,))
    panel.posts_list.setCurrentRow(0)

    panel.posts_list.setCurrentRow(-1)

    assert panel.remote_category_selector.selected_ids() == ()
    assert not panel.remote_category_selector.isEnabled()


def test_my_posts_clears_categories_when_loading_new_posts(qtbot):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    post = RemotePost(
        remote_id="123",
        destination=PublishingDestination.WORDPRESS,
        content="Example content",
        published_at=datetime(2026, 10, 31, 12, 0),
        status="publish",
        category_ids=(10, 20),
    )

    panel.show_posts((post,))
    panel.posts_list.setCurrentRow(0)

    panel.show_loading()

    assert panel.remote_category_selector.selected_ids() == ()
    assert not panel.remote_category_selector.isEnabled()



def test_my_posts_category_names_preserve_selected_ids(qtbot):
    from socialflow.domain.post.remote_category import RemoteCategory

    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    panel.remote_category_selector.set_selected_ids((10, 20))

    categories = (
        RemoteCategory(10, "Technology"),
        RemoteCategory(20, "Python", parent_id=10),
    )

    panel.set_available_remote_categories(categories)

    assert (
        panel.remote_category_selector.available_categories()
        == categories
    )
    assert panel.remote_category_selector.selected_ids() == (10, 20)
    assert not panel.remote_category_selector.isEnabled()



def test_category_changes_do_not_enable_save_while_read_only(qtbot):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    post = RemotePost(
        remote_id="123",
        destination=PublishingDestination.WORDPRESS,
        content="Example content",
        published_at=datetime(2026, 10, 31, 12, 0),
        status="publish",
        category_ids=(10,),
    )

    panel.show_posts((post,))
    panel.posts_list.setCurrentRow(0)

    panel.remote_category_selector.set_selected_ids((20,))
    panel._update_save_button()

    assert not panel.remote_category_selector.isEnabled()
    assert not panel.save_button.isEnabled()


def test_category_changes_enable_save_when_editing_is_enabled(qtbot):
    panel = RemotePostsPanel()
    qtbot.addWidget(panel)

    post = RemotePost(
        remote_id="123",
        destination=PublishingDestination.WORDPRESS,
        content="Example content",
        published_at=datetime(2026, 10, 31, 12, 0),
        status="publish",
        category_ids=(10,),
    )

    panel.show_posts((post,))
    panel.posts_list.setCurrentRow(0)

    panel.remote_category_selector.setEnabled(True)
    panel.remote_category_selector.set_selected_ids((20,))
    panel._update_save_button()

    assert panel.save_button.isEnabled()

    panel.remote_category_selector.set_selected_ids((10,))
    panel._update_save_button()

    assert not panel.save_button.isEnabled()
