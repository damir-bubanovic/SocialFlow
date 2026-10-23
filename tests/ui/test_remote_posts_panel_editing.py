from datetime import datetime, timezone
import pytest
from PySide6.QtCore import Qt
from unittest.mock import Mock

from socialflow.ui.posts.posts_page import PostsPage

from socialflow.domain.post.remote_post import RemotePost
from socialflow.domain.publishing.destination import (
    PublishingDestination,
)
from socialflow.ui.posts.remote_posts_panel import RemotePostsPanel


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
    """Selecting a post displays its existing editable tag IDs."""
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

    assert panel.tags_editor.isEnabled()
    assert not panel.tags_editor.isReadOnly()
    assert panel.tags_editor.text() == "12, 34"
    assert not panel.save_button.isEnabled()



def test_loading_clears_displayed_tag_ids(qtbot):
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

    assert panel.tags_editor.text() == "12, 34"

    panel.show_loading()

    assert panel.tags_editor.text() == ""
    assert not panel.tags_editor.isEnabled()


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("12, 34", (12, 34)),
        ("12", (12,)),
        (" 12 , 34 ", (12, 34)),
        ("", ()),
        ("   ", ()),
    ],
)
def test_parses_wordpress_tag_ids(text, expected):
    assert RemotePostsPanel._parse_tag_ids(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "0",
        "-1",
        "12, 0",
        "12, -3",
        "12, abc",
        "12.5",
        "12,",
        ",12",
        "12,,34",
        "True",
    ],
)
def test_rejects_invalid_wordpress_tag_ids(text):
    with pytest.raises(
        ValueError,
        match="WordPress tag IDs must be positive integers",
    ):
        RemotePostsPanel._parse_tag_ids(text)


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

    panel.tags_editor.setText("12, 56")

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

    panel.tags_editor.clear()

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

    panel.tags_editor.setText("12, invalid")

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
    panel.tags_editor.setText("12, 56")

    panel.save_button.click()

    assert not panel.content_editor.isEnabled()
    assert not panel.tags_editor.isEnabled()

    panel.restore_editing()

    assert panel.content_editor.isEnabled()
    assert panel.tags_editor.isEnabled()
    assert panel.tags_editor.text() == "12, 56"
    assert panel.save_button.isEnabled()


def test_successful_remote_post_update_refreshes_posts():
    """A completed successful update reloads remote posts."""
    page = Mock()
    account = Mock()

    page._remote_post_updating_shutting_down = False
    page._remote_post_updating_account = account
    page._loaded_remote_posts_account = account
    page._remote_post_update_succeeded = True

    PostsPage._on_remote_post_update_finished(page)

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
    page._remote_post_updating_account = account
    page._loaded_remote_posts_account = account
    page._remote_post_update_succeeded = False

    PostsPage._on_remote_post_update_finished(page)

    assert page._remote_post_updating_account is None
    assert page._remote_post_update_succeeded is False

    page._refresh_remote_posts.assert_not_called()
    page.remote_posts_panel.restore_editing.assert_called_once_with()
