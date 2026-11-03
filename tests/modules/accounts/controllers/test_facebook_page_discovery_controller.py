
from threading import Event, Thread
from unittest.mock import Mock

from socialflow.modules.accounts.controllers.facebook_page_discovery_controller import (
    FacebookPageDiscoveryController,
)
from socialflow.modules.facebook.api.facebook_api_error import (
    FacebookApiError,
)
from socialflow.modules.facebook.api.facebook_page_discovery_service import (
    FacebookPageDiscoveryService,
)
from socialflow.modules.facebook.models.discovered_facebook_page import (
    DiscoveredFacebookPage,
)
from socialflow.modules.facebook.models.facebook_page import (
    FacebookPage,
)


USER_TOKEN = "sensitive-user-token"


def create_service() -> Mock:
    return Mock(spec=FacebookPageDiscoveryService)


def create_pages() -> list[DiscoveredFacebookPage]:
    return [
        DiscoveredFacebookPage(
            page=FacebookPage(id="123", name="My Page"),
            access_token="sensitive-page-token",
        ),
    ]


def test_controller_emits_discovered_pages(qtbot) -> None:
    service = create_service()
    pages = create_pages()
    service.discover.return_value = pages

    controller = FacebookPageDiscoveryController(service)
    result_listener = Mock()
    controller.result_ready.connect(result_listener)

    with qtbot.waitSignals(
        [controller.result_ready, controller.finished],
        timeout=3000,
        order="strict",
    ):
        controller.start(USER_TOKEN)

    service.discover.assert_called_once_with(USER_TOKEN)
    result_listener.assert_called_once_with(pages)
    assert not controller.is_running
    assert controller._thread is None
    assert controller._worker is None


def test_controller_emits_empty_discovery_result(qtbot) -> None:
    service = create_service()
    service.discover.return_value = []

    controller = FacebookPageDiscoveryController(service)
    result_listener = Mock()

    controller.result_ready.connect(result_listener)

    with qtbot.waitSignals(
        [controller.result_ready, controller.finished],
        timeout=3000,
        order="strict",
    ):
        controller.start(USER_TOKEN)

    result_listener.assert_called_once_with([])
    service.discover.assert_called_once_with(USER_TOKEN)

    assert not controller.is_running
    assert controller._thread is None
    assert controller._worker is None


def test_controller_reports_api_error(qtbot) -> None:
    service = create_service()
    service.discover.side_effect = FacebookApiError(
        message="Sensitive authentication details.",
        status_code=401,
        code=190,
    )

    controller = FacebookPageDiscoveryController(service)
    error_listener = Mock()
    controller.error_occurred.connect(error_listener)

    with qtbot.waitSignals(
        [controller.error_occurred, controller.finished],
        timeout=3000,
        order="strict",
    ):
        controller.start(USER_TOKEN)

    error_listener.assert_called_once_with(
        "Could not discover Facebook Pages. "
        "Check your Facebook access token and permissions."
    )
    assert not controller.is_running
    assert controller._thread is None
    assert controller._worker is None


def test_controller_reports_unexpected_error(qtbot) -> None:
    service = create_service()
    service.discover.side_effect = RuntimeError(
        "Sensitive internal details."
    )

    controller = FacebookPageDiscoveryController(service)
    error_listener = Mock()
    controller.error_occurred.connect(error_listener)

    with qtbot.waitSignals(
        [controller.error_occurred, controller.finished],
        timeout=3000,
        order="strict",
    ):
        controller.start(USER_TOKEN)

    error_listener.assert_called_once_with(
        "Facebook Page discovery failed unexpectedly."
    )
    assert not controller.is_running


def test_controller_prevents_concurrent_discovery(qtbot) -> None:
    service = create_service()
    started = Event()
    release = Event()
    pages = create_pages()

    def discover(_token: str):
        started.set()
        if not release.wait(timeout=3):
            raise TimeoutError("Test worker was not released.")
        return pages

    service.discover.side_effect = discover

    controller = FacebookPageDiscoveryController(service)

    try:
        controller.start(USER_TOKEN)

        assert started.wait(timeout=2)
        assert controller.is_running

        controller.start("second-user-token")
        assert service.discover.call_count == 1

        with qtbot.waitSignals(
            [controller.result_ready, controller.finished],
            timeout=3000,
            order="strict",
        ):
            release.set()

        service.discover.assert_called_once_with(USER_TOKEN)
        assert not controller.is_running
        assert controller._thread is None
        assert controller._worker is None

    finally:
        release.set()
        controller.shutdown()


def test_controller_can_retry_after_failure(qtbot) -> None:
    service = create_service()
    pages = create_pages()

    service.discover.side_effect = [
        FacebookApiError(message="Authentication failed."),
        pages,
    ]

    controller = FacebookPageDiscoveryController(service)

    try:
        with qtbot.waitSignals(
            [controller.error_occurred, controller.finished],
            timeout=3000,
            order="strict",
        ):
            controller.start(USER_TOKEN)

        assert not controller.is_running

        with qtbot.waitSignals(
            [controller.result_ready, controller.finished],
            timeout=3000,
            order="strict",
        ):
            controller.start(USER_TOKEN)

        assert service.discover.call_count == 2
        assert not controller.is_running

    finally:
        controller.shutdown()


def test_controller_shutdown_waits_for_active_discovery(qtbot) -> None:
    service = create_service()
    started = Event()
    release = Event()

    def discover(_token: str):
        started.set()
        if not release.wait(timeout=3):
            raise TimeoutError("Test worker was not released.")
        return create_pages()

    service.discover.side_effect = discover

    controller = FacebookPageDiscoveryController(service)
    controller.start(USER_TOKEN)

    try:
        assert started.wait(timeout=2)
        assert controller.is_running

        releaser = Thread(target=release.set)
        releaser.start()

        try:
            controller.shutdown()
        finally:
            release.set()
            releaser.join(timeout=2)

        qtbot.waitUntil(
            lambda: not controller.is_running,
            timeout=3000,
        )

        assert controller._thread is None
        assert controller._worker is None

    finally:
        release.set()
        controller.shutdown()


def test_controller_repeated_shutdown_is_safe(qtbot) -> None:
    service = create_service()
    service.discover.return_value = []

    controller = FacebookPageDiscoveryController(service)

    with qtbot.waitSignals(
        [controller.result_ready, controller.finished],
        timeout=3000,
        order="strict",
    ):
        controller.start(USER_TOKEN)

    controller.shutdown()
    controller.shutdown()

    assert not controller.is_running
    assert controller._thread is None
    assert controller._worker is None
    service.discover.assert_called_once_with(USER_TOKEN)
