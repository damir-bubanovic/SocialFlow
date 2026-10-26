from unittest.mock import Mock

from socialflow.domain.account.account import Account
from socialflow.domain.publishing.destination import (
    PublishingDestination,
)
from socialflow.ui.workers.remote_post_updating_worker import (
    RemotePostUpdatingWorker,
)


def test_worker_emits_finished_after_successful_update(qtbot):
    account = Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    update_remote_post = Mock()

    worker = RemotePostUpdatingWorker(
        update_remote_post=update_remote_post,
        account=account,
        post_id=123,
        content="Ažurirani sadržaj čćžšđ",
    )

    with qtbot.waitSignal(worker.finished, timeout=1000):
        worker.run()

    update_remote_post.execute.assert_called_once_with(
        account=account,
        post_id=123,
        content="Ažurirani sadržaj čćžšđ",
    )


def test_worker_emits_failed_when_update_fails(qtbot):
    account = Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    update_remote_post = Mock()
    update_remote_post.execute.side_effect = RuntimeError(
        "WordPress post update failed (HTTP 403)."
    )

    worker = RemotePostUpdatingWorker(
        update_remote_post=update_remote_post,
        account=account,
        post_id=123,
        content="Updated content",
    )

    with qtbot.waitSignal(worker.failed, timeout=1000) as signal:
        worker.run()

    assert signal.args == [
        "WordPress post update failed (HTTP 403)."
    ]

    update_remote_post.execute.assert_called_once_with(
        account=account,
        post_id=123,
        content="Updated content",
    )

def test_remote_post_updating_worker_emits_success_signal(qtbot):
    """A successful update must emit its Qt completion signal."""
    update_remote_post = Mock()
    account = Mock()

    worker = RemotePostUpdatingWorker(
        update_remote_post=update_remote_post,
        account=account,
        post_id=42,
        content="Updated WordPress content",
    )

    with qtbot.waitSignal(worker.finished, timeout=1000):
        worker.run()

    update_remote_post.execute.assert_called_once_with(
        account=account,
        post_id=42,
        content="Updated WordPress content",
    )

def test_remote_post_updating_worker_emits_error_and_finished(qtbot):
    """A failed update must emit an error and a completion signal."""
    update_remote_post = Mock()
    update_remote_post.execute.side_effect = RuntimeError(
        "WordPress update failed"
    )

    worker = RemotePostUpdatingWorker(
        update_remote_post=update_remote_post,
        account=Mock(),
        post_id=42,
        content="Updated WordPress content",
    )

    errors = []
    worker.failed.connect(errors.append)

    with qtbot.waitSignal(worker.finished, timeout=1000):
        worker.run()

    assert errors == ["WordPress update failed"]


def test_worker_forwards_tag_ids(qtbot):
    """Forward tag IDs when updating an existing remote post."""
    update_remote_post = Mock()
    account = Mock()

    worker = RemotePostUpdatingWorker(
        update_remote_post=update_remote_post,
        account=account,
        post_id=123,
        content="Updated content",
        tags=(12, 34),
    )

    with qtbot.waitSignal(worker.finished, timeout=1000):
        worker.run()

    update_remote_post.execute.assert_called_once_with(
        account=account,
        post_id=123,
        content="Updated content",
        tags=(12, 34),
    )


def test_worker_forwards_empty_tags(qtbot):
    """An empty tag tuple explicitly clears existing tags."""
    update_remote_post = Mock()
    account = Mock()

    worker = RemotePostUpdatingWorker(
        update_remote_post=update_remote_post,
        account=account,
        post_id=123,
        content="Updated content",
        tags=(),
    )

    with qtbot.waitSignal(worker.finished, timeout=1000):
        worker.run()

    update_remote_post.execute.assert_called_once_with(
        account=account,
        post_id=123,
        content="Updated content",
        tags=(),
    )

def test_worker_forwards_featured_media_id(qtbot):
    update_remote_post = Mock()
    account = Mock()

    worker = RemotePostUpdatingWorker(
        update_remote_post=update_remote_post,
        account=account,
        post_id=123,
        content="Updated content",
        featured_media_id=456,
    )

    with qtbot.waitSignal(worker.finished, timeout=1000):
        worker.run()

    update_remote_post.execute.assert_called_once_with(
        account=account,
        post_id=123,
        content="Updated content",
        featured_media_id=456,
    )

import pytest


@pytest.mark.parametrize(
    "status",
    ("draft", "pending", "private", "publish"),
)
def test_worker_forwards_wordpress_status(qtbot, status):
    update_remote_post = Mock()
    account = Mock()

    worker = RemotePostUpdatingWorker(
        update_remote_post=update_remote_post,
        account=account,
        post_id=123,
        content="Updated content",
        status=status,
    )

    with qtbot.waitSignal(worker.finished, timeout=1000):
        worker.run()

    update_remote_post.execute.assert_called_once_with(
        account=account,
        post_id=123,
        content="Updated content",
        status=status,
    )


def test_worker_combines_status_with_existing_metadata(qtbot):
    update_remote_post = Mock()
    account = Mock()

    worker = RemotePostUpdatingWorker(
        update_remote_post=update_remote_post,
        account=account,
        post_id=123,
        content="Updated content",
        tags=(10, 20),
        featured_media_id=456,
        status="draft",
    )

    with qtbot.waitSignal(worker.finished, timeout=1000):
        worker.run()

    update_remote_post.execute.assert_called_once_with(
        account=account,
        post_id=123,
        content="Updated content",
        tags=(10, 20),
        featured_media_id=456,
        status="draft",
    )


@pytest.mark.parametrize(
    "excerpt",
    ["", "Sažetak čćžšđ"],
)
def test_worker_forwards_excerpt(qtbot, excerpt):
    account = Mock()
    update_remote_post = Mock()

    worker = RemotePostUpdatingWorker(
        update_remote_post=update_remote_post,
        account=account,
        post_id=42,
        content="Updated content",
        excerpt=excerpt,
    )

    with qtbot.waitSignal(worker.finished, timeout=1000):
        worker.run()

    update_remote_post.execute.assert_called_once_with(
        account=account,
        post_id=42,
        content="Updated content",
        excerpt=excerpt,
    )
