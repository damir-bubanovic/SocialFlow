from threading import Event, Thread
from unittest.mock import Mock

from socialflow.core.destination import PublishingDestination
from socialflow.modules.accounts.controllers.instagram_verification_controller import (
    InstagramVerificationController,
)
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


def create_instagram_account() -> Account:
    return Account(
        name="Test Instagram",
        destination=PublishingDestination.INSTAGRAM,
    )


def connected_result() -> ConnectionResult:
    return ConnectionResult(
        status=ConnectionStatus.CONNECTED,
        message="Instagram connection verified.",
    )


def test_controller_emits_verification_result(qtbot) -> None:
    account = create_instagram_account()
    verifier = Mock(spec=ConnectionVerifier)
    result = connected_result()
    verifier.verify.return_value = result

    controller = InstagramVerificationController(verifier)
    result_listener = Mock()
    controller.result_ready.connect(result_listener)

    try:
        with qtbot.waitSignals(
            [controller.result_ready, controller.finished],
            timeout=3000,
            order="strict",
        ):
            controller.start(account)

        verifier.verify.assert_called_once_with(account)
        result_listener.assert_called_once_with(result)
        assert not controller.is_running
        assert controller._worker is None
        assert controller._thread is None
    finally:
        controller.shutdown()


def test_controller_emits_credential_storage_error(qtbot) -> None:
    account = create_instagram_account()
    verifier = Mock(spec=ConnectionVerifier)
    verifier.verify.side_effect = CredentialStorageError(
        "SECRET_STORAGE_DETAILS"
    )

    controller = InstagramVerificationController(verifier)
    error_listener = Mock()
    controller.error_occurred.connect(error_listener)

    try:
        with qtbot.waitSignals(
            [controller.error_occurred, controller.finished],
            timeout=3000,
            order="strict",
        ):
            controller.start(account)

        verifier.verify.assert_called_once_with(account)
        error_listener.assert_called_once_with(
            "Could not access stored Instagram credentials."
        )
        assert not controller.is_running
    finally:
        controller.shutdown()


def test_controller_prevents_concurrent_verification(qtbot) -> None:
    account = create_instagram_account()
    verifier = Mock(spec=ConnectionVerifier)

    started = Event()
    release = Event()
    result = connected_result()

    def verify(_account):
        started.set()
        if not release.wait(timeout=3):
            raise TimeoutError("Test worker was not released.")
        return result

    verifier.verify.side_effect = verify

    controller = InstagramVerificationController(verifier)
    result_listener = Mock()
    finished_listener = Mock()

    controller.result_ready.connect(result_listener)
    controller.finished.connect(finished_listener)

    try:
        controller.start(account)

        assert started.wait(timeout=2)
        assert controller.is_running

        controller.start(account)
        assert verifier.verify.call_count == 1

        with qtbot.waitSignals(
            [controller.result_ready, controller.finished],
            timeout=3000,
            order="strict",
        ):
            release.set()

        result_listener.assert_called_once_with(result)
        finished_listener.assert_called_once_with()
        assert not controller.is_running
    finally:
        release.set()
        controller.shutdown()


def test_controller_shutdown_waits_for_active_verification(qtbot) -> None:
    account = create_instagram_account()
    verifier = Mock(spec=ConnectionVerifier)

    started = Event()
    release = Event()
    result = connected_result()

    def verify(_account):
        started.set()
        if not release.wait(timeout=3):
            raise TimeoutError("Test worker was not released.")
        return result

    verifier.verify.side_effect = verify

    controller = InstagramVerificationController(verifier)
    controller.start(account)

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

    verifier.verify.assert_called_once_with(account)
    assert controller._thread is None
    assert controller._worker is None


def test_controller_can_restart_after_failure(qtbot) -> None:
    account = create_instagram_account()
    verifier = Mock(spec=ConnectionVerifier)
    result = connected_result()

    verifier.verify.side_effect = [
        RuntimeError("SECRET_INTERNAL_DETAILS"),
        result,
    ]

    controller = InstagramVerificationController(verifier)
    error_listener = Mock()
    result_listener = Mock()

    controller.error_occurred.connect(error_listener)
    controller.result_ready.connect(result_listener)

    try:
        with qtbot.waitSignals(
            [controller.error_occurred, controller.finished],
            timeout=3000,
            order="strict",
        ):
            controller.start(account)

        assert not controller.is_running
        error_listener.assert_called_once_with(
            "Instagram connection verification failed unexpectedly."
        )

        with qtbot.waitSignals(
            [controller.result_ready, controller.finished],
            timeout=3000,
            order="strict",
        ):
            controller.start(account)

        result_listener.assert_called_once_with(result)
        assert verifier.verify.call_count == 2
        assert not controller.is_running
    finally:
        controller.shutdown()


def test_controller_can_restart_after_credential_failure(qtbot) -> None:
    account = create_instagram_account()
    verifier = Mock(spec=ConnectionVerifier)
    result = connected_result()

    verifier.verify.side_effect = [
        CredentialStorageError("SECRET_STORAGE_DETAILS"),
        result,
    ]

    controller = InstagramVerificationController(verifier)
    error_listener = Mock()
    result_listener = Mock()

    controller.error_occurred.connect(error_listener)
    controller.result_ready.connect(result_listener)

    try:
        with qtbot.waitSignals(
            [controller.error_occurred, controller.finished],
            timeout=3000,
            order="strict",
        ):
            controller.start(account)

        assert not controller.is_running

        with qtbot.waitSignals(
            [controller.result_ready, controller.finished],
            timeout=3000,
            order="strict",
        ):
            controller.start(account)

        error_listener.assert_called_once_with(
            "Could not access stored Instagram credentials."
        )
        result_listener.assert_called_once_with(result)
        assert verifier.verify.call_count == 2
        assert not controller.is_running
    finally:
        controller.shutdown()


def test_controller_can_verify_repeatedly(qtbot) -> None:
    account = create_instagram_account()
    verifier = Mock(spec=ConnectionVerifier)
    result = connected_result()
    verifier.verify.return_value = result

    controller = InstagramVerificationController(verifier)
    result_listener = Mock()
    finished_listener = Mock()

    controller.result_ready.connect(result_listener)
    controller.finished.connect(finished_listener)

    try:
        for attempt in range(1, 4):
            with qtbot.waitSignals(
                [controller.result_ready, controller.finished],
                timeout=3000,
                order="strict",
            ):
                controller.start(account)

            assert not controller.is_running
            assert controller._worker is None
            assert controller._thread is None
            assert verifier.verify.call_count == attempt
            assert result_listener.call_count == attempt
            assert finished_listener.call_count == attempt
    finally:
        controller.shutdown()


def test_controller_repeated_shutdown_is_safe(qtbot) -> None:
    account = create_instagram_account()
    verifier = Mock(spec=ConnectionVerifier)
    verifier.verify.return_value = connected_result()

    controller = InstagramVerificationController(verifier)

    with qtbot.waitSignals(
        [controller.result_ready, controller.finished],
        timeout=3000,
        order="strict",
    ):
        controller.start(account)

    controller.shutdown()
    controller.shutdown()

    assert not controller.is_running
    assert controller._thread is None
    assert controller._worker is None