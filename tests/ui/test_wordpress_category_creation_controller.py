
from unittest.mock import Mock

import pytest

from socialflow.domain.post.remote_category import RemoteCategory
from socialflow.infrastructure.wordpress.wordpress_category_provider import (
    WordPressCategoryProvider,
)
from socialflow.ui.workers.wordpress_category_creation_controller import (
    WordPressCategoryCreationController,
)


def test_controller_creates_category(qtbot):
    category = RemoteCategory(15, "Technology")

    provider = Mock(spec=WordPressCategoryProvider)
    provider.create_category.return_value = category

    controller = WordPressCategoryCreationController(provider)
    results = []
    controller.category_created.connect(results.append)

    with qtbot.waitSignal(controller.finished, timeout=3000):
        controller.start(Mock(), "Technology")

    assert results == [category]
    assert controller.is_running is False


def test_controller_reports_creation_error(qtbot):
    provider = Mock(spec=WordPressCategoryProvider)
    provider.create_category.side_effect = RuntimeError(
        "Authentication failed"
    )

    controller = WordPressCategoryCreationController(provider)
    errors = []
    controller.error_occurred.connect(errors.append)

    with qtbot.waitSignal(controller.finished, timeout=3000):
        controller.start(Mock(), "Technology")

    assert errors == ["Authentication failed"]
    assert controller.is_running is False


def test_controller_rejects_blank_name():
    provider = Mock(spec=WordPressCategoryProvider)
    controller = WordPressCategoryCreationController(provider)

    with pytest.raises(ValueError, match="Category name"):
        controller.start(Mock(), "   ")

    assert controller.is_running is False


def test_controller_rejects_invalid_parent():
    provider = Mock(spec=WordPressCategoryProvider)
    controller = WordPressCategoryCreationController(provider)

    with pytest.raises(ValueError, match="Parent category"):
        controller.start(Mock(), "Python", parent_id=-1)

    assert controller.is_running is False


def test_controller_can_create_again(qtbot):
    provider = Mock(spec=WordPressCategoryProvider)
    provider.create_category.return_value = RemoteCategory(
        15, "Technology"
    )

    controller = WordPressCategoryCreationController(provider)

    with qtbot.waitSignal(controller.finished, timeout=3000):
        controller.start(Mock(), "Technology")

    with qtbot.waitSignal(controller.finished, timeout=3000):
        controller.start(Mock(), "Technology")

    assert provider.create_category.call_count == 2


def test_controller_shutdown_prevents_new_requests():
    provider = Mock(spec=WordPressCategoryProvider)
    controller = WordPressCategoryCreationController(provider)

    controller.shutdown()
    controller.start(Mock(), "Technology")

    assert controller.is_running is False
    provider.create_category.assert_not_called()
