from threading import Event, Thread
from unittest.mock import Mock

from socialflow.core.destination import PublishingDestination
from socialflow.modules.accounts.models.account import Account
from socialflow.modules.accounts.models.connection_result import (
    ConnectionResult,
)
from socialflow.modules.accounts.models.connection_status import (
    ConnectionStatus,
)
from socialflow.modules.accounts.repositories.in_memory_account_repository import (
    InMemoryAccountRepository,
)
from socialflow.modules.accounts.services.add_account import AddAccount
from socialflow.modules.accounts.services.connection_verifier import (
    ConnectionVerifier,
)
from socialflow.modules.accounts.services.credential_errors import (
    CredentialStorageError,
)
from socialflow.modules.accounts.services.list_accounts import ListAccounts
from socialflow.modules.accounts.services.remove_account import RemoveAccount
from socialflow.modules.accounts.services.update_account import UpdateAccount
from socialflow.modules.accounts.views.accounts_page import AccountsPage


def create_page(
    instagram_verifier: ConnectionVerifier | None = None,
) -> tuple[AccountsPage, Account]:
    repository = InMemoryAccountRepository()
    account = Account(
        name="Test Instagram Account",
        destination=PublishingDestination.INSTAGRAM,
    )
    repository.add(account)

    page = AccountsPage(
        add_account=AddAccount(repository),
        list_accounts=ListAccounts(repository),
        remove_account=RemoveAccount(repository),
        update_account=UpdateAccount(repository),
        instagram_connection_verifier=instagram_verifier,
    )
    return page, account


def test_instagram_verify_button_requires_verifier(qtbot) -> None:
    page, _ = create_page()
    qtbot.addWidget(page)
    page.account_list.setCurrentRow(0)

    assert not page.verify_button.isEnabled()

    verifier = Mock(spec=ConnectionVerifier)
    configured_page, _ = create_page(verifier)
    qtbot.addWidget(configured_page)
    configured_page.account_list.setCurrentRow(0)

    assert configured_page.verify_button.isEnabled()


def test_instagram_verification_success(qtbot) -> None:
    verifier = Mock(spec=ConnectionVerifier)
    verifier.verify.return_value = ConnectionResult(
        status=ConnectionStatus.CONNECTED,
        message="Instagram account connection verified successfully.",
    )

    page, account = create_page(verifier)
    qtbot.addWidget(page)
    page.account_list.setCurrentRow(0)

    controller = page._instagram_verification_controller
    assert controller is not None

    with qtbot.waitSignal(controller.finished, timeout=3000):
        page.verify_button.click()

    verifier.verify.assert_called_once_with(account)
    assert not controller.is_running
    assert page.account_status.property("status") == "success"
    assert page.account_status.text() == (
        "Instagram account connection verified successfully."
    )
    assert page.verify_button.isEnabled()


def test_instagram_verification_invalid_credentials(qtbot) -> None:
    verifier = Mock(spec=ConnectionVerifier)
    verifier.verify.return_value = ConnectionResult(
        status=ConnectionStatus.INVALID_CREDENTIALS,
        message="Instagram access token is invalid.",
    )

    page, account = create_page(verifier)
    qtbot.addWidget(page)
    page.account_list.setCurrentRow(0)

    controller = page._instagram_verification_controller
    assert controller is not None

    with qtbot.waitSignal(controller.finished, timeout=3000):
        page.verify_button.click()

    verifier.verify.assert_called_once_with(account)
    assert page.account_status.property("status") == "error"
    assert page.account_status.text() == (
        "Instagram access token is invalid."
    )
    assert page.verify_button.isEnabled()


def test_instagram_verification_storage_error_is_sanitized(qtbot) -> None:
    verifier = Mock(spec=ConnectionVerifier)
    verifier.verify.side_effect = CredentialStorageError(
        "SECRET_KEYRING_DETAILS"
    )

    page, account = create_page(verifier)
    qtbot.addWidget(page)
    page.account_list.setCurrentRow(0)

    controller = page._instagram_verification_controller
    assert controller is not None

    with qtbot.waitSignal(controller.finished, timeout=3000):
        page.verify_button.click()

    verifier.verify.assert_called_once_with(account)
    assert page.account_status.property("status") == "error"
    assert page.account_status.text() == (
        "Could not access stored Instagram credentials."
    )
    assert "SECRET_KEYRING_DETAILS" not in page.account_status.text()
    assert page.verify_button.isEnabled()


def test_instagram_verification_prevents_overlapping_requests(qtbot) -> None:
    started = Event()
    release = Event()
    verifier = Mock(spec=ConnectionVerifier)

    def verify(_account: Account) -> ConnectionResult:
        started.set()
        if not release.wait(timeout=3):
            raise RuntimeError("Verification timed out.")
        return ConnectionResult(
            status=ConnectionStatus.CONNECTED,
            message="Instagram account connection verified.",
        )

    verifier.verify.side_effect = verify

    page, account = create_page(verifier)
    qtbot.addWidget(page)
    page.account_list.setCurrentRow(0)

    controller = page._instagram_verification_controller
    assert controller is not None

    try:
        page.verify_button.click()

        assert started.wait(timeout=2)
        assert controller.is_running
        assert page.verification_is_running
        assert not page.verify_button.isEnabled()

        page._handle_verify_connection()
        assert verifier.verify.call_count == 1

        with qtbot.waitSignal(controller.finished, timeout=3000):
            release.set()

        assert not controller.is_running
        assert not page.verification_is_running
        assert page.verify_button.isEnabled()
        verifier.verify.assert_called_once_with(account)
    finally:
        release.set()
        page.shutdown()


def test_instagram_verification_shutdown_waits_for_worker(qtbot) -> None:
    started = Event()
    release = Event()
    verifier = Mock(spec=ConnectionVerifier)

    def verify(_account: Account) -> ConnectionResult:
        started.set()
        if not release.wait(timeout=3):
            raise RuntimeError("Verification timed out.")
        return ConnectionResult(
            status=ConnectionStatus.CONNECTED,
            message="Instagram account connection verified.",
        )

    verifier.verify.side_effect = verify

    page, _ = create_page(verifier)
    qtbot.addWidget(page)
    page.account_list.setCurrentRow(0)
    page.verify_button.click()

    try:
        assert started.wait(timeout=2)

        controller = page._instagram_verification_controller
        assert controller is not None
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