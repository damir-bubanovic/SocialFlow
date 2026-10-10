from PySide6.QtWidgets import QMainWindow
from unittest.mock import patch
from socialflow.ui.main_content import MainContent

from socialflow.ui.main_window import MainWindow


def test_main_window_is_qt_main_window(qtbot) -> None:
    window = MainWindow()

    qtbot.addWidget(window)

    assert isinstance(window, QMainWindow)


def test_main_window_has_socialflow_title(qtbot) -> None:
    window = MainWindow()

    qtbot.addWidget(window)

    assert window.windowTitle() == "SocialFlow"

def test_main_window_has_initial_size(qtbot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)

    assert window.width() == 1200
    assert window.height() == 800

def test_main_window_has_central_widget(qtbot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)

    assert isinstance(window.centralWidget(), MainContent)

def test_main_window_shuts_down_accounts_page_on_close(qtbot) -> None:
    """Closing the main window shuts down WordPress verification."""
    window = MainWindow()
    qtbot.addWidget(window)

    with patch.object(
        window.main_content.accounts_page,
        "shutdown",
    ) as shutdown:
        window.close()

    shutdown.assert_called_once_with()

def test_main_window_defers_close_until_verification_finishes(
    qtbot,
) -> None:
    """The main window closes only after verification finishes."""
    from unittest.mock import PropertyMock, patch

    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    accounts_page = window.main_content.accounts_page

    with patch.object(
        type(accounts_page),
        "verification_is_running",
        new_callable=PropertyMock,
    ) as is_running:
        is_running.return_value = True

        window.close()

        assert window.isVisible()
        assert window._close_pending

        is_running.return_value = False

        accounts_page.verification_finished.emit()

        qtbot.waitUntil(
            lambda: not window.isVisible(),
            timeout=3000,
        )

    assert not window._close_pending

def test_main_window_closes_after_active_verification_finishes(
    qtbot,
) -> None:
    """Closing remains responsive until the real worker finishes."""
    from threading import Event
    from unittest.mock import Mock

    from socialflow.application.connections.connection_verifier import (
        ConnectionVerifier,
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

    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    accounts_page = window.main_content.accounts_page

    started = Event()
    release = Event()

    verifier = Mock(spec=ConnectionVerifier)

    def verify(_account):
        started.set()

        if not release.wait(timeout=5):
            raise TimeoutError("Test verification was not released.")

        return ConnectionResult(
            status=ConnectionStatus.CONNECTED,
            message="WordPress connection verified.",
        )

    verifier.verify.side_effect = verify

    # Replace the idle controller with one using our controlled verifier.
    controller = WordPressVerificationController(
        verifier,
        parent=accounts_page,
    )
    accounts_page._verification_controller = controller

    controller.finished.connect(
        accounts_page.verification_finished.emit
    )

    account = Account(
        name="Test WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    try:
        controller.start(account)

        assert started.wait(timeout=2)
        assert accounts_page.verification_is_running

        window.close()

        assert window.isVisible()
        assert window._close_pending

        release.set()

        qtbot.waitUntil(
            lambda: not window.isVisible(),
            timeout=5000,
        )

        assert not accounts_page.verification_is_running
        verifier.verify.assert_called_once_with(account)

    finally:
        release.set()
        controller.shutdown()