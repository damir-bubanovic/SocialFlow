from unittest.mock import Mock, patch

import pytest
from PySide6.QtWidgets import QMessageBox

from socialflow.ui.posts.posts_page import PostsPage


def make_restore_page(
    remote_id="42",
    *,
    selected_account=True,
    loaded_account=True,
):
    """Build an isolated PostsPage for Restore workflow tests."""
    page = Mock()

    account = Mock()
    post = Mock()
    post.remote_id = remote_id
    post.title = "Trashed article"

    restore_controller = Mock()
    restore_controller.is_running = False

    trash_controller = Mock()
    trash_controller.is_running = False

    update_controller = Mock()
    update_controller.is_running = False

    page._remote_post_restoring_controller = restore_controller
    page._remote_post_trashing_controller = trash_controller
    page._remote_post_updating_controller = update_controller

    page._remote_post_restoring_shutting_down = False
    page._remote_post_restoring_account = None
    page._remote_post_restoring_generation = None
    page._remote_post_restoring_succeeded = False

    page._trashed_posts_generation = 3
    page._loaded_trashed_posts = (post,)
    page._loaded_trashed_posts_account = (
        account if loaded_account else None
    )

    selected_account_mock = Mock(
        return_value=account if selected_account else None
    )
    setattr(page, "_selected_wordpress_account", selected_account_mock)
    page.remote_trashed_posts_panel.selected_post.return_value = post

    return page, restore_controller, account, post


def test_restore_confirmation_defaults_to_no():
    page, controller, _, _ = make_restore_page()

    with patch(
        "socialflow.ui.posts.posts_page.QMessageBox.question",
        return_value=QMessageBox.StandardButton.No,
    ) as question:
        PostsPage._handle_remote_post_restore(page, "42")

    assert question.call_args.args[-1] == QMessageBox.StandardButton.No
    assert "Draft" in question.call_args.args[2]
    assert "not be published automatically" in question.call_args.args[2]
    controller.start.assert_not_called()


def test_confirmed_restore_starts_for_correct_account_and_post():
    page, controller, account, _ = make_restore_page()

    with patch(
        "socialflow.ui.posts.posts_page.QMessageBox.question",
        return_value=QMessageBox.StandardButton.Yes,
    ):
        PostsPage._handle_remote_post_restore(page, "42")

    controller.start.assert_called_once_with(
        account=account,
        post_id=42,
    )
    page.remote_trashed_posts_panel.set_restoring.assert_called_once_with(
        True
    )
    assert page._remote_post_restoring_account is account
    assert page._remote_post_restoring_generation == 3


@pytest.mark.parametrize(
    "remote_id",
    ["invalid", "0", "-4"],
)
def test_invalid_post_id_does_not_start_restore(remote_id):
    page, controller, _, _ = make_restore_page(remote_id)

    with patch(
        "socialflow.ui.posts.posts_page.QMessageBox.question"
    ) as question:
        PostsPage._handle_remote_post_restore(page, remote_id)

    question.assert_not_called()
    controller.start.assert_not_called()


def test_restore_rejects_mismatched_post_id():
    page, controller, _, _ = make_restore_page()

    PostsPage._handle_remote_post_restore(page, "99")

    controller.start.assert_not_called()


@pytest.mark.parametrize(
    "selected_account,loaded_account",
    [
        (False, True),
        (True, False),
    ],
)
def test_restore_requires_current_loaded_account(
    selected_account,
    loaded_account,
):
    page, controller, _, _ = make_restore_page(
        selected_account=selected_account,
        loaded_account=loaded_account,
    )

    PostsPage._handle_remote_post_restore(page, "42")

    controller.start.assert_not_called()


@pytest.mark.parametrize(
    "busy_controller",
    ["restore", "trash", "update"],
)
def test_restore_rejected_during_concurrent_operation(busy_controller):
    page, controller, _, _ = make_restore_page()

    controllers = {
        "restore": page._remote_post_restoring_controller,
        "trash": page._remote_post_trashing_controller,
        "update": page._remote_post_updating_controller,
    }
    controllers[busy_controller].is_running = True

    with patch(
        "socialflow.ui.posts.posts_page.QMessageBox.question"
    ) as question:
        PostsPage._handle_remote_post_restore(page, "42")

    question.assert_not_called()
    controller.start.assert_not_called()


def test_restore_revalidates_selection_after_confirmation():
    page, controller, _, _ = make_restore_page()

    def change_selection(*_args):
        page.remote_trashed_posts_panel.selected_post.return_value = None
        return QMessageBox.StandardButton.Yes

    with patch(
        "socialflow.ui.posts.posts_page.QMessageBox.question",
        side_effect=change_selection,
    ):
        PostsPage._handle_remote_post_restore(page, "42")

    controller.start.assert_not_called()


