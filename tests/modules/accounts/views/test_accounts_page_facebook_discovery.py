
from threading import Event, Thread
from unittest.mock import Mock

from socialflow.core.destination import PublishingDestination
from socialflow.modules.accounts.repositories.in_memory_account_repository import (
    InMemoryAccountRepository,
)
from socialflow.modules.accounts.services.add_account import AddAccount
from socialflow.modules.accounts.services.list_accounts import ListAccounts
from socialflow.modules.accounts.services.remove_account import RemoveAccount
from socialflow.modules.accounts.services.update_account import UpdateAccount
from socialflow.modules.accounts.views.accounts_page import AccountsPage
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


def create_page(
    discovery_service: FacebookPageDiscoveryService | None = None,
) -> AccountsPage:
    repository = InMemoryAccountRepository()

    return AccountsPage(
        add_account=AddAccount(repository),
        list_accounts=ListAccounts(repository),
        remove_account=RemoveAccount(repository),
        update_account=UpdateAccount(repository),
        facebook_page_discovery_service=discovery_service,
    )


def select_facebook(page: AccountsPage) -> None:
    index = page.account_form.destination_input.findData(
        PublishingDestination.FACEBOOK
    )
    assert index >= 0
    page.account_form.destination_input.setCurrentIndex(index)


def create_discovered_pages() -> list[DiscoveredFacebookPage]:
    return [
        DiscoveredFacebookPage(
            page=FacebookPage(id="123", name="First Page"),
            access_token="secret-page-token",
        ),
    ]


def test_discovery_populates_accounts_page(qtbot) -> None:
    service = Mock(spec=FacebookPageDiscoveryService)
    service.discover.return_value = create_discovered_pages()

    page = create_page(service)
    qtbot.addWidget(page)
    select_facebook(page)

    page.account_form.facebook_user_token_input.setText(USER_TOKEN)

    controller = page._facebook_discovery_controller
    assert controller is not None

    with qtbot.waitSignals(
        [controller.result_ready, controller.finished],
        timeout=3000,
        order="strict",
    ):
        page.account_form.facebook_discover_button.click()

    service.discover.assert_called_once_with(USER_TOKEN)

    assert page.account_form.facebook_page_selector.count() == 2
    assert page.account_form.facebook_page_selector.itemText(1) == (
        "First Page"
    )
    assert page.account_form.facebook_user_token_input.text() == ""
    assert page.account_form.facebook_discover_button.isEnabled()

    page.account_form.facebook_page_selector.setCurrentIndex(1)

    assert page.account_form.facebook_page_id_input.text() == "123"
    assert page.account_form.facebook_page_name_input.text() == "First Page"
    assert (
        page.account_form.selected_facebook_page_token()
        == "secret-page-token"
    )


def test_discovery_api_error_restores_button(qtbot) -> None:
    service = Mock(spec=FacebookPageDiscoveryService)
    service.discover.side_effect = FacebookApiError(
        message="Sensitive authentication failure.",
        status_code=401,
        code=190,
    )

    page = create_page(service)
    qtbot.addWidget(page)
    select_facebook(page)

    page.account_form.facebook_user_token_input.setText(USER_TOKEN)

    controller = page._facebook_discovery_controller
    assert controller is not None

    with qtbot.waitSignals(
        [controller.error_occurred, controller.finished],
        timeout=3000,
        order="strict",
    ):
        page.account_form.facebook_discover_button.click()

    assert page.account_form.facebook_discover_button.isEnabled()
    assert page.account_form.facebook_user_token_input.text() == ""
    assert page.account_form.facebook_page_selector.count() == 1
    assert "Sensitive" not in page.account_status.text()


def test_discovery_without_service_reports_error(qtbot) -> None:
    page = create_page()
    qtbot.addWidget(page)
    select_facebook(page)

    page.account_form.facebook_user_token_input.setText(USER_TOKEN)
    page.account_form.facebook_discover_button.click()

    assert page._facebook_discovery_controller is None
    assert page.account_form.facebook_discover_button.isEnabled()
    assert page.account_status.property("status") == "error"
    assert page.account_form.facebook_user_token_input.text() == ""


def test_discovery_ignores_overlapping_requests(qtbot) -> None:
    service = Mock(spec=FacebookPageDiscoveryService)

    started = Event()
    release = Event()

    def discover(_token: str):
        started.set()
        if not release.wait(timeout=3):
            raise TimeoutError("Test worker was not released.")
        return create_discovered_pages()

    service.discover.side_effect = discover

    page = create_page(service)
    qtbot.addWidget(page)
    select_facebook(page)

    controller = page._facebook_discovery_controller
    assert controller is not None

    try:
        page.account_form.facebook_user_token_input.setText(USER_TOKEN)
        page.account_form.facebook_discover_button.click()

        assert started.wait(timeout=2)
        assert controller.is_running

        page._handle_facebook_discovery_requested("another-token")

        assert service.discover.call_count == 1

        with qtbot.waitSignals(
            [controller.result_ready, controller.finished],
            timeout=3000,
            order="strict",
        ):
            release.set()

        assert not controller.is_running
        assert page.account_form.facebook_discover_button.isEnabled()

    finally:
        release.set()
        page.shutdown()


def test_discovery_shutdown_waits_for_worker(qtbot) -> None:
    service = Mock(spec=FacebookPageDiscoveryService)

    started = Event()
    release = Event()

    def discover(_token: str):
        started.set()
        if not release.wait(timeout=3):
            raise TimeoutError("Test worker was not released.")
        return []

    service.discover.side_effect = discover

    page = create_page(service)
    qtbot.addWidget(page)
    select_facebook(page)

    controller = page._facebook_discovery_controller
    assert controller is not None

    page.account_form.facebook_user_token_input.setText(USER_TOKEN)
    page.account_form.facebook_discover_button.click()

    try:
        assert started.wait(timeout=2)
        assert controller.is_running

        releaser = Thread(target=release.set)
        releaser.start()

        try:
            page.shutdown()
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
        page.shutdown()
