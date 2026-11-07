
from unittest.mock import Mock

from socialflow.core.destination import PublishingDestination
from socialflow.modules.accounts.models.account import Account
from socialflow.modules.accounts.models.connection_result import (
    ConnectionResult,
)
from socialflow.modules.accounts.models.connection_status import (
    ConnectionStatus,
)
from socialflow.modules.accounts.services.connection_verifier import (
    ConnectionVerifier,
)
from socialflow.modules.accounts.services.credential_errors import (
    CredentialStorageError,
)
from socialflow.modules.accounts.workers.facebook_verification_worker import (
    FacebookVerificationWorker,
)


def create_facebook_account() -> Account:
    return Account(
        name="Test Facebook Page",
        destination=PublishingDestination.FACEBOOK,
    )


def test_worker_emits_successful_verification_result(qtbot) -> None:
    account = create_facebook_account()
    verifier = Mock(spec=ConnectionVerifier)

    result = ConnectionResult(
        status=ConnectionStatus.CONNECTED,
        message="Facebook Page connection verified.",
    )
    verifier.verify.return_value = result

    worker = FacebookVerificationWorker(verifier, account)

    with qtbot.waitSignal(worker.finished, timeout=1000) as signal:
        worker.run()

    verifier.verify.assert_called_once_with(account)
    assert signal.args == [result]


def test_worker_emits_invalid_credentials_result(qtbot) -> None:
    account = create_facebook_account()
    verifier = Mock(spec=ConnectionVerifier)

    result = ConnectionResult(
        status=ConnectionStatus.INVALID_CREDENTIALS,
        message="Facebook Page access token is invalid.",
    )
    verifier.verify.return_value = result

    worker = FacebookVerificationWorker(verifier, account)

    with qtbot.waitSignal(worker.finished, timeout=1000) as signal:
        worker.run()

    verifier.verify.assert_called_once_with(account)
    assert signal.args == [result]


def test_worker_handles_credential_storage_failure(qtbot) -> None:
    account = create_facebook_account()
    verifier = Mock(spec=ConnectionVerifier)
    verifier.verify.side_effect = CredentialStorageError(
        "Sensitive credential storage details."
    )

    worker = FacebookVerificationWorker(verifier, account)

    with (
        qtbot.waitSignal(worker.failed, timeout=1000) as failure,
        qtbot.assertNotEmitted(worker.finished),
    ):
        worker.run()

    assert failure.args == [
        "Could not access stored Facebook credentials."
    ]


def test_worker_handles_unexpected_runtime_failure(qtbot) -> None:
    account = create_facebook_account()
    verifier = Mock(spec=ConnectionVerifier)
    verifier.verify.side_effect = RuntimeError(
        "Sensitive internal verification details."
    )

    worker = FacebookVerificationWorker(verifier, account)

    with (
        qtbot.waitSignal(worker.failed, timeout=1000) as failure,
        qtbot.assertNotEmitted(worker.finished),
    ):
        worker.run()

    assert failure.args == [
        "Facebook connection verification failed unexpectedly."
    ]


def test_worker_handles_unexpected_value_error(qtbot) -> None:
    account = create_facebook_account()
    verifier = Mock(spec=ConnectionVerifier)
    verifier.verify.side_effect = ValueError(
        "Sensitive invalid response details."
    )

    worker = FacebookVerificationWorker(verifier, account)

    with (
        qtbot.waitSignal(worker.failed, timeout=1000) as failure,
        qtbot.assertNotEmitted(worker.finished),
    ):
        worker.run()

    assert failure.args == [
        "Facebook connection verification failed unexpectedly."
    ]
