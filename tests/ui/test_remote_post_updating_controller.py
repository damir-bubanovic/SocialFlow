from threading import Event
from unittest.mock import Mock
import pytest

from socialflow.domain.account.account import Account
from socialflow.domain.publishing.destination import (
    PublishingDestination,
)
from socialflow.ui.workers.remote_post_updating_controller import (
    RemotePostUpdatingController,
)


def make_account():
    return Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
    )


def test_controller_starts_without_running_thread():
    controller = RemotePostUpdatingController(
        update_remote_post=Mock(),
    )

    assert not controller.is_running

    controller.shutdown()


def test_controller_updates_post_in_background(qtbot):
    account = make_account()
    update_remote_post = Mock()

    controller = RemotePostUpdatingController(
        update_remote_post=update_remote_post,
    )

    try:
        with qtbot.waitSignal(
            controller.post_updated,
            timeout=5000,
        ):
            controller.start(
                account=account,
                post_id=123,
                content="Ažurirani sadržaj čćžšđ",
            )

        qtbot.waitUntil(
            lambda: not controller.is_running,
            timeout=5000,
        )

        update_remote_post.execute.assert_called_once_with(
            account=account,
            post_id=123,
            content="Ažurirani sadržaj čćžšđ",
        )
    finally:
        controller.shutdown()


def test_controller_reports_update_failure(qtbot):
    account = make_account()
    update_remote_post = Mock()
    update_remote_post.execute.side_effect = RuntimeError(
        "WordPress post update failed (HTTP 403)."
    )

    controller = RemotePostUpdatingController(
        update_remote_post=update_remote_post,
    )

    try:
        with qtbot.waitSignal(
            controller.error_occurred,
            timeout=5000,
        ) as signal:
            controller.start(
                account=account,
                post_id=123,
                content="Updated content",
            )

        assert signal.args == [
            "WordPress post update failed (HTTP 403)."
        ]

        qtbot.waitUntil(
            lambda: not controller.is_running,
            timeout=5000,
        )

        update_remote_post.execute.assert_called_once_with(
            account=account,
            post_id=123,
            content="Updated content",
        )
    finally:
        controller.shutdown()


def test_controller_prevents_concurrent_updates(qtbot):
    account = make_account()

    worker_started = Event()
    allow_worker_to_finish = Event()

    def update_post(**_kwargs):
        worker_started.set()

        if not allow_worker_to_finish.wait(timeout=5):
            raise TimeoutError("Worker was not released")

    update_remote_post = Mock()
    update_remote_post.execute.side_effect = update_post

    controller = RemotePostUpdatingController(
        update_remote_post=update_remote_post,
    )

    try:
        controller.start(
            account=account,
            post_id=123,
            content="First update",
        )

        qtbot.waitUntil(
            worker_started.is_set,
            timeout=5000,
        )

        assert controller.is_running

        controller.start(
            account=account,
            post_id=456,
            content="Second update",
        )

        assert update_remote_post.execute.call_count == 1

        allow_worker_to_finish.set()

        qtbot.waitUntil(
            lambda: not controller.is_running,
            timeout=5000,
        )

        update_remote_post.execute.assert_called_once_with(
            account=account,
            post_id=123,
            content="First update",
        )
    finally:
        allow_worker_to_finish.set()
        controller.shutdown()


def test_controller_shutdown_waits_for_active_worker(qtbot):
    account = make_account()

    worker_started = Event()
    allow_worker_to_finish = Event()

    def update_post(**kwargs):
        assert kwargs == {
            "account": account,
            "post_id": 123,
            "content": "Updated content",
        }

        worker_started.set()

        if not allow_worker_to_finish.wait(timeout=5):
            raise TimeoutError("Worker was not released")

    update_remote_post = Mock()
    update_remote_post.execute.side_effect = update_post

    controller = RemotePostUpdatingController(
        update_remote_post=update_remote_post,
    )

    try:
        controller.start(
            account=account,
            post_id=123,
            content="Updated content",
        )

        qtbot.waitUntil(
            worker_started.is_set,
            timeout=5000,
        )

        assert controller.is_running

        allow_worker_to_finish.set()
        controller.shutdown()

        assert not controller.is_running

        update_remote_post.execute.assert_called_once_with(
            account=account,
            post_id=123,
            content="Updated content",
        )
    finally:
        allow_worker_to_finish.set()
        controller.shutdown()

