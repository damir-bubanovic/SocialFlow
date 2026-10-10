from threading import Event
from unittest.mock import Mock

from socialflow.application.connections.connection_verifier import (
    ConnectionVerifier,
)
from socialflow.application.credentials.errors import (
    CredentialStorageError,
)
from socialflow.domain.account.account import Account
from socialflow.domain.connections.connection_result import (
    ConnectionResult,
)
from socialflow.domain.connections.connection_status import (
    ConnectionStatus,
)
from socialflow.domain.publishing.destination import (
    PublishingDestination,
)
from socialflow.ui.accounts.wordpress_verification_controller import (
    WordPressVerificationController,
)


def create_wordpress_account() -> Account:
    """Create a WordPress account for controller tests."""
    return Account(
        name="Test WordPress",
        destination=PublishingDestination.WORDPRESS,
    )


def test_controller_emits_verification_result(qtbot) -> None:
    """A successful verification delivers its result and stops."""
    account = create_wordpress_account()
    verifier = Mock(spec=ConnectionVerifier)

    result = ConnectionResult(
        status=ConnectionStatus.CONNECTED,
        message="WordPress connection verified.",
    )
    verifier.verify.return_value = result

    controller = WordPressVerificationController(verifier)
    result_listener = Mock()
    controller.result_ready.connect(result_listener)

    with qtbot.waitSignals(
        [controller.result_ready, controller.finished],
        timeout=3000,
        order="strict",
    ):
        controller.start(account)

    verifier.verify.assert_called_once_with(account)
    result_listener.assert_called_once_with(result)
    assert not controller.is_running


def test_controller_emits_credential_storage_error(qtbot) -> None:
    """Credential storage failures are reported and cleaned up."""
    account = create_wordpress_account()
    verifier = Mock(spec=ConnectionVerifier)

    verifier.verify.side_effect = CredentialStorageError(
        "Sensitive credential storage details."
    )

    controller = WordPressVerificationController(verifier)
    error_listener = Mock()
    controller.error_occurred.connect(error_listener)

    with qtbot.waitSignals(
        [controller.error_occurred, controller.finished],
        timeout=3000,
        order="strict",
    ):
        controller.start(account)

    verifier.verify.assert_called_once_with(account)
    error_listener.assert_called_once_with(
        "Could not access stored WordPress credentials."
    )
    assert not controller.is_running


def test_controller_prevents_concurrent_verification(qtbot) -> None:
    """A second verification cannot start while one is running."""
    account = create_wordpress_account()
    verifier = Mock(spec=ConnectionVerifier)

    started = Event()
    release = Event()

    result = ConnectionResult(
        status=ConnectionStatus.CONNECTED,
        message="WordPress connection verified.",
    )

    def verify(_account):
        started.set()
        if not release.wait(timeout=2):
            raise TimeoutError("Test worker was not released.")
        return result

    verifier.verify.side_effect = verify

    controller = WordPressVerificationController(verifier)

    try:
        controller.start(account)

        assert started.wait(timeout=2)
        assert controller.is_running

        controller.start(account)
        assert verifier.verify.call_count == 1
    finally:
        release.set()
        with qtbot.waitSignal(controller.finished, timeout=3000):
            controller.shutdown()

    assert not controller.is_running

def test_controller_shutdown_waits_for_active_verification(qtbot) -> None:
    """Shutdown must not destroy a running verification thread."""
    from threading import Event, Thread

    account = create_wordpress_account()
    verifier = Mock(spec=ConnectionVerifier)

    started = Event()
    release = Event()

    result = ConnectionResult(
        status=ConnectionStatus.CONNECTED,
        message="WordPress connection verified.",
    )

    def verify(_account):
        started.set()
        if not release.wait(timeout=3):
            raise TimeoutError("Test worker was not released.")
        return result

    verifier.verify.side_effect = verify

    controller = WordPressVerificationController(verifier)
    controller.start(account)

    assert started.wait(timeout=2)
    assert controller.is_running

    releaser = Thread(target=lambda: release.set())
    releaser.start()

    try:
        controller.shutdown()
    finally:
        release.set()
        releaser.join(timeout=2)

    qtbot.waitUntil(lambda: not controller.is_running, timeout=3000)

    verifier.verify.assert_called_once_with(account)