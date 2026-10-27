
from threading import Event
from unittest.mock import Mock

from socialflow.domain.account.account import Account
from socialflow.domain.publishing.destination import (
    PublishingDestination,
)
from socialflow.ui.workers.remote_trashed_post_loading_controller import (
    RemoteTrashedPostLoadingController,
)


def make_account():
    return Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
    )


def test_controller_starts_idle():
    controller = RemoteTrashedPostLoadingController(
        list_trashed_remote_posts=Mock(),
    )

    assert not controller.is_running
    controller.shutdown()


def test_controller_loads_trashed_posts_in_background(qtbot):
    account = make_account()
    use_case = Mock()
    use_case.execute.return_value = ()

    controller = RemoteTrashedPostLoadingController(
        list_trashed_remote_posts=use_case,
    )

    try:
        with qtbot.waitSignal(
            controller.posts_ready,
            timeout=5000,
        ) as signal:
            controller.start(account)

        assert signal.args == [()]

        qtbot.waitUntil(
            lambda: not controller.is_running,
            timeout=5000,
        )

        use_case.execute.assert_called_once_with(
            account=account,
            limit=50,
        )
    finally:
        controller.shutdown()


def test_controller_reports_trash_retrieval_failure(qtbot):
    account = make_account()
    use_case = Mock()
    use_case.execute.side_effect = RuntimeError(
        "WordPress Trash retrieval failed"
    )

    controller = RemoteTrashedPostLoadingController(
        list_trashed_remote_posts=use_case,
    )

    try:
        with qtbot.waitSignal(
            controller.error_occurred,
            timeout=5000,
        ) as signal:
            controller.start(account)

        assert signal.args == [
            "WordPress Trash retrieval failed"
        ]

        qtbot.waitUntil(
            lambda: not controller.is_running,
            timeout=5000,
        )
    finally:
        controller.shutdown()


def test_controller_prevents_concurrent_trash_loading(qtbot):
    started = Event()
    release = Event()

    def retrieve_posts(**_kwargs):
        started.set()
        if not release.wait(timeout=5):
            raise TimeoutError("Trash loader was not released")
        return ()

    use_case = Mock()
    use_case.execute.side_effect = retrieve_posts

    controller = RemoteTrashedPostLoadingController(
        list_trashed_remote_posts=use_case,
    )

    try:
        controller.start(make_account())

        qtbot.waitUntil(
            started.is_set,
            timeout=5000,
        )

        assert controller.is_running

        controller.start(make_account())

        assert use_case.execute.call_count == 1
    finally:
        release.set()
        controller.shutdown()


def test_controller_shutdown_waits_for_active_worker(qtbot):
    started = Event()
    release = Event()

    def retrieve_posts(**_kwargs):
        started.set()
        if not release.wait(timeout=5):
            raise TimeoutError("Trash loader was not released")
        return ()

    use_case = Mock()
    use_case.execute.side_effect = retrieve_posts

    controller = RemoteTrashedPostLoadingController(
        list_trashed_remote_posts=use_case,
    )

    try:
        controller.start(make_account())

        qtbot.waitUntil(
            started.is_set,
            timeout=5000,
        )

        release.set()
        controller.shutdown()

        assert not controller.is_running
        assert use_case.execute.call_count == 1
    finally:
        release.set()
        controller.shutdown()


def test_shutdown_suppresses_queued_trashed_posts(qtbot):
    retrieval_complete = Event()

    def retrieve_posts(**_kwargs):
        retrieval_complete.set()
        return ()

    use_case = Mock()
    use_case.execute.side_effect = retrieve_posts

    controller = RemoteTrashedPostLoadingController(
        list_trashed_remote_posts=use_case,
    )

    posts_listener = Mock()
    controller.posts_ready.connect(posts_listener)

    try:
        controller.start(make_account())

        assert retrieval_complete.wait(timeout=3)

        controller.shutdown()
        qtbot.wait(100)

        posts_listener.assert_not_called()
    finally:
        controller.shutdown()


def test_shutdown_suppresses_queued_trash_error(qtbot):
    retrieval_complete = Event()

    def retrieve_posts(**_kwargs):
        retrieval_complete.set()
        raise RuntimeError("Trash retrieval failed")

    use_case = Mock()
    use_case.execute.side_effect = retrieve_posts

    controller = RemoteTrashedPostLoadingController(
        list_trashed_remote_posts=use_case,
    )

    error_listener = Mock()
    controller.error_occurred.connect(error_listener)

    try:
        controller.start(make_account())

        assert retrieval_complete.wait(timeout=3)

        controller.shutdown()
        qtbot.wait(100)

        error_listener.assert_not_called()
    finally:
        controller.shutdown()


def test_controller_rejects_start_after_shutdown():
    use_case = Mock()

    controller = RemoteTrashedPostLoadingController(
        list_trashed_remote_posts=use_case,
    )

    controller.shutdown()
    controller.start(make_account())

    assert not controller.is_running
    use_case.execute.assert_not_called()
