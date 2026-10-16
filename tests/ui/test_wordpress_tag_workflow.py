from unittest.mock import Mock, patch

import pytest
from PySide6.QtWidgets import QDialog

from socialflow.domain.account.account import Account
from socialflow.domain.post.tag import Tag
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.infrastructure.wordpress.wordpress_tag_creation_plan import (
    WordPressTagCreationPlan,
)
from socialflow.ui.posts.posts_page import PostsPage


def make_account(name: str) -> Account:
    return Account(
        name=name,
        destination=PublishingDestination.WORDPRESS,
    )


def make_plan() -> WordPressTagCreationPlan:
    return WordPressTagCreationPlan(
        missing_tags=(Tag("SocialFlow"),),
    )


def make_request(accounts: list[Account]) -> Mock:
    request = Mock()
    request.accounts = tuple(accounts)
    request.post.tags = (Tag("SocialFlow"),)
    return request


@pytest.fixture
def workflow(qtbot):
    """Create a Qt-managed PostsPage with mocked dependencies."""
    list_accounts = Mock()
    list_accounts.execute.return_value = ()

    page = PostsPage(
        publish_post=Mock(),
        list_accounts=list_accounts,
        list_tags=Mock(),
        create_tag=Mock(),
        list_recent_publications=Mock(),
    )

    qtbot.addWidget(page)

    creation_controller = Mock()
    creation_controller.is_running = False

    preparation_controller = Mock()
    preparation_controller.is_running = False

    page._wordpress_tag_creation_controller = creation_controller
    page._wordpress_tag_preparation_controller = preparation_controller

    page._wordpress_preparation_shutting_down = False
    page._pending_publish_request = None
    page._pending_wordpress_accounts = []
    page._preparing_wordpress_account = None
    page._approved_wordpress_tag_plans = {}
    page._wordpress_tag_creation_failed = False
    page._wordpress_tag_creation_completed = False

    yield page

    page.shutdown()


def test_approved_tags_are_created_before_publishing(workflow):
    account = make_account("WordPress A")
    request = make_request([account])
    plan = make_plan()

    workflow._pending_publish_request = request
    workflow._preparing_wordpress_account = account

    with patch(
        "socialflow.ui.posts.posts_page.WordPressTagConfirmationDialog"
    ) as dialog:
        with patch.object(
            workflow,
            "_start_publishing",
        ) as start_publishing:
            dialog.return_value.exec.return_value = (
                QDialog.DialogCode.Accepted
            )

            workflow._on_wordpress_tag_plan_ready(plan)

            assert (
                workflow._approved_wordpress_tag_plans[account.id]
                == plan
            )

            workflow._on_wordpress_tag_preparation_finished()

            creation_start = (
                workflow._wordpress_tag_creation_controller.start
            )
            assert creation_start.call_args_list == [
                ((), {"account": account, "plan": plan})
            ]

            start_publishing.assert_not_called()

            workflow._on_wordpress_tags_created(())
            workflow._on_wordpress_tag_creation_finished()

            start_publishing.assert_called_once_with(request)


def test_rejected_tags_cancel_publishing(workflow):
    account = make_account("WordPress A")
    request = make_request([account])

    workflow._pending_publish_request = request
    workflow._preparing_wordpress_account = account

    with patch(
        "socialflow.ui.posts.posts_page.WordPressTagConfirmationDialog"
    ) as dialog:
        with patch.object(
            workflow,
            "_start_publishing",
        ) as start_publishing:
            dialog.return_value.exec.return_value = (
                QDialog.DialogCode.Rejected
            )

            workflow._on_wordpress_tag_plan_ready(make_plan())

            assert workflow._pending_publish_request is None
            assert workflow._approved_wordpress_tag_plans == {}

            creation_start = (
                workflow._wordpress_tag_creation_controller.start
            )
            assert creation_start.call_count == 0
            start_publishing.assert_not_called()


