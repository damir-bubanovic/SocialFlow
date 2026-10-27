from unittest.mock import Mock
from typing import cast

from socialflow.ui.posts.posts_page import PostsPage
from socialflow.domain.publishing.destination import PublishingDestination


def test_remote_post_save_starts_update_for_selected_post():
    """Saving must target the selected WordPress account and post."""
    page = Mock()

    controller = Mock()
    controller.is_running = False
    page._remote_post_updating_controller = controller
    page._remote_post_updating_shutting_down = False
    page._remote_post_trashing_controller = None

    account = Mock()
    account.destination = PublishingDestination.WORDPRESS

    page.post_editor.selected_accounts.return_value = (account,)
    page._loaded_remote_posts = (Mock(remote_id="42"),)
    page._loaded_remote_posts_account = account

    page.remote_posts_panel = Mock()

    PostsPage._handle_remote_post_save(
        page,
        "42",
        "Updated WordPress content",
    )

    controller.start.assert_called_once_with(
        account=account,
        post_id=42,
        content="Updated WordPress content",
    )

def test_remote_post_update_error_restores_editing():
    """A failed update must show the error and restore editing."""
    page = Mock()
    account = Mock()

    page._remote_post_updating_shutting_down = False
    page._remote_posts_generation = 1
    page._remote_post_updating_generation = 1
    page._remote_post_updating_account = account
    page._loaded_remote_posts_account = account
    page.post_editor.selected_accounts.return_value = (account,)

    PostsPage._on_remote_post_update_error(
        page,
        "HTTP 403",
    )

    page.remote_posts_panel.status_label.setText.assert_called_once_with(
        "Unable to update WordPress post: HTTP 403"
    )
    page.remote_posts_panel.restore_editing.assert_called_once_with()

def test_remote_post_update_finished_ignores_previous_account():
    """Finishing an update must not affect a different selected account."""
    page = Mock()

    original_account = Mock()
    newly_selected_account = Mock()

    page._remote_post_updating_shutting_down = False
    page._remote_post_updating_account = original_account
    page._remote_post_update_succeeded = True

    page.post_editor.selected_accounts.return_value = (
        newly_selected_account,
    )

    PostsPage._on_remote_post_update_finished(page)

    assert page._remote_post_updating_account is None
    assert page._remote_post_update_succeeded is False

    page._refresh_remote_posts.assert_not_called()
    page.remote_posts_panel.restore_editing.assert_not_called()
    page.remote_posts_panel.status_label.setText.assert_not_called()

def test_remote_post_update_callbacks_ignored_during_shutdown():
    """Update callbacks must not modify the UI during shutdown."""
    page = Mock()

    page._remote_post_updating_shutting_down = True
    page._remote_post_updating_account = Mock()
    page._remote_post_update_succeeded = False

    PostsPage._on_remote_post_updated(page)
    PostsPage._on_remote_post_update_error(
        page,
        "HTTP 500",
    )
    PostsPage._on_remote_post_update_finished(page)

    assert page._remote_post_update_succeeded is False

    page.remote_posts_panel.status_label.setText.assert_not_called()
    page.remote_posts_panel.restore_editing.assert_not_called()
    page._refresh_remote_posts.assert_not_called()

def test_remote_posts_loaded_ignores_stale_account():
    """Results from a previous account must not replace current posts."""
    page = Mock()

    original_account = Mock()
    newly_selected_account = Mock()

    page._remote_post_loading_account = original_account
    page._remote_post_loading_shutting_down = False
    page._pending_remote_post_account = newly_selected_account

    page.post_editor.selected_accounts.return_value = (
        newly_selected_account,
    )

    page._is_current_remote_post_account = (
        lambda: PostsPage._is_current_remote_post_account(page)
    )

    previous_posts = (Mock(remote_id="100"),)
    stale_posts = (Mock(remote_id="200"),)

    page._loaded_remote_posts = previous_posts

    PostsPage._on_remote_posts_loaded(page, stale_posts)

    assert page._loaded_remote_posts == previous_posts
    page.remote_posts_panel.show_posts.assert_not_called()