def test_failed_update_does_not_emit_post_updated(qtbot):
    """A failed WordPress update must never report success."""
    update_remote_post = Mock()
    update_remote_post.execute.side_effect = RuntimeError(
        "WordPress update failed"
    )

    controller = RemotePostUpdatingController(
        update_remote_post=update_remote_post,
    )

    successes = []
    errors = []

    controller.post_updated.connect(lambda: successes.append(True))
    controller.error_occurred.connect(errors.append)

    try:
        with qtbot.waitSignal(controller.finished, timeout=5000):
            controller.start(
                account=Mock(),
                post_id=42,
                content="Updated WordPress content",
            )

        assert errors == ["WordPress update failed"]
        assert successes == []
        assert controller.is_running is False

    finally:
        controller.shutdown()

def test_shutdown_waits_for_active_remote_post_update():
    """Shutdown must wait until an active update has finished."""
    import threading

    update_started = threading.Event()
    allow_update_to_finish = threading.Event()

    def execute_update(**_kwargs):
        update_started.set()

        if not allow_update_to_finish.wait(timeout=3):
            raise RuntimeError("Timed out waiting to finish update")

    update_remote_post = Mock()
    update_remote_post.execute.side_effect = execute_update

    controller = RemotePostUpdatingController(
        update_remote_post=update_remote_post,
    )

    try:
        controller.start(
            account=Mock(),
            post_id=42,
            content="Updated WordPress content",
        )

        assert update_started.wait(timeout=2)
        assert controller.is_running is True

        # Allow the worker to finish before shutdown waits for it.
        allow_update_to_finish.set()

        controller.shutdown()

        assert controller.is_running is False
        assert controller._thread is None
        assert controller._worker is None

        update_remote_post.execute.assert_called_once()

    finally:
        allow_update_to_finish.set()
        controller.shutdown()

def test_successful_update_emits_post_updated_once(qtbot):
    """A successful update reports success and releases its thread."""
    update_remote_post = Mock()

    controller = RemotePostUpdatingController(
        update_remote_post=update_remote_post,
    )

    successes = []
    errors = []

    controller.post_updated.connect(lambda: successes.append(True))
    controller.error_occurred.connect(errors.append)

    try:
        with qtbot.waitSignal(controller.finished, timeout=5000):
            controller.start(
                account=Mock(),
                post_id=42,
                content="Updated WordPress content",
            )

        assert successes == [True]
        assert errors == []
        assert controller.is_running is False

        update_remote_post.execute.assert_called_once()

    finally:
        controller.shutdown()

def test_shutdown_does_not_emit_finished_twice(qtbot):
    """A queued thread-finished callback must not duplicate cleanup."""
    update_remote_post = Mock()

    controller = RemotePostUpdatingController(
        update_remote_post=update_remote_post,
    )

    finished_signals = []
    controller.finished.connect(
        lambda: finished_signals.append(True)
    )

    try:
        controller.start(
            account=Mock(),
            post_id=42,
            content="Updated WordPress content",
        )

        controller.shutdown()

        # Deliver any queued Qt signals after shutdown.
        qtbot.wait(50)

        assert controller.is_running is False
        assert controller._thread is None
        assert controller._worker is None
        assert len(finished_signals) <= 1

    finally:
        controller.shutdown()