def test_restore_revalidates_account_after_confirmation():
    page, controller, _, _ = make_restore_page()

    def change_account(*_args):
        setattr(
            page,
            "_selected_wordpress_account",
            Mock(return_value=None),
        )
        return QMessageBox.StandardButton.Yes

    with patch(
        "socialflow.ui.posts.posts_page.QMessageBox.question",
        side_effect=change_account,
    ):
        PostsPage._handle_remote_post_restore(page, "42")

    controller.start.assert_not_called()


def test_restore_success_refreshes_both_post_lists():
    page, _, account, _ = make_restore_page()

    page._remote_post_restoring_account = account
    page._remote_post_restoring_generation = 3

    PostsPage._on_remote_post_restored(page)
    PostsPage._on_remote_post_restore_finished(page)

    page._refresh_trashed_posts.assert_called_once_with()
    page._refresh_remote_posts.assert_called_once_with()
    assert page._remote_post_restoring_account is None
    assert page._remote_post_restoring_generation is None
    assert page._remote_post_restoring_succeeded is False


def test_restore_failure_does_not_refresh_lists():
    page, _, account, _ = make_restore_page()

    page._remote_post_restoring_account = account
    page._remote_post_restoring_generation = 3

    PostsPage._on_remote_post_restore_error(
        page,
        "Permission denied",
    )
    PostsPage._on_remote_post_restore_finished(page)

    assert "Permission denied" in (
        page.remote_trashed_posts_panel.status_label.setText.call_args.args[0]
    )
    page._refresh_trashed_posts.assert_not_called()
    page._refresh_remote_posts.assert_not_called()
    page.remote_trashed_posts_panel.set_restoring.assert_called_with(False)


def test_stale_restore_completion_does_not_refresh():
    page, _, account, _ = make_restore_page()

    page._remote_post_restoring_account = account
    page._remote_post_restoring_generation = 2
    page._remote_post_restoring_succeeded = True

    PostsPage._on_remote_post_restore_finished(page)

    page._refresh_trashed_posts.assert_not_called()
    page._refresh_remote_posts.assert_not_called()
    page.remote_trashed_posts_panel.set_restoring.assert_called_with(False)


def test_restore_ignored_during_shutdown():
    page, controller, _, _ = make_restore_page()
    page._remote_post_restoring_shutting_down = True

    PostsPage._handle_remote_post_restore(page, "42")
    PostsPage._on_remote_post_restored(page)
    PostsPage._on_remote_post_restore_finished(page)

    controller.start.assert_not_called()
    assert page._remote_post_restoring_succeeded is False
    page._refresh_trashed_posts.assert_not_called()
    page._refresh_remote_posts.assert_not_called()


def test_stale_restore_completion_does_not_unlock_unloaded_trash():
    page, _, account, _ = make_restore_page()

    page._remote_post_restoring_account = account
    page._remote_post_restoring_generation = 3
    page._remote_post_restoring_succeeded = True

    # Account switching has invalidated the old Trash results.
    page._trashed_posts_generation = 4
    page._loaded_trashed_posts_account = None

    PostsPage._on_remote_post_restore_finished(page)

    page.remote_trashed_posts_panel.set_restoring.assert_not_called()
    page._refresh_trashed_posts.assert_not_called()
    page._refresh_remote_posts.assert_not_called()

    assert page._remote_post_restoring_account is None
    assert page._remote_post_restoring_generation is None
    assert page._remote_post_restoring_succeeded is False


def test_trash_loading_error_preserves_active_restore_state():
    page, restore_controller, account, _ = make_restore_page()

    page._trashed_post_loading_account = account
    page._trashed_post_loading_generation = 3
    page._pending_trashed_post_account = None
    page._remote_trashed_post_loading_shutting_down = False

    restore_controller.is_running = True

    PostsPage._on_trashed_posts_error(page, "Connection failed")

    assert page._loaded_trashed_posts == ()
    assert page._loaded_trashed_posts_account is None

    page.remote_trashed_posts_panel.show_error.assert_called_once_with(
        "Connection failed"
    )
    page.remote_trashed_posts_panel.set_restoring.assert_called_once_with(
        True
    )


def test_trash_loading_error_does_not_lock_panel_without_restore():
    page, restore_controller, account, _ = make_restore_page()

    page._trashed_post_loading_account = account
    page._trashed_post_loading_generation = 3
    page._pending_trashed_post_account = None
    page._remote_trashed_post_loading_shutting_down = False

    restore_controller.is_running = False

    PostsPage._on_trashed_posts_error(page, "Connection failed")

    page.remote_trashed_posts_panel.show_error.assert_called_once_with(
        "Connection failed"
    )
    page.remote_trashed_posts_panel.set_restoring.assert_not_called()