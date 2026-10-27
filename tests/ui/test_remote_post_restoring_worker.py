
from unittest.mock import Mock

from socialflow.ui.workers.remote_post_restoring_worker import (
    RemotePostRestoringWorker,
)


def test_worker_restores_post_and_emits_success(qtbot):
    use_case = Mock()
    account = Mock()

    worker = RemotePostRestoringWorker(
        restore_remote_post=use_case,
        account=account,
        post_id=123,
    )

    successes = []
    errors = []

    worker.succeeded.connect(lambda: successes.append(True))
    worker.failed.connect(errors.append)

    with qtbot.waitSignal(worker.finished, timeout=1000):
        worker.run()

    use_case.execute.assert_called_once_with(
        account=account,
        post_id=123,
    )
    assert successes == [True]
    assert errors == []


def test_worker_reports_failure_and_finishes(qtbot):
    use_case = Mock()
    use_case.execute.side_effect = RuntimeError(
        "WordPress post restore failed (HTTP 403)."
    )

    worker = RemotePostRestoringWorker(
        restore_remote_post=use_case,
        account=Mock(),
        post_id=123,
    )

    successes = []
    errors = []

    worker.succeeded.connect(lambda: successes.append(True))
    worker.failed.connect(errors.append)

    with qtbot.waitSignal(worker.finished, timeout=1000):
        worker.run()

    assert successes == []
    assert errors == [
        "WordPress post restore failed (HTTP 403)."
    ]
    use_case.execute.assert_called_once()
