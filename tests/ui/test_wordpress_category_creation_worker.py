
from unittest.mock import Mock

from socialflow.domain.post.remote_category import RemoteCategory
from socialflow.infrastructure.wordpress.wordpress_category_provider import (
    WordPressCategoryProvider,
)
from socialflow.ui.workers.wordpress_category_creation_worker import (
    WordPressCategoryCreationWorker,
)


def test_worker_creates_top_level_category(qtbot):
    account = Mock()
    category = RemoteCategory(12, "Technology")

    provider = Mock(spec=WordPressCategoryProvider)
    provider.create_category.return_value = category

    worker = WordPressCategoryCreationWorker(
        provider, account, "Technology"
    )

    with qtbot.waitSignal(worker.created, timeout=1000) as signal:
        worker.run()

    assert signal.args == [category]
    provider.create_category.assert_called_once_with(
        account=account,
        name="Technology",
        parent_id=0,
    )


def test_worker_creates_subcategory(qtbot):
    account = Mock()
    category = RemoteCategory(22, "Python", parent_id=12)

    provider = Mock(spec=WordPressCategoryProvider)
    provider.create_category.return_value = category

    worker = WordPressCategoryCreationWorker(
        provider, account, "Python", parent_id=12
    )

    with qtbot.waitSignal(worker.created, timeout=1000) as signal:
        worker.run()

    assert signal.args == [category]
    assert category.parent_id == 12


def test_worker_emits_error_without_success(qtbot):
    provider = Mock(spec=WordPressCategoryProvider)
    provider.create_category.side_effect = RuntimeError(
        "WordPress rejected category creation"
    )

    worker = WordPressCategoryCreationWorker(
        provider, Mock(), "Technology"
    )

    created = []
    worker.created.connect(created.append)

    with qtbot.waitSignal(worker.failed, timeout=1000) as signal:
        worker.run()

    assert "WordPress rejected" in signal.args[0]
    assert created == []
