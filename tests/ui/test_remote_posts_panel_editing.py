from datetime import datetime, timezone

from PySide6.QtCore import Qt

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