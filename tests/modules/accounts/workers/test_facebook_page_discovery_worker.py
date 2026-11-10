
from unittest.mock import Mock

from socialflow.modules.accounts.workers.facebook_page_discovery_worker import (
    FacebookPageDiscoveryWorker,
)
from socialflow.modules.facebook.api.facebook_api_error import (
    FacebookApiError,
)
from socialflow.modules.facebook.services.facebook_page_discovery_service import (
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


def create_worker(service: Mock) -> FacebookPageDiscoveryWorker:
    return FacebookPageDiscoveryWorker(service, USER_TOKEN)


def test_worker_emits_discovered_pages(qtbot) -> None:
    service = create_service()
    pages = [
        DiscoveredFacebookPage(
            page=FacebookPage(id="123", name="My Page"),
            access_token="sensitive-page-token",
        ),
    ]
    service.discover.return_value = pages

    worker = create_worker(service)

    with qtbot.waitSignal(worker.finished, timeout=1000) as signal:
        worker.run()

    service.discover.assert_called_once_with(USER_TOKEN)
    assert signal.args == [pages]


def test_worker_emits_empty_discovery_result(qtbot) -> None:
    service = create_service()
    service.discover.return_value = []

    worker = create_worker(service)

    with qtbot.waitSignal(worker.finished, timeout=1000) as signal:
        worker.run()

    assert signal.args == [[]]


def test_worker_reports_api_error_safely(qtbot) -> None:
    service = create_service()
    service.discover.side_effect = FacebookApiError(
        message="Sensitive token: " + USER_TOKEN,
        status_code=401,
        code=190,
    )

    worker = create_worker(service)

    with (
        qtbot.waitSignal(worker.failed, timeout=1000) as signal,
        qtbot.assertNotEmitted(worker.finished),
    ):
        worker.run()

    assert signal.args == [
        "Could not discover Facebook Pages. "
        "Check your Facebook access token and permissions."
    ]
    assert USER_TOKEN not in signal.args[0]


def test_worker_reports_unexpected_error_safely(qtbot) -> None:
    service = create_service()
    service.discover.side_effect = RuntimeError(
        "Sensitive internal token: " + USER_TOKEN
    )

    worker = create_worker(service)

    with (
        qtbot.waitSignal(worker.failed, timeout=1000) as signal,
        qtbot.assertNotEmitted(worker.finished),
    ):
        worker.run()

    assert signal.args == [
        "Facebook Page discovery failed unexpectedly."
    ]
    assert USER_TOKEN not in signal.args[0]


def test_worker_clears_user_token_after_success() -> None:
    service = create_service()
    service.discover.return_value = []

    worker = create_worker(service)

    worker.run()

    assert worker._user_access_token == ""


def test_worker_clears_user_token_after_failure() -> None:
    service = create_service()
    service.discover.side_effect = FacebookApiError(
        message="Authentication failed.",
    )

    worker = create_worker(service)

    worker.run()

    assert worker._user_access_token == ""


def test_worker_calls_discovery_only_once() -> None:
    service = create_service()
    service.discover.return_value = []

    worker = create_worker(service)
    worker.run()

    service.discover.assert_called_once_with(USER_TOKEN)


def test_worker_does_not_expose_token_in_repr() -> None:
    service = create_service()
    worker = create_worker(service)

    assert USER_TOKEN not in repr(worker)
