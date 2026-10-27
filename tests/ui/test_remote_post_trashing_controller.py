
from threading import Event
from unittest.mock import Mock

from socialflow.ui.workers.remote_post_trashing_controller import (
    RemotePostTrashingController,
)


def test_controller_starts_idle():
    controller = RemotePostTrashingController(
        trash_remote_post=Mock(),
    )

    assert not controller.is_running
    controller.shutdown()


def test_controller_trashes_post_in_background(qtbot):
    account = Mock()
    use_case = Mock()

    controller = RemotePostTrashingController(
        trash_remote_post=use_case,
    )

    try:
        with qtbot.waitSignal(
            controller.post_trashed,
            timeout=5000,
        ):
            controller.start(
                account=account,
                post_id=123,
            )

        qtbot.waitUntil(
            lambda: not controller.is_running,
            timeout=5000,
        )

        use_case.execute.assert_called_once_with(
            account=account,
            post_id=123,
        )
    finally:
        controller.shutdown()


def test_controller_reports_trash_failure(qtbot):
    use_case = Mock()
    use_case.execute.side_effect = RuntimeError(
        "WordPress post trash failed (HTTP 403)."
    )

    controller = RemotePostTrashingController(
        trash_remote_post=use_case,
    )

    try:
        with qtbot.waitSignal(
            controller.error_occurred,
            timeout=5000,
        ) as signal:
            controller.start(
                account=Mock(),
                post_id=123,
            )

        assert signal.args == [
            "WordPress post trash failed (HTTP 403)."
        ]

        qtbot.waitUntil(
            lambda: not controller.is_running,
            timeout=5000,
        )
    finally:
        controller.shutdown()


def test_controller_prevents_concurrent_trash_operations(qtbot):
    started = Event()
    release = Event()

    def trash_post(**_kwargs):
        started.set()
        if not release.wait(timeout=5):
            raise TimeoutError("Trash worker was not released")

    use_case = Mock()
    use_case.execute.side_effect = trash_post

    controller = RemotePostTrashingController(
        trash_remote_post=use_case,
    )

    try:
        controller.start(
            account=Mock(),
            post_id=123,
        )

        qtbot.waitUntil(started.is_set, timeout=5000)

        assert controller.is_running

        controller.start(
            account=Mock(),
            post_id=456,
        )

        assert use_case.execute.call_count == 1
    finally:
        release.set()
        controller.shutdown()


def test_controller_rejects_start_after_shutdown():
    use_case = Mock()

    controller = RemotePostTrashingController(
        trash_remote_post=use_case,
    )

    controller.shutdown()
    controller.start(
        account=Mock(),
        post_id=123,
    )

    assert not controller.is_running
    use_case.execute.assert_not_called()