def test_creation_failure_prevents_publishing(workflow):
    account = make_account("WordPress A")
    workflow._pending_publish_request = make_request([account])
    workflow._preparing_wordpress_account = account

    with patch.object(
        workflow,
        "_start_publishing",
    ) as start_publishing:
        workflow._on_wordpress_tag_creation_error(
            "WordPress API error"
        )
        workflow._on_wordpress_tag_creation_finished()

        assert workflow._pending_publish_request is None
        start_publishing.assert_not_called()


def test_multiple_accounts_are_processed_sequentially(workflow):
    first = make_account("WordPress A")
    second = make_account("WordPress B")
    request = make_request([first, second])
    plan = make_plan()

    workflow._pending_publish_request = request
    workflow._preparing_wordpress_account = first
    workflow._pending_wordpress_accounts = [second]
    workflow._approved_wordpress_tag_plans[first.id] = plan

    with patch.object(
        workflow,
        "_start_publishing",
    ) as start_publishing:
        with patch.object(
            workflow,
            "_start_next_wordpress_tag_preparation",
        ) as start_next:
            workflow._on_wordpress_tag_preparation_finished()

            creation_start = (
                workflow._wordpress_tag_creation_controller.start
            )
            assert creation_start.call_args_list == [
                ((), {"account": first, "plan": plan})
            ]

            workflow._on_wordpress_tags_created(())
            workflow._on_wordpress_tag_creation_finished()

            start_next.assert_called_once_with()
            start_publishing.assert_not_called()

            assert workflow._pending_wordpress_accounts == [second]


def test_existing_tags_allow_publishing(workflow):
    account = make_account("WordPress A")
    request = make_request([account])

    workflow._pending_publish_request = request
    workflow._preparing_wordpress_account = account

    empty_plan = WordPressTagCreationPlan(missing_tags=())

    with patch.object(
        workflow,
        "_start_publishing",
    ) as start_publishing:
        workflow._on_wordpress_tag_plan_ready(empty_plan)
        workflow._on_wordpress_tag_preparation_finished()

        creation_start = (
            workflow._wordpress_tag_creation_controller.start
        )
        assert creation_start.call_count == 0

        start_publishing.assert_called_once_with(request)

def test_duplicate_request_does_not_replace_pending_request(workflow):
    account = make_account("WordPress A")
    original_request = make_request([account])
    duplicate_request = make_request([account])

    workflow._pending_publish_request = original_request
    workflow._last_publish_request = original_request

    with patch.object(
        workflow,
        "_begin_wordpress_tag_preparation",
    ) as begin_preparation:
        workflow._handle_publish_request(duplicate_request)

        begin_preparation.assert_not_called()

    assert workflow._pending_publish_request is original_request
    assert workflow._last_publish_request is original_request


def test_duplicate_request_during_tag_creation_is_ignored(workflow):
    account = make_account("WordPress A")
    request = make_request([account])

    workflow._wordpress_tag_creation_controller.is_running = True

    with patch.object(
        workflow,
        "_begin_wordpress_tag_preparation",
    ) as begin_preparation:
        workflow._handle_publish_request(request)

        begin_preparation.assert_not_called()

    assert workflow._last_publish_request is None


def test_duplicate_request_during_tag_preparation_is_ignored(workflow):
    account = make_account("WordPress A")
    request = make_request([account])

    workflow._wordpress_tag_preparation_controller.is_running = True

    with patch.object(
        workflow,
        "_begin_wordpress_tag_preparation",
    ) as begin_preparation:
        workflow._handle_publish_request(request)

        begin_preparation.assert_not_called()

    assert workflow._last_publish_request is None

