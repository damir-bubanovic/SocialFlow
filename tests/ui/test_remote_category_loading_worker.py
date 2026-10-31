
from unittest.mock import Mock

from socialflow.application.categories.list_remote_categories import (
    ListRemoteCategories,
)
from socialflow.domain.post.remote_category import RemoteCategory
from socialflow.ui.workers.remote_category_loading_worker import (
    RemoteCategoryLoadingWorker,
)


def test_worker_emits_categories(qtbot):
    account = Mock()
    categories = (
        RemoteCategory(10, "Technology"),
        RemoteCategory(20, "Python", parent_id=10),
    )

    use_case = Mock(spec=ListRemoteCategories)
    use_case.execute.return_value = categories

    worker = RemoteCategoryLoadingWorker(use_case, account)

    with qtbot.waitSignal(worker.finished, timeout=1000) as signal:
        worker.run()

    assert signal.args == [categories]
    use_case.execute.assert_called_once_with(account)


def test_worker_emits_empty_category_list(qtbot):
    use_case = Mock(spec=ListRemoteCategories)
    use_case.execute.return_value = ()

    worker = RemoteCategoryLoadingWorker(use_case, Mock())

    with qtbot.waitSignal(worker.finished, timeout=1000) as signal:
        worker.run()

    assert signal.args == [()]


def test_worker_emits_error_without_success(qtbot):
    use_case = Mock(spec=ListRemoteCategories)
    use_case.execute.side_effect = ConnectionError(
        "WordPress unavailable"
    )

    worker = RemoteCategoryLoadingWorker(use_case, Mock())

    successes = []
    worker.finished.connect(lambda result: successes.append(result))

    with qtbot.waitSignal(worker.failed, timeout=1000) as signal:
        worker.run()

    assert "WordPress unavailable" in signal.args[0]
    assert successes == []
