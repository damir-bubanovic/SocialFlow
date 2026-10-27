
from unittest.mock import Mock, patch

import pytest
from PySide6.QtWidgets import QMessageBox

from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.ui.posts.posts_page import PostsPage


def make_trash_page():
    """Build an isolated page with a selected WordPress post."""
    page = Mock()

    account = Mock()
    account.destination = PublishingDestination.WORDPRESS

    post = Mock()
    post.remote_id = "42"
    post.title = "Example WordPress post"

    trash_controller = Mock()
    trash_controller.is_running = False

    update_controller = Mock()
    update_controller.is_running = False

    page._remote_post_trashing_controller = trash_controller
    page._remote_post_updating_controller = update_controller
    page._remote_post_trashing_shutting_down = False
    page._remote_post_trashing_account = None
    page._remote_post_trashing_generation = None
    page._remote_post_trashing_succeeded = False

    page._remote_posts_generation = 3
    page._loaded_remote_posts_account = account
    page._loaded_remote_posts = (post,)

    # noinspection PyProtectedMember
    page._selected_wordpress_account.return_value = account
    page.remote_posts_panel.posts_list.currentRow.return_value = 0

    return page, trash_controller, update_controller, account


@pytest.mark.parametrize(
    "answer",
    [
        QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.Cancel,
    ],
)
def test_trash_confirmation_rejected_does_not_start(answer):
    page, controller, _, _ = make_trash_page()

    with patch(
        "socialflow.ui.posts.posts_page.QMessageBox.question",
        return_value=answer,
    ):
        PostsPage._handle_remote_post_trash(page, "42")

    controller.start.assert_not_called()
    page.remote_posts_panel.set_trashing.assert_not_called()


def test_trash_confirmation_starts_selected_post():
    page, controller, _, account = make_trash_page()

    with patch(
        "socialflow.ui.posts.posts_page.QMessageBox.question",
        return_value=QMessageBox.StandardButton.Yes,
    ) as confirmation:
        PostsPage._handle_remote_post_trash(page, "42")

    controller.start.assert_called_once_with(
        account=account,
        post_id=42,
    )
    page.remote_posts_panel.set_trashing.assert_called_once_with(True)

    assert page._remote_post_trashing_account is account
    assert page._remote_post_trashing_generation == 3
    assert page._remote_post_trashing_succeeded is False

    assert "does not permanently delete" in confirmation.call_args.args[2]


@pytest.mark.parametrize(
    "remote_id",
    ["41", "invalid", "0", "-1"],
)
def test_trash_rejects_invalid_or_mismatched_post(remote_id):
    page, controller, _, _ = make_trash_page()

    with patch(
        "socialflow.ui.posts.posts_page.QMessageBox.question",
    ) as confirmation:
        PostsPage._handle_remote_post_trash(page, remote_id)

    confirmation.assert_not_called()
    controller.start.assert_not_called()


def test_trash_rejects_other_selected_account():
    page, controller, _, _ = make_trash_page()

    page._selected_wordpress_account.return_value = Mock()

    with patch(
        "socialflow.ui.posts.posts_page.QMessageBox.question",
    ) as confirmation:
        PostsPage._handle_remote_post_trash(page, "42")

    confirmation.assert_not_called()
    controller.start.assert_not_called()


@pytest.mark.parametrize(
    "running_controller",
    ["trash", "update"],
)
def test_trash_cannot_start_during_conflicting_operation(
    running_controller,
):
    page, trash_controller, update_controller, _ = make_trash_page()

    if running_controller == "trash":
        trash_controller.is_running = True
    else:
        update_controller.is_running = True

    with patch(
        "socialflow.ui.posts.posts_page.QMessageBox.question",
    ) as confirmation:
        PostsPage._handle_remote_post_trash(page, "42")

    confirmation.assert_not_called()
    trash_controller.start.assert_not_called()


def test_trash_revalidates_selection_after_confirmation():
    page, controller, _, _ = make_trash_page()

    def change_selection(*_args, **_kwargs):
        page.remote_posts_panel.posts_list.currentRow.return_value = 1
        return QMessageBox.StandardButton.Yes

    with patch(
        "socialflow.ui.posts.posts_page.QMessageBox.question",
        side_effect=change_selection,
    ):
        PostsPage._handle_remote_post_trash(page, "42")

    controller.start.assert_not_called()
    page.remote_posts_panel.set_trashing.assert_not_called()


