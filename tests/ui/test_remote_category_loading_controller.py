
from unittest.mock import Mock

from socialflow.application.categories.list_remote_categories import (
    ListRemoteCategories,
)
from socialflow.domain.post.remote_category import RemoteCategory
from socialflow.ui.workers.remote_category_loading_controller import (
    RemoteCategoryLoadingController,
)


def test_controller_loads_categories_in_background(qtbot):
    use_case = Mock(spec=ListRemoteCategories)
    use_case.execute.return_value = (
        RemoteCategory(10, "Technology"),
        RemoteCategory(20, "Python", parent_id=10),
    )

    controller = RemoteCategoryLoadingController(use_case)

    results = []
    controller.categories_ready.connect(results.append)

    with qtbot.waitSignal(controller.finished, timeout=3000):
        controller.start(Mock())

    assert results == [
        (
            RemoteCategory(10, "Technology"),
            RemoteCategory(20, "Python", parent_id=10),
        )
    ]
    assert controller.is_running is False


def test_controller_handles_errors(qtbot):
    use_case = Mock(spec=ListRemoteCategories)
    use_case.execute.side_effect = RuntimeError(
        "Authentication failed"
    )

    controller = RemoteCategoryLoadingController(use_case)

    errors = []
    controller.error_occurred.connect(errors.append)

    with qtbot.waitSignal(controller.finished, timeout=3000):
        controller.start(Mock())

    assert errors == ["Authentication failed"]
    assert controller.is_running is False


def test_controller_ignores_concurrent_start(qtbot):
    use_case = Mock(spec=ListRemoteCategories)
    use_case.execute.return_value = ()

    controller = RemoteCategoryLoadingController(use_case)

    with qtbot.waitSignal(controller.finished, timeout=3000):
        controller.start(Mock())
        controller.start(Mock())

    assert use_case.execute.call_count == 1


def test_controller_can_load_again_after_completion(qtbot):
    use_case = Mock(spec=ListRemoteCategories)
    use_case.execute.return_value = ()

    controller = RemoteCategoryLoadingController(use_case)

    with qtbot.waitSignal(controller.finished, timeout=3000):
        controller.start(Mock())

    with qtbot.waitSignal(controller.finished, timeout=3000):
        controller.start(Mock())

    assert use_case.execute.call_count == 2


def test_controller_shutdown_prevents_new_requests():
    use_case = Mock(spec=ListRemoteCategories)

    controller = RemoteCategoryLoadingController(use_case)
    controller.shutdown()
    controller.start(Mock())

    assert controller.is_running is False
    use_case.execute.assert_not_called()
