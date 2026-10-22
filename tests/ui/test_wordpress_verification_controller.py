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
    """An overlapping request is ignored without disrupting the first."""
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
    result_listener = Mock()
    error_listener = Mock()
    finished_listener = Mock()

    controller.result_ready.connect(result_listener)
    controller.error_occurred.connect(error_listener)
    controller.finished.connect(finished_listener)

    try:
        controller.start(account)

        assert started.wait(timeout=2)
        assert controller.is_running

        # The overlapping request must not launch another worker.
        controller.start(account)
        assert verifier.verify.call_count == 1

        with qtbot.waitSignals(
            [controller.result_ready, controller.finished],
            timeout=3000,
            order="strict",
        ):
            release.set()

        result_listener.assert_called_once_with(result)
        error_listener.assert_not_called()
        finished_listener.assert_called_once_with()

        verifier.verify.assert_called_once_with(account)
        assert not controller.is_running
        assert controller._worker is None
        assert controller._thread is None

    finally:
        release.set()
        controller.shutdown()


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


def test_controller_can_restart_after_verification_failure(
    qtbot,
) -> None:
    """A failed verification can be followed by a successful retry."""
    account = create_wordpress_account()
    verifier = Mock(spec=ConnectionVerifier)

    result = ConnectionResult(
        status=ConnectionStatus.CONNECTED,
        message="WordPress connection verified.",
    )

    verifier.verify.side_effect = [
        RuntimeError("Simulated verification failure."),
        result,
    ]

    controller = WordPressVerificationController(verifier)

    result_listener = Mock()
    error_listener = Mock()
    finished_listener = Mock()

    controller.result_ready.connect(result_listener)
    controller.error_occurred.connect(error_listener)
    controller.finished.connect(finished_listener)

    # First attempt fails.
    with qtbot.waitSignals(
        [controller.error_occurred, controller.finished],
        timeout=3000,
        order="strict",
    ):
        controller.start(account)

    assert not controller.is_running
    assert controller._thread is None
    assert controller._worker is None

    error_listener.assert_called_once_with(
        "WordPress connection verification failed unexpectedly."
    )
    result_listener.assert_not_called()
    assert finished_listener.call_count == 1

    # Retry using the same controller.
    with qtbot.waitSignals(
        [controller.result_ready, controller.finished],
        timeout=3000,
        order="strict",
    ):
        controller.start(account)

    assert not controller.is_running
    assert controller._thread is None
    assert controller._worker is None

    result_listener.assert_called_once_with(result)
    error_listener.assert_called_once()
    assert finished_listener.call_count == 2

    assert verifier.verify.call_count == 2
    assert verifier.verify.call_args_list == [
        ((account,), {}),
        ((account,), {}),
    ]


def test_controller_can_restart_after_credential_storage_error(
    qtbot,
) -> None:
    """Verification can be retried after a credential storage error."""
    account = create_wordpress_account()
    verifier = Mock(spec=ConnectionVerifier)

    result = ConnectionResult(
        status=ConnectionStatus.CONNECTED,
        message="WordPress connection verified.",
    )

    verifier.verify.side_effect = [
        CredentialStorageError("Sensitive credential details."),
        result,
    ]

    controller = WordPressVerificationController(verifier)

    error_listener = Mock()
    result_listener = Mock()
    finished_listener = Mock()

    controller.error_occurred.connect(error_listener)
    controller.result_ready.connect(result_listener)
    controller.finished.connect(finished_listener)

    try:
        with qtbot.waitSignals(
            [controller.error_occurred, controller.finished],
            timeout=3000,
            order="strict",
        ):
            controller.start(account)

        error_listener.assert_called_once_with(
            "Could not access stored WordPress credentials."
        )
        result_listener.assert_not_called()

        assert not controller.is_running
        assert controller._thread is None
        assert controller._worker is None

        with qtbot.waitSignals(
            [controller.result_ready, controller.finished],
            timeout=3000,
            order="strict",
        ):
            controller.start(account)

        result_listener.assert_called_once_with(result)
        error_listener.assert_called_once()
        assert finished_listener.call_count == 2

        assert not controller.is_running
        assert controller._thread is None
        assert controller._worker is None

        assert verifier.verify.call_count == 2
        assert verifier.verify.call_args_list[0].args == (account,)
        assert verifier.verify.call_args_list[1].args == (account,)

    finally:
        controller.shutdown()


def test_controller_repeated_shutdown_after_active_verification(
    qtbot,
) -> None:
    """Repeated shutdown is safe after an active worker completes."""
    from threading import Thread

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
    result_listener = Mock()
    finished_listener = Mock()

    controller.result_ready.connect(result_listener)
    controller.finished.connect(finished_listener)

    controller.start(account)

    try:
        assert started.wait(timeout=2)
        assert controller.is_running

        # Release the worker from another thread while shutdown waits.
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

        result_listener.assert_called_once_with(result)
        finished_listener.assert_called_once_with()

        # Additional shutdown calls must be harmless.
        controller.shutdown()
        controller.shutdown()

        assert not controller.is_running
        assert controller._thread is None
        assert controller._worker is None

        verifier.verify.assert_called_once_with(account)
        finished_listener.assert_called_once_with()

    finally:
        release.set()
        controller.shutdown()