def test_remote_post_save_rejects_mismatched_account():
    """A post must not be updated through a different WordPress account."""
    page = Mock()
    controller = Mock()

    loaded_account = Mock()
    selected_account = Mock()

    loaded_account.destination = PublishingDestination.WORDPRESS
    selected_account.destination = PublishingDestination.WORDPRESS

    page._remote_post_updating_controller = controller
    page._remote_post_updating_shutting_down = False

    controller.is_running = False

    page._loaded_remote_posts_account = loaded_account
    page._loaded_remote_posts = (Mock(remote_id="42"),)

    page.post_editor.selected_accounts.return_value = (
        selected_account,
    )

    PostsPage._handle_remote_post_save(
        page,
        "42",
        "Updated WordPress content",
    )

    controller.start.assert_not_called()
    page.remote_posts_panel.save_button.setEnabled.assert_not_called()
    page.remote_posts_panel.content_editor.setEnabled.assert_not_called()

def test_remote_post_update_error_ignores_previous_account():
    """An update error must not affect a newly selected account."""
    page = Mock()

    original_account = Mock()
    newly_selected_account = Mock()

    page._remote_post_updating_shutting_down = False
    page._remote_post_updating_account = original_account

    page.post_editor.selected_accounts.return_value = (
        newly_selected_account,
    )

    PostsPage._on_remote_post_update_error(
        page,
        "HTTP 403",
    )

    page.remote_posts_panel.status_label.setText.assert_not_called()
    page.remote_posts_panel.restore_editing.assert_not_called()

def test_remote_post_update_error_ignores_other_displayed_account():
    """An update error must not affect another selected account."""
    page = Mock()

    account_a = Mock()
    account_b = Mock()

    account_a.destination = PublishingDestination.WORDPRESS
    account_b.destination = PublishingDestination.WORDPRESS

    page._remote_post_updating_shutting_down = False
    page._remote_post_updating_account = account_a
    page._loaded_remote_posts_account = account_b

    page.post_editor.selected_accounts.return_value = (
        account_b,
        account_a,
    )

    PostsPage._on_remote_post_update_error(
        page,
        "HTTP 403",
    )

    page.remote_posts_panel.status_label.setText.assert_not_called()
    page.remote_posts_panel.restore_editing.assert_not_called()

def test_remote_post_update_finished_ignores_other_displayed_account():
    """A completed update must not refresh another account's posts."""
    page = Mock()

    account_a = Mock()
    account_b = Mock()

    account_a.destination = PublishingDestination.WORDPRESS
    account_b.destination = PublishingDestination.WORDPRESS

    page._remote_post_updating_shutting_down = False
    page._remote_post_updating_account = account_a
    page._remote_post_update_succeeded = True
    page._loaded_remote_posts_account = account_b

    page.post_editor.selected_accounts.return_value = (
        account_b,
        account_a,
    )

    PostsPage._on_remote_post_update_finished(page)

    assert page._remote_post_updating_account is None
    assert page._remote_post_update_succeeded is False

    page._refresh_remote_posts.assert_not_called()
    page.remote_posts_panel.restore_editing.assert_not_called()
    page.remote_posts_panel.status_label.setText.assert_not_called()

def test_posts_page_shutdown_stops_remote_post_updating():
    """Shutdown must stop updates and prevent further callbacks."""
    page = Mock()

    page._remote_post_updating_shutting_down = False

    PostsPage.shutdown(page)

    assert page._remote_post_updating_shutting_down is True

    page._remote_post_updating_controller.shutdown.assert_called_once_with()
    page._remote_post_loading_controller.shutdown.assert_called_once_with()
    page._tag_loading_controller.shutdown.assert_called_once_with()
    page._publishing_controller.shutdown.assert_called_once_with()

def test_remote_post_save_ignored_during_shutdown():
    """No WordPress update may start after shutdown begins."""
    page = Mock()
    controller = Mock()

    page._remote_post_updating_controller = controller
    page._remote_post_updating_shutting_down = True

    controller.is_running = False

    PostsPage._handle_remote_post_save(
        page,
        "42",
        "Updated WordPress content",
    )

    controller.start.assert_not_called()
    page.remote_posts_panel.save_button.setEnabled.assert_not_called()
    page.remote_posts_panel.content_editor.setEnabled.assert_not_called()
    page.remote_posts_panel.status_label.setText.assert_not_called()