def test_successful_trash_refreshes_remote_posts():
    page, _, _, account = make_trash_page()

    page._remote_post_trashing_account = account
    page._remote_post_trashing_generation = 3

    PostsPage._on_remote_post_trashed(page)

    assert page._remote_post_trashing_succeeded is True

    PostsPage._on_remote_post_trash_finished(page)

    page._refresh_remote_posts.assert_called_once_with()
    page.remote_posts_panel.restore_editing.assert_not_called()

    assert page._remote_post_trashing_account is None
    assert page._remote_post_trashing_generation is None
    assert page._remote_post_trashing_succeeded is False


def test_failed_trash_restores_editing_without_refresh():
    page, _, _, account = make_trash_page()

    page._remote_post_trashing_account = account
    page._remote_post_trashing_generation = 3

    PostsPage._on_remote_post_trash_error(page, "HTTP 403")
    PostsPage._on_remote_post_trash_finished(page)

    page.remote_posts_panel.status_label.setText.assert_called_once_with(
        "Unable to move WordPress post to Trash: HTTP 403"
    )
    page.remote_posts_panel.restore_editing.assert_called_once_with()
    page._refresh_remote_posts.assert_not_called()


def test_trash_completion_ignores_stale_account():
    page, _, _, account = make_trash_page()

    page._remote_post_trashing_account = account
    page._remote_post_trashing_generation = 3
    page._remote_post_trashing_succeeded = True
    page._loaded_remote_posts_account = Mock()

    PostsPage._on_remote_post_trash_finished(page)

    page._refresh_remote_posts.assert_not_called()
    page.remote_posts_panel.restore_editing.assert_not_called()


def test_trash_completion_ignores_stale_generation():
    page, _, _, account = make_trash_page()

    page._remote_post_trashing_account = account
    page._remote_post_trashing_generation = 2
    page._remote_post_trashing_succeeded = True

    PostsPage._on_remote_post_trash_finished(page)

    page._refresh_remote_posts.assert_not_called()
    page.remote_posts_panel.restore_editing.assert_not_called()


def test_trash_callbacks_ignored_during_shutdown():
    page, _, _, account = make_trash_page()

    page._remote_post_trashing_shutting_down = True
    page._remote_post_trashing_account = account
    page._remote_post_trashing_generation = 3

    PostsPage._on_remote_post_trashed(page)
    PostsPage._on_remote_post_trash_error(page, "HTTP 500")
    PostsPage._on_remote_post_trash_finished(page)

    assert page._remote_post_trashing_succeeded is False
    page._refresh_remote_posts.assert_not_called()
    page.remote_posts_panel.restore_editing.assert_not_called()
    page.remote_posts_panel.status_label.setText.assert_not_called()



def test_save_during_trash_does_not_restore_editing():
    """A rejected Save must not unlock an active Trash operation."""
    page, trash_controller, update_controller, _ = (
        make_trash_page()
    )

    trash_controller.is_running = True

    PostsPage._handle_remote_post_save(
        page,
        "42",
        "Updated WordPress content",
    )

    update_controller.start.assert_not_called()
    page.remote_posts_panel.restore_editing.assert_not_called()
    page.remote_posts_panel.save_button.setEnabled.assert_not_called()
    page.remote_posts_panel.content_editor.setEnabled.assert_not_called()


def test_trash_error_ignored_after_account_switch():
    page, _, _, account = make_trash_page()

    page._remote_post_trashing_account = account
    page._remote_post_trashing_generation = 3

    # The user selected a different WordPress account.
    page._loaded_remote_posts_account = Mock()

    PostsPage._on_remote_post_trash_error(
        page,
        "HTTP 403",
    )

    page.remote_posts_panel.status_label.setText.assert_not_called()


def test_successful_trash_refreshes_both_post_lists():
    page, _, _, account = make_trash_page()

    page._remote_post_trashing_account = account
    page._remote_post_trashing_generation = 3
    page._remote_post_trashing_succeeded = True

    PostsPage._on_remote_post_trash_finished(page)

    page._refresh_remote_posts.assert_called_once_with()
    page._refresh_trashed_posts.assert_called_once_with()
    page.remote_posts_panel.restore_editing.assert_not_called()