
from unittest.mock import Mock

from socialflow.modules.accounts.services.connection_verifier import (
    ConnectionVerifier,
)
from socialflow.modules.accounts.services.credential_errors import (
    CredentialStorageError,
)
from socialflow.modules.accounts.models.account import Account
from socialflow.modules.accounts.models.connection_result import (
    ConnectionResult,
)
from socialflow.modules.accounts.models.connection_status import (
    ConnectionStatus,
)
from socialflow.modules.posts.models.destination import (
    PublishingDestination,
)
from socialflow.modules.accounts.workers.wordpress_verification_worker import (
    WordPressVerificationWorker,
)


def create_wordpress_account() -> Account:
    """Create a WordPress account for worker tests."""
    return Account(
        name="Test WordPress",
        destination=PublishingDestination.WORDPRESS,
    )


def test_worker_emits_successful_verification_result(qtbot) -> None:
    """Successful verification emits the expected result."""
    account = create_wordpress_account()
    verifier = Mock(spec=ConnectionVerifier)

    result = ConnectionResult(
        status=ConnectionStatus.CONNECTED,
        message="WordPress connection verified.",
    )
    verifier.verify.return_value = result

    worker = WordPressVerificationWorker(verifier, account)

    with qtbot.waitSignal(worker.finished, timeout=1000) as signal:
        worker.run()

    verifier.verify.assert_called_once_with(account)
    assert signal.args == [result]


def test_worker_emits_failed_connection_result(qtbot) -> None:
    """Authentication failures are returned as connection results."""
    account = create_wordpress_account()
    verifier = Mock(spec=ConnectionVerifier)

    result = ConnectionResult(
        status=ConnectionStatus.INVALID_CREDENTIALS,
        message="Invalid WordPress credentials.",
    )
    verifier.verify.return_value = result

    worker = WordPressVerificationWorker(verifier, account)

    with qtbot.waitSignal(worker.finished, timeout=1000) as signal:
        worker.run()

    verifier.verify.assert_called_once_with(account)
    assert signal.args == [result]


def test_worker_emits_error_on_credential_storage_failure(qtbot) -> None:
    """Credential storage failures emit a safe error message."""
    account = create_wordpress_account()
    verifier = Mock(spec=ConnectionVerifier)

    verifier.verify.side_effect = CredentialStorageError(
        "Sensitive credential storage details."
    )

    worker = WordPressVerificationWorker(verifier, account)

    with qtbot.waitSignal(worker.failed, timeout=1000) as signal:
        worker.run()

    verifier.verify.assert_called_once_with(account)
    assert signal.args == [
        "Could not access stored WordPress credentials."
    ]


def test_worker_emits_failure_for_unexpected_exception(
    qtbot,
) -> None:
    """Unexpected verification errors emit failure, not Qt exceptions."""
    from unittest.mock import Mock

    from socialflow.modules.accounts.services.connection_verifier import (
        ConnectionVerifier,
    )
    from socialflow.modules.accounts.models.account import Account
    from socialflow.modules.posts.models.destination import (
        PublishingDestination,
    )
    from socialflow.modules.accounts.workers.wordpress_verification_worker import (
        WordPressVerificationWorker,
    )

    verifier = Mock(spec=ConnectionVerifier)
    verifier.verify.side_effect = RuntimeError(
        "Sensitive internal verification details"
    )

    account = Account(
        name="Test WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    worker = WordPressVerificationWorker(verifier, account)

    with (
        qtbot.waitSignal(worker.failed, timeout=1000) as failure,
        qtbot.assertNotEmitted(worker.finished),
    ):
        worker.run()

    assert failure.args == [
        "WordPress connection verification failed unexpectedly."
    ]

    verifier.verify.assert_called_once_with(account)