def test_remote_post_save_ignored_while_update_running():
    """A second WordPress update must not start while one is running."""
    page = Mock()
    controller = Mock()

    page._remote_post_updating_controller = controller
    page._remote_post_updating_shutting_down = False

    controller.is_running = True

    PostsPage._handle_remote_post_save(
        page,
        "42",
        "Another WordPress update",
    )

    controller.start.assert_not_called()
    page.remote_posts_panel.save_button.setEnabled.assert_not_called()
    page.remote_posts_panel.content_editor.setEnabled.assert_not_called()
    page.remote_posts_panel.status_label.setText.assert_not_called()


def test_remote_post_save_with_tags_starts_tag_aware_update():
    """Tag-aware saving forwards the selected post and tag IDs."""
    page = Mock()

    controller = Mock()
    controller.is_running = False
    page._remote_post_updating_controller = controller
    page._remote_post_updating_shutting_down = False
    page._remote_post_trashing_controller = None

    account = Mock()
    account.destination = PublishingDestination.WORDPRESS

    page.post_editor.selected_accounts.return_value = (account,)
    page._loaded_remote_posts = (Mock(remote_id="42"),)
    page._loaded_remote_posts_account = account
    page.remote_posts_panel = Mock()

    # Bind the real save handler for this isolated test.
    page._handle_remote_post_save = (
        lambda remote_id, content, tags=None:
        PostsPage._handle_remote_post_save(
            page, remote_id, content, tags
        )
    )

    PostsPage._handle_remote_post_save_with_tags(
        page,
        "42",
        "Updated WordPress content",
        (12, 34),
    )

    controller.start.assert_called_once_with(
        account=account,
        post_id=42,
        content="Updated WordPress content",
        tags=(12, 34),
    )


def test_remote_post_save_with_tags_rejects_invalid_ids():
    """Invalid tag IDs never reach the update controller."""
    page = Mock()
    page.remote_posts_panel = Mock()

    PostsPage._handle_remote_post_save_with_tags(
        page,
        "42",
        "Updated WordPress content",
        (0, 34),
    )

    page._handle_remote_post_save.assert_not_called()
    page.remote_posts_panel.status_label.setText.assert_called_once_with(
        "WordPress tag IDs must be positive integers."
    )
    page.remote_posts_panel.restore_editing.assert_called_once_with()


def test_tag_aware_save_rejection_restores_editing():
    """A rejected tag-aware save must restore the editors."""
    page = Mock()
    controller = Mock()

    page._remote_post_updating_controller = controller
    page._remote_post_updating_shutting_down = False
    page._remote_post_trashing_controller = None
    controller.is_running = True

    page._handle_remote_post_save = (
        lambda remote_id, content, tags=None:
        PostsPage._handle_remote_post_save(
            page, remote_id, content, tags
        )
    )

    PostsPage._handle_remote_post_save_with_tags(
        page,
        "42",
        "Updated WordPress content",
        (12, 34),
    )

    controller.start.assert_not_called()
    page.remote_posts_panel.restore_editing.assert_called_once_with()


import pytest


@pytest.mark.parametrize(
    ("controller_available", "shutting_down", "is_running"),
    [
        (False, False, False),
        (True, True, False),
        (True, False, True),
    ],
)
def test_rejected_remote_post_save_restores_editing(
    controller_available,
    shutting_down,
    is_running,
):
    page = Mock()
    controller = Mock()
    controller.is_running = is_running

    page._remote_post_updating_controller = (
        controller if controller_available else None
    )
    page._remote_post_updating_shutting_down = shutting_down
    page._remote_post_trashing_controller = None

    PostsPage._handle_remote_post_save(
        page,
        "42",
        "Updated content",
    )

    controller.start.assert_not_called()
    page.remote_posts_panel.restore_editing.assert_called_once_with()