def test_all_wordpress_accounts_complete_before_publishing(workflow):
    first = make_account("WordPress A")
    second = make_account("WordPress B")
    request = make_request([first, second])
    plan = make_plan()

    workflow._pending_publish_request = request
    workflow._pending_wordpress_accounts = [second]
    workflow._preparing_wordpress_account = first
    workflow._approved_wordpress_tag_plans[first.id] = plan

    with patch.object(
        workflow,
        "_start_publishing",
    ) as start_publishing:
        # First account: preparation finishes and creation starts.
        workflow._on_wordpress_tag_preparation_finished()

        creation_start = (
            workflow._wordpress_tag_creation_controller.start
        )

        assert creation_start.call_count == 1
        start_publishing.assert_not_called()

        # First account: approved tags are created.
        workflow._on_wordpress_tags_created(())
        workflow._on_wordpress_tag_creation_finished()

        preparation_start = (
            workflow._wordpress_tag_preparation_controller.start
        )

        assert preparation_start.call_count == 1
        assert workflow._preparing_wordpress_account == second
        start_publishing.assert_not_called()

        # Second account: preparation reports another approved plan.
        workflow._approved_wordpress_tag_plans[second.id] = plan
        workflow._on_wordpress_tag_preparation_finished()

        assert creation_start.call_count == 2
        start_publishing.assert_not_called()

        # Second account: approved tags are created.
        workflow._on_wordpress_tags_created(())
        workflow._on_wordpress_tag_creation_finished()

        # Publishing starts only after both accounts finish.
        start_publishing.assert_called_once_with(request)

        assert workflow._pending_publish_request is None
        assert workflow._pending_wordpress_accounts == []
        assert workflow._approved_wordpress_tag_plans == {}

def test_cancelled_workflow_does_not_resume_after_preparation_finishes(
    workflow,
):
    account = make_account("WordPress A")
    request = make_request([account])

    workflow._pending_publish_request = request
    workflow._preparing_wordpress_account = account

    with patch.object(
        workflow,
        "_start_publishing",
    ) as start_publishing:
        workflow._cancel_wordpress_tag_preparation()
        workflow._on_wordpress_tag_preparation_finished()

        start_publishing.assert_not_called()
        assert workflow._pending_publish_request is None


def test_cancelled_workflow_does_not_resume_after_creation_finishes(
    workflow,
):
    account = make_account("WordPress A")
    request = make_request([account])

    workflow._pending_publish_request = request
    workflow._preparing_wordpress_account = account

    with patch.object(
        workflow,
        "_start_publishing",
    ) as start_publishing:
        workflow._on_wordpress_tags_created(())
        workflow._cancel_wordpress_tag_preparation()
        workflow._on_wordpress_tag_creation_finished()

        start_publishing.assert_not_called()
        assert workflow._pending_publish_request is None


def test_shutdown_prevents_queued_wordpress_work(
    workflow,
):
    first = make_account("WordPress A")
    second = make_account("WordPress B")
    request = make_request([first, second])

    workflow._pending_publish_request = request
    workflow._pending_wordpress_accounts = [second]
    workflow._preparing_wordpress_account = first

    with patch.object(
        workflow,
        "_start_publishing",
    ) as start_publishing:
        workflow.shutdown()

        workflow._on_wordpress_tag_preparation_finished()
        workflow._on_wordpress_tags_created(())
        workflow._on_wordpress_tag_creation_finished()

        start_publishing.assert_not_called()

        assert workflow._pending_publish_request is None
        assert workflow._pending_wordpress_accounts == []
        assert workflow._wordpress_preparation_shutting_down is True

def test_remote_tag_lookup_failure_cancels_publishing(workflow):
    account = make_account("WordPress A")
    request = make_request([account])

    workflow._pending_publish_request = request
    workflow._pending_wordpress_accounts = []
    workflow._preparing_wordpress_account = account

    with patch.object(
        workflow,
        "_start_publishing",
    ) as start_publishing:
        workflow._on_wordpress_tag_preparation_error(
            "Connection timed out while retrieving tags."
        )

        # Simulate the preparation thread finishing after its error.
        workflow._on_wordpress_tag_preparation_finished()

        start_publishing.assert_not_called()

    assert workflow._pending_publish_request is None
    assert workflow._pending_wordpress_accounts == []
    assert workflow._approved_wordpress_tag_plans == {}

    assert (
        workflow.publish_status.text()
        == "Unable to prepare WordPress tags: "
        "Connection timed out while retrieving tags."
    )