def test_controller_rejects_updates_after_shutdown(qtbot):
    """No new update may start after controller shutdown."""
    update_remote_post = Mock()

    controller = RemotePostUpdatingController(
        update_remote_post=update_remote_post,
    )

    controller.shutdown()

    controller.start(
        account=Mock(),
        post_id=42,
        content="Updated WordPress content",
    )

    qtbot.wait(50)

    assert controller.is_running is False
    assert controller._thread is None
    assert controller._worker is None

    update_remote_post.execute.assert_not_called()

def test_controller_reports_error_before_completion(qtbot):
    """The UI must receive the update error before final completion."""
    update_remote_post = Mock()
    update_remote_post.execute.side_effect = RuntimeError(
        "WordPress update failed"
    )

    controller = RemotePostUpdatingController(
        update_remote_post=update_remote_post,
    )

    events = []

    controller.error_occurred.connect(
        lambda message: events.append(("error", message))
    )
    controller.post_updated.connect(
        lambda: events.append(("success", None))
    )
    controller.finished.connect(
        lambda: events.append(("finished", None))
    )

    try:
        with qtbot.waitSignal(controller.finished, timeout=5000):
            controller.start(
                account=Mock(),
                post_id=42,
                content="Updated WordPress content",
            )

        assert events == [
            ("error", "WordPress update failed"),
            ("finished", None),
        ]

        assert controller.is_running is False

    finally:
        controller.shutdown()


def test_controller_forwards_tag_ids(qtbot):
    """The controller forwards tag IDs to the update worker."""
    account = make_account()
    update_remote_post = Mock()

    controller = RemotePostUpdatingController(
        update_remote_post=update_remote_post,
    )

    try:
        with qtbot.waitSignal(
            controller.post_updated,
            timeout=5000,
        ):
            controller.start(
                account=account,
                post_id=123,
                content="Updated content",
                tags=(12, 34),
            )

        qtbot.waitUntil(
            lambda: not controller.is_running,
            timeout=5000,
        )

        update_remote_post.execute.assert_called_once_with(
            account=account,
            post_id=123,
            content="Updated content",
            tags=(12, 34),
        )

        assert controller._worker is None
        assert controller._thread is None

    finally:
        controller.shutdown()


def test_controller_forwards_empty_tags(qtbot):
    """An empty tag tuple removes all tags from the remote post."""
    account = make_account()
    update_remote_post = Mock()

    controller = RemotePostUpdatingController(
        update_remote_post=update_remote_post,
    )

    try:
        with qtbot.waitSignal(
            controller.post_updated,
            timeout=5000,
        ):
            controller.start(
                account=account,
                post_id=123,
                content="Updated content",
                tags=(),
            )

        qtbot.waitUntil(
            lambda: not controller.is_running,
            timeout=5000,
        )

        update_remote_post.execute.assert_called_once_with(
            account=account,
            post_id=123,
            content="Updated content",
            tags=(),
        )

        assert controller._worker is None
        assert controller._thread is None

    finally:
        controller.shutdown()

def test_controller_forwards_featured_media_id(qtbot):
    account = make_account()
    update_remote_post = Mock()

    controller = RemotePostUpdatingController(
        update_remote_post=update_remote_post,
    )

    try:
        with qtbot.waitSignal(
            controller.post_updated,
            timeout=5000,
        ):
            controller.start(
                account=account,
                post_id=123,
                content="Updated content",
                featured_media_id=456,
            )

        qtbot.waitUntil(
            lambda: not controller.is_running,
            timeout=5000,
        )

        update_remote_post.execute.assert_called_once_with(
            account=account,
            post_id=123,
            content="Updated content",
            featured_media_id=456,
        )
    finally:
        controller.shutdown()