def make_featured_media_update_page():
    page = Mock()

    controller = Mock()
    controller.is_running = False

    account = Mock()
    account.destination = PublishingDestination.WORDPRESS

    page._remote_post_updating_controller = controller
    page._remote_post_updating_shutting_down = False
    page._remote_post_trashing_controller = None
    page._remote_posts_generation = 1

    page._loaded_remote_posts_account = account
    page._loaded_remote_posts = (Mock(remote_id="42"),)

    page.post_editor.selected_accounts.return_value = (account,)

    save_handler = getattr(
        PostsPage,
        "_handle_remote_post_save",
    )

    page._handle_remote_post_save = lambda *args, **kwargs: (
        save_handler(page, *args, **kwargs)
    )

    return page, controller, account


@pytest.mark.parametrize(
    "featured_media_id",
    [789, 0],
    ids=["replace-featured-image", "remove-featured-image"],
)
def test_featured_media_update_reaches_controller(
    featured_media_id,
):
    page, controller, account = make_featured_media_update_page()

    PostsPage._handle_remote_post_save_with_media(
        page,
        "42",
        "Updated content čćžšđ",
        None,
        featured_media_id,
    )

    controller.start.assert_called_once_with(
        account=account,
        post_id=42,
        content="Updated content čćžšđ",
        featured_media_id=featured_media_id,
    )

    assert page._remote_post_updating_account is account
    assert page._remote_post_updating_generation == 1
    assert page._remote_post_update_succeeded is False


@pytest.mark.parametrize(
    "featured_media_id",
    [789, 0],
    ids=["replace-with-tags", "remove-with-tags"],
)
def test_featured_media_update_preserves_explicit_tags(
    featured_media_id,
):
    page, controller, account = make_featured_media_update_page()

    PostsPage._handle_remote_post_save_with_media(
        page,
        "42",
        "Updated content",
        (12, 34),
        featured_media_id,
    )

    controller.start.assert_called_once_with(
        account=account,
        post_id=42,
        content="Updated content",
        tags=(12, 34),
        featured_media_id=featured_media_id,
    )


@pytest.mark.parametrize(
    "invalid_media_id",
    [-1, True, False, 1.5, "789", None],
)
def test_invalid_featured_media_id_does_not_start_update(
    invalid_media_id,
):
    page, controller, account = make_featured_media_update_page()

    PostsPage._handle_remote_post_save_with_media(
        page,
        "42",
        "Updated content",
        None,
        invalid_media_id,
    )

    controller.start.assert_not_called()

    page.remote_posts_panel.status_label.setText.assert_called_once_with(
        "WordPress featured media ID must be "
        "a non-negative integer."
    )
    page.remote_posts_panel.restore_editing.assert_called_once()


@pytest.mark.parametrize(
    "invalid_tags",
    [
        [12, 34],
        (0,),
        (-1,),
    ],
    ids=["list-instead-of-tuple", "zero-tag", "negative-tag"],
)
def test_invalid_tags_block_featured_media_update(
    invalid_tags,
):
    page, controller, account = make_featured_media_update_page()

    PostsPage._handle_remote_post_save_with_media(
        page,
        "42",
        "Updated content",
        cast(tuple[int, ...] | None, invalid_tags),
        789,
    )

    controller.start.assert_not_called()

    page.remote_posts_panel.status_label.setText.assert_called_once_with(
        "WordPress tag IDs must be positive integers."
    )
    page.remote_posts_panel.restore_editing.assert_called_once()



@pytest.mark.parametrize(
    "excerpt",
    [
        "",
        "Sažetak čćžšđ",
    ],
    ids=["clear-excerpt", "replace-excerpt"],
)
def test_excerpt_update_reaches_controller(excerpt):
    page, controller, account = make_featured_media_update_page()

    PostsPage._handle_remote_post_save_with_excerpt(
        page,
        "42",
        "Updated content",
        None,
        None,
        None,
        excerpt,
    )

    controller.start.assert_called_once_with(
        account=account,
        post_id=42,
        content="Updated content",
        excerpt=excerpt,
    )

    assert page._remote_post_updating_account is account
    assert page._remote_post_update_succeeded is False