def test_creation_finished_without_result_cancels_pending_publishing(
    workflow,
):
    account = make_account("WordPress A")
    request = make_request([account])

    workflow._pending_publish_request = request
    workflow._preparing_wordpress_account = account

    with patch.object(
        workflow,
        "_start_publishing",
    ) as start_publishing:
        workflow._on_wordpress_tag_creation_finished()

        assert workflow._pending_publish_request is None
        assert workflow._preparing_wordpress_account is None
        assert workflow._pending_wordpress_accounts == []
        assert workflow._approved_wordpress_tag_plans == {}

        start_publishing.assert_not_called()

def test_creation_finished_after_success_continues_preparation(
    workflow,
):
    account = make_account("WordPress A")
    request = make_request([account])

    workflow._pending_publish_request = request
    workflow._preparing_wordpress_account = account
    workflow._wordpress_tag_creation_completed = True
    workflow._wordpress_tag_creation_failed = False

    with patch.object(
        workflow,
        "_continue_wordpress_tag_preparation",
    ) as continue_preparation:
        with patch.object(
            workflow,
            "_cancel_wordpress_tag_preparation",
        ) as cancel_preparation:
            workflow._on_wordpress_tag_creation_finished()

    continue_preparation.assert_called_once_with()
    cancel_preparation.assert_not_called()

def test_cancellation_clears_all_wordpress_workflow_state(workflow):
    account = make_account("WordPress A")
    request = make_request([account])

    workflow._pending_publish_request = request
    workflow._pending_wordpress_accounts = [account]
    workflow._preparing_wordpress_account = account
    workflow._approved_wordpress_tag_plans[account.id] = make_plan()
    workflow._wordpress_tag_creation_completed = True
    workflow._wordpress_tag_creation_failed = True

    workflow._cancel_wordpress_tag_preparation()

    assert workflow._pending_publish_request is None
    assert workflow._pending_wordpress_accounts == []
    assert workflow._preparing_wordpress_account is None
    assert workflow._approved_wordpress_tag_plans == {}
    assert workflow._wordpress_tag_creation_completed is False
    assert workflow._wordpress_tag_creation_failed is False
    assert workflow.post_editor.publish_button.isEnabled()

def test_repeated_cancellation_preserves_clean_workflow_state(workflow):
    account = make_account("WordPress A")

    workflow._pending_publish_request = make_request([account])
    workflow._pending_wordpress_accounts = [account]
    workflow._preparing_wordpress_account = account
    workflow._approved_wordpress_tag_plans[account.id] = make_plan()
    workflow._wordpress_tag_creation_completed = True
    workflow._wordpress_tag_creation_failed = True

    workflow._cancel_wordpress_tag_preparation()
    workflow._cancel_wordpress_tag_preparation()

    assert workflow._pending_publish_request is None
    assert workflow._pending_wordpress_accounts == []
    assert workflow._preparing_wordpress_account is None
    assert workflow._approved_wordpress_tag_plans == {}
    assert workflow._wordpress_tag_creation_completed is False
    assert workflow._wordpress_tag_creation_failed is False
    assert workflow.post_editor.publish_button.isEnabled()

def test_creation_error_followed_by_finished_preserves_error(workflow):
    account = make_account("WordPress A")
    request = make_request([account])

    workflow._pending_publish_request = request
    workflow._preparing_wordpress_account = account

    with patch.object(
        workflow,
        "_start_publishing",
    ) as start_publishing:
        workflow._on_wordpress_tag_creation_error(
            "WordPress API connection failed"
        )

        workflow._on_wordpress_tag_creation_finished()

        start_publishing.assert_not_called()

    assert workflow._pending_publish_request is None
    assert workflow._preparing_wordpress_account is None
    assert workflow._wordpress_tag_creation_completed is False
    assert workflow._wordpress_tag_creation_failed is False

    assert workflow.publish_status.text() == (
        "Unable to create WordPress tags: "
        "WordPress API connection failed"
    )

    assert workflow.post_editor.publish_button.isEnabled()