@pytest.mark.parametrize(
    "status",
    ("draft", "pending", "private", "publish"),
)
def test_controller_forwards_wordpress_status(qtbot, status):
    account = make_account()
    update_remote_post = Mock()

    controller = RemotePostUpdatingController(
        update_remote_post=update_remote_post,
    )

    try:
        with qtbot.waitSignal(
            controller.post_updated,
            timeout=5000,
        ):
            controller.start(
                account=account,
                post_id=123,
                content="Updated content",
                status=status,
            )

        qtbot.waitUntil(
            lambda: not controller.is_running,
            timeout=5000,
        )

        update_remote_post.execute.assert_called_once_with(
            account=account,
            post_id=123,
            content="Updated content",
            status=status,
        )
    finally:
        controller.shutdown()


def test_controller_combines_status_with_existing_metadata(qtbot):
    account = make_account()
    update_remote_post = Mock()

    controller = RemotePostUpdatingController(
        update_remote_post=update_remote_post,
    )

    try:
        with qtbot.waitSignal(
            controller.post_updated,
            timeout=5000,
        ):
            controller.start(
                account=account,
                post_id=123,
                content="Updated content",
                tags=(10, 20),
                featured_media_id=456,
                status="draft",
            )

        qtbot.waitUntil(
            lambda: not controller.is_running,
            timeout=5000,
        )

        update_remote_post.execute.assert_called_once_with(
            account=account,
            post_id=123,
            content="Updated content",
            tags=(10, 20),
            featured_media_id=456,
            status="draft",
        )
    finally:
        controller.shutdown()



@pytest.mark.parametrize(
    "excerpt",
    [
        "",
        "Sažetak čćžšđ",
    ],
    ids=["clear-excerpt", "replace-excerpt"],
)
def test_controller_forwards_excerpt_to_worker(qtbot, excerpt):
    account = make_account()
    update_remote_post = Mock()

    controller = RemotePostUpdatingController(
        update_remote_post=update_remote_post,
    )

    try:
        with qtbot.waitSignal(
            controller.post_updated,
            timeout=5000,
        ):
            controller.start(
                account=account,
                post_id=123,
                content="Updated content",
                excerpt=excerpt,
            )

        qtbot.waitUntil(
            lambda: not controller.is_running,
            timeout=5000,
        )

        update_remote_post.execute.assert_called_once_with(
            account=account,
            post_id=123,
            content="Updated content",
            excerpt=excerpt,
        )
    finally:
        controller.shutdown()



@pytest.mark.parametrize(
    "title",
    ["Updated title", "Novi naslov čćžšđ"],
)
def test_controller_forwards_title(qtbot, title):
    account = make_account()
    update_remote_post = Mock()

    controller = RemotePostUpdatingController(
        update_remote_post=update_remote_post,
    )

    try:
        with qtbot.waitSignal(
            controller.post_updated,
            timeout=5000,
        ):
            controller.start(
                account=account,
                post_id=123,
                content="Updated content",
                title=title,
            )

        qtbot.waitUntil(
            lambda: not controller.is_running,
            timeout=5000,
        )

        update_remote_post.execute.assert_called_once_with(
            account=account,
            post_id=123,
            content="Updated content",
            title=title,
        )
    finally:
        controller.shutdown()


def test_controller_forwards_title_with_metadata(qtbot):
    account = make_account()
    update_remote_post = Mock()

    controller = RemotePostUpdatingController(
        update_remote_post=update_remote_post,
    )

    try:
        with qtbot.waitSignal(
            controller.post_updated,
            timeout=5000,
        ):
            controller.start(
                account=account,
                post_id=123,
                content="Updated content",
                tags=(12, 34),
                featured_media_id=789,
                status="draft",
                excerpt="Updated excerpt",
                title="Updated title",
            )

        qtbot.waitUntil(
            lambda: not controller.is_running,
            timeout=5000,
        )

        update_remote_post.execute.assert_called_once_with(
            account=account,
            post_id=123,
            content="Updated content",
            tags=(12, 34),
            featured_media_id=789,
            status="draft",
            excerpt="Updated excerpt",
            title="Updated title",
        )
    finally:
        controller.shutdown()