def test_excerpt_update_preserves_combined_metadata():
    page, controller, account = make_featured_media_update_page()

    PostsPage._handle_remote_post_save_with_excerpt(
        page,
        "42",
        "Updated content",
        (12, 34),
        789,
        "draft",
        "Sažetak čćžšđ",
    )

    controller.start.assert_called_once_with(
        account=account,
        post_id=42,
        content="Updated content",
        tags=(12, 34),
        featured_media_id=789,
        status="draft",
        excerpt="Sažetak čćžšđ",
    )


def test_excerpt_update_rejects_invalid_tag_ids():
    page, controller, _account = make_featured_media_update_page()

    PostsPage._handle_remote_post_save_with_excerpt(
        page,
        "42",
        "Updated content",
        (0,),
        None,
        None,
        "New excerpt",
    )

    controller.start.assert_not_called()
    page.remote_posts_panel.restore_editing.assert_called_once()


def test_excerpt_update_rejects_invalid_status():
    page, controller, _account = make_featured_media_update_page()

    PostsPage._handle_remote_post_save_with_excerpt(
        page,
        "42",
        "Updated content",
        None,
        None,
        "unsupported",
        "New excerpt",
    )

    controller.start.assert_not_called()
    page.remote_posts_panel.restore_editing.assert_called_once()



@pytest.mark.parametrize(
    "title",
    ["Updated title", "Novi naslov čćžšđ"],
)
def test_title_update_reaches_controller(title):
    page, controller, account = make_featured_media_update_page()

    PostsPage._handle_remote_post_save_with_title(
        page,
        "42",
        "Updated content",
        None,
        None,
        None,
        None,
        title,
    )

    controller.start.assert_called_once_with(
        account=account,
        post_id=42,
        content="Updated content",
        title=title,
    )

    assert page._remote_post_updating_account is account
    assert page._remote_post_update_succeeded is False


def test_title_update_preserves_combined_metadata():
    page, controller, account = make_featured_media_update_page()

    PostsPage._handle_remote_post_save_with_title(
        page,
        "42",
        "Updated content",
        (12, 34),
        789,
        "draft",
        "Updated excerpt",
        "Updated title",
    )

    controller.start.assert_called_once_with(
        account=account,
        post_id=42,
        content="Updated content",
        tags=(12, 34),
        featured_media_id=789,
        status="draft",
        excerpt="Updated excerpt",
        title="Updated title",
    )


@pytest.mark.parametrize(
    "invalid_title",
    ["", "   ", "\n\t", 123, True, None],
)
def test_title_update_rejects_invalid_title(invalid_title):
    page, controller, _account = make_featured_media_update_page()

    PostsPage._handle_remote_post_save_with_title(
        page,
        "42",
        "Updated content",
        None,
        None,
        None,
        None,
        invalid_title,
    )

    controller.start.assert_not_called()
    page.remote_posts_panel.restore_editing.assert_called_once()


def test_title_update_rejects_invalid_tags():
    page, controller, _account = make_featured_media_update_page()

    PostsPage._handle_remote_post_save_with_title(
        page,
        "42",
        "Updated content",
        (0,),
        None,
        None,
        None,
        "Updated title",
    )

    controller.start.assert_not_called()
    page.remote_posts_panel.restore_editing.assert_called_once()


def test_title_update_rejects_invalid_status():
    page, controller, _account = make_featured_media_update_page()

    PostsPage._handle_remote_post_save_with_title(
        page,
        "42",
        "Updated content",
        None,
        None,
        "unsupported",
        None,
        "Updated title",
    )

    controller.start.assert_not_called()
    page.remote_posts_panel.restore_editing.assert_called_once()


def test_title_update_rejects_invalid_excerpt():
    page, controller, _account = make_featured_media_update_page()

    PostsPage._handle_remote_post_save_with_title(
        page,
        "42",
        "Updated content",
        None,
        None,
        None,
        cast(str | None, 123),
        "Updated title",
    )

    controller.start.assert_not_called()
    page.remote_posts_panel.restore_editing.assert_called_once()
