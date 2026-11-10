from unittest.mock import Mock

import pytest

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
from socialflow.modules.accounts.workers.instagram_verification_worker import (
    InstagramVerificationWorker,
)


def create_instagram_account() -> Account:
    return Account(
        name="Test Instagram Account",
        destination=PublishingDestination.INSTAGRAM,
    )


@pytest.mark.parametrize(
    "status",
    [
        ConnectionStatus.CONNECTED,
        ConnectionStatus.INVALID_CREDENTIALS,
        ConnectionStatus.UNREACHABLE,
        ConnectionStatus.ERROR,
    ],
)
def test_worker_emits_verification_result(qtbot, status) -> None:
    account = create_instagram_account()
    verifier = Mock(spec=ConnectionVerifier)

    result = ConnectionResult(
        status=status,
        message="Instagram verification result.",
    )
    verifier.verify.return_value = result

    worker = InstagramVerificationWorker(verifier, account)

    with (
        qtbot.waitSignal(worker.finished, timeout=1000) as signal,
        qtbot.assertNotEmitted(worker.failed),
    ):
        worker.run()

    verifier.verify.assert_called_once_with(account)
    assert signal.args == [result]


def test_worker_handles_credential_storage_failure(qtbot) -> None:
    account = create_instagram_account()
    verifier = Mock(spec=ConnectionVerifier)
    verifier.verify.side_effect = CredentialStorageError(
        "SECRET_CREDENTIAL_DETAILS"
    )

    worker = InstagramVerificationWorker(verifier, account)

    with (
        qtbot.waitSignal(worker.failed, timeout=1000) as failure,
        qtbot.assertNotEmitted(worker.finished),
    ):
        worker.run()

    assert failure.args == [
        "Could not access stored Instagram credentials."
    ]
    assert "SECRET_CREDENTIAL_DETAILS" not in failure.args[0]


@pytest.mark.parametrize(
    "exception_type",
    [
        RuntimeError,
        ValueError,
        TypeError,
        OSError,
    ],
)
def test_worker_handles_unexpected_failures(
    qtbot,
    exception_type,
) -> None:
    account = create_instagram_account()
    verifier = Mock(spec=ConnectionVerifier)
    verifier.verify.side_effect = exception_type(
        "SECRET_INTERNAL_DETAILS"
    )

    worker = InstagramVerificationWorker(verifier, account)

    with (
        qtbot.waitSignal(worker.failed, timeout=1000) as failure,
        qtbot.assertNotEmitted(worker.finished),
    ):
        worker.run()

    assert failure.args == [
        "Instagram connection verification failed unexpectedly."
    ]
    assert "SECRET_INTERNAL_DETAILS" not in failure.args[0]