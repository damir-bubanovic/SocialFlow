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