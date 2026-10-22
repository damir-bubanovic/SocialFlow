from unittest.mock import PropertyMock, patch

import pytest
from PySide6.QtWidgets import QMainWindow

from socialflow.ui.main_content import MainContent
from socialflow.ui.main_window import MainWindow




@pytest.fixture
def real_background_workers(qtbot):
    """Create controlled verification and publishing Qt workers."""
    from threading import Event
    from unittest.mock import Mock

    from socialflow.application.connections.connection_verifier import (
        ConnectionVerifier,
    )
    from socialflow.application.publishing.publish_post import PublishPost
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
    from socialflow.domain.publishing.publish_request import PublishRequest
    from socialflow.ui.accounts.wordpress_verification_controller import (
        WordPressVerificationController,
    )
    from socialflow.ui.posts.publishing_controller import (
        PublishingController,
    )

    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    accounts_page = window.main_content.accounts_page
    posts_page = window.main_content.posts_page

    verification_started = Event()
    publishing_started = Event()
    release_verification = Event()
    release_publishing = Event()

    verifier = Mock(spec=ConnectionVerifier)
    publisher = Mock(spec=PublishPost)

    def verify(_account):
        verification_started.set()

        if not release_verification.wait(timeout=5):
            raise TimeoutError("Verification worker timed out.")

        return ConnectionResult(
            status=ConnectionStatus.CONNECTED,
            message="Verified.",
        )

    def publish(_request, *, on_progress=None):
        assert on_progress is None or callable(on_progress)
        publishing_started.set()

        if not release_publishing.wait(timeout=5):
            raise TimeoutError("Publishing worker timed out.")

        return ()

    verifier.verify.side_effect = verify
    publisher.execute.side_effect = publish

    verification_controller = WordPressVerificationController(
        verifier,
        parent=accounts_page,
    )
    publishing_controller = PublishingController(
        publisher,
        parent=posts_page,
    )

    accounts_page._verification_controller = verification_controller
    posts_page._publishing_controller = publishing_controller

    verification_controller.finished.connect(
        accounts_page.verification_finished.emit
    )
    publishing_controller.finished.connect(
        posts_page.publishing_finished.emit
    )

    account = Account(
        name="Test WordPress",
        destination=PublishingDestination.WORDPRESS,
    )
    request = PublishRequest(
        post=Mock(),
        accounts=(),
    )

    context = {
        "window": window,
        "accounts_page": accounts_page,
        "posts_page": posts_page,
        "verification_controller": verification_controller,
        "publishing_controller": publishing_controller,
        "verification_started": verification_started,
        "publishing_started": publishing_started,
        "release_verification": release_verification,
        "release_publishing": release_publishing,
        "verifier": verifier,
        "publisher": publisher,
        "account": account,
        "request": request,
    }

    try:
        yield context
    finally:
        release_verification.set()
        release_publishing.set()
        verification_controller.shutdown()
        publishing_controller.shutdown()


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

def test_main_window_closes_without_initialized_content(
    qtbot,
) -> None:
    """Allow a partially initialized window to close safely."""
    window = MainWindow.__new__(MainWindow)
    QMainWindow.__init__(window)

    qtbot.addWidget(window)

    assert not hasattr(window, "main_content")
    assert window.close()

def test_main_window_defers_close_until_verification_finishes(
    qtbot,
) -> None:
    """The main window closes only after verification finishes."""

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


def test_main_window_defers_close_until_publishing_finishes(
    qtbot,
) -> None:
    """Keep the window open until publishing finishes."""

    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    posts_page = window.main_content.posts_page

    with patch.object(
        type(posts_page),
        "publishing_is_running",
        new_callable=PropertyMock,
    ) as is_running:
        is_running.return_value = True

        window.close()

        assert window.isVisible()
        assert window._close_pending

        is_running.return_value = False

        posts_page.publishing_finished.emit()

        qtbot.waitUntil(
            lambda: not window.isVisible(),
            timeout=3000,
        )

    assert not window._close_pending


def test_main_window_closes_after_active_publishing_finishes(
    qtbot,
) -> None:
    """Keep the window open until a real publishing worker finishes."""
    from threading import Event
    from unittest.mock import Mock

    from socialflow.application.publishing.publish_post import PublishPost
    from socialflow.domain.publishing.publish_request import PublishRequest
    from socialflow.ui.posts.publishing_controller import PublishingController

    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    posts_page = window.main_content.posts_page

    started = Event()
    release = Event()

    publish_post = Mock(spec=PublishPost)

    def execute(_request, *, on_progress=None):
        assert callable(on_progress)
        started.set()

        if not release.wait(timeout=5):
            return ()

        return ()

    publish_post.execute.side_effect = execute

    controller = PublishingController(
        publish_post,
        parent=posts_page,
    )
    posts_page._publishing_controller = controller

    controller.finished.connect(
        posts_page.publishing_finished.emit
    )

    request = PublishRequest(
        post=Mock(),
        accounts=(),
    )

    try:
        controller.start(request)

        assert started.wait(timeout=2)
        assert posts_page.publishing_is_running

        window.close()

        assert window.isVisible()
        assert window._close_pending

        release.set()

        qtbot.waitUntil(
            lambda: not window.isVisible(),
            timeout=5000,
        )

        assert not posts_page.publishing_is_running
        publish_post.execute.assert_called_once()
        args, kwargs = publish_post.execute.call_args

        assert args == (request,)
        assert callable(kwargs["on_progress"])

    finally:
        release.set()
        controller.shutdown()

def test_main_window_closes_with_partially_initialized_content(
    qtbot,
    monkeypatch,
) -> None:
    """Closing tolerates content whose child pages are incomplete."""

    window = MainWindow()
    qtbot.addWidget(window)

    class PartialContent:
        pass

    monkeypatch.setattr(
        window,
        "main_content",
        PartialContent(),
    )

    assert window.close()


def test_main_window_closes_after_active_publishing_failure(
    qtbot,
) -> None:
    """Close the window after an active publishing worker fails."""
    from threading import Event
    from unittest.mock import Mock

    from socialflow.application.publishing.publish_post import PublishPost
    from socialflow.domain.publishing.publish_request import PublishRequest
    from socialflow.ui.posts.publishing_controller import PublishingController

    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    posts_page = window.main_content.posts_page

    started = Event()
    release = Event()

    publish_post = Mock(spec=PublishPost)

    def execute(_request, *, on_progress=None):
        assert callable(on_progress)
        started.set()

        if not release.wait(timeout=5):
            raise TimeoutError("Publishing was not released.")

        raise RuntimeError("Unexpected publishing failure")

    publish_post.execute.side_effect = execute

    controller = PublishingController(
        publish_post,
        parent=posts_page,
    )
    posts_page._publishing_controller = controller

    controller.finished.connect(
        posts_page.publishing_finished.emit
    )

    request = PublishRequest(
        post=Mock(),
        accounts=(),
    )

    try:
        controller.start(request)

        qtbot.waitUntil(
            started.is_set,
            timeout=3000,
        )

        assert posts_page.publishing_is_running

        window.close()

        assert window.isVisible()
        assert window._close_pending

        release.set()

        qtbot.waitUntil(
            lambda: not window.isVisible(),
            timeout=5000,
        )

        assert not posts_page.publishing_is_running
        assert not window._close_pending

        publish_post.execute.assert_called_once()

    finally:
        release.set()
        controller.shutdown()

def test_main_window_repeated_close_during_publishing(qtbot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    accounts_page = window.main_content.accounts_page
    posts_page = window.main_content.posts_page

    with (
        patch.object(
            type(posts_page),
            "publishing_is_running",
            new_callable=PropertyMock,
        ) as publishing_running,
        patch.object(posts_page, "shutdown") as posts_shutdown,
        patch.object(accounts_page, "shutdown") as accounts_shutdown,
    ):
        publishing_running.return_value = True

        window.close()
        window.close()

        assert window.isVisible()
        assert window._close_pending

        posts_shutdown.assert_not_called()
        accounts_shutdown.assert_not_called()

        publishing_running.return_value = False

        window._finish_pending_close()

        assert not window.isVisible()
        assert not window._close_pending

        posts_shutdown.assert_called_once()
        accounts_shutdown.assert_called_once()


def test_main_window_waits_for_both_background_operations(
    qtbot,
) -> None:
    """Close only after verification and publishing both finish."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    accounts_page = window.main_content.accounts_page
    posts_page = window.main_content.posts_page

    with (
        patch.object(
            type(accounts_page),
            "verification_is_running",
            new_callable=PropertyMock,
        ) as verification_running,
        patch.object(
            type(posts_page),
            "publishing_is_running",
            new_callable=PropertyMock,
        ) as publishing_running,
        patch.object(
            accounts_page,
            "shutdown",
        ) as accounts_shutdown,
        patch.object(
            posts_page,
            "shutdown",
        ) as posts_shutdown,
    ):
        verification_running.return_value = True
        publishing_running.return_value = True

        window.close()

        assert window.isVisible()
        assert window._close_pending

        verification_running.return_value = False
        accounts_page.verification_finished.emit()

        assert window.isVisible()
        assert window._close_pending

        accounts_shutdown.assert_not_called()
        posts_shutdown.assert_not_called()

        publishing_running.return_value = False
        posts_page.publishing_finished.emit()

        qtbot.waitUntil(
            lambda: not window.isVisible(),
            timeout=3000,
        )

        assert not window._close_pending

        accounts_shutdown.assert_called_once_with()
        posts_shutdown.assert_called_once_with()


def test_main_window_repeated_close_with_both_operations(
    qtbot,
) -> None:
    """Repeated close requests wait for both workers."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    accounts_page = window.main_content.accounts_page
    posts_page = window.main_content.posts_page

    with (
        patch.object(
            type(accounts_page),
            "verification_is_running",
            new_callable=PropertyMock,
        ) as verification_running,
        patch.object(
            type(posts_page),
            "publishing_is_running",
            new_callable=PropertyMock,
        ) as publishing_running,
        patch.object(
            accounts_page,
            "shutdown",
        ) as accounts_shutdown,
        patch.object(
            posts_page,
            "shutdown",
        ) as posts_shutdown,
    ):
        verification_running.return_value = True
        publishing_running.return_value = True

        # Multiple close requests while both are active.
        for _ in range(3):
            window.close()

        assert window.isVisible()
        assert window._close_pending

        accounts_shutdown.assert_not_called()
        posts_shutdown.assert_not_called()

        # Verification finishes first.
        verification_running.return_value = False
        accounts_page.verification_finished.emit()

        window.close()

        assert window.isVisible()
        assert window._close_pending

        accounts_shutdown.assert_not_called()
        posts_shutdown.assert_not_called()

        # Publishing finishes last.
        publishing_running.return_value = False
        posts_page.publishing_finished.emit()

        qtbot.waitUntil(
            lambda: not window.isVisible(),
            timeout=3000,
        )

        assert not window._close_pending

        # Shutdown must happen exactly once per page.
        accounts_shutdown.assert_called_once_with()
        posts_shutdown.assert_called_once_with()


def test_main_window_waits_when_publishing_finishes_first(
    qtbot,
) -> None:
    """Closing waits for verification when publishing finishes first."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    accounts_page = window.main_content.accounts_page
    posts_page = window.main_content.posts_page

    with (
        patch.object(
            type(accounts_page),
            "verification_is_running",
            new_callable=PropertyMock,
        ) as verification_running,
        patch.object(
            type(posts_page),
            "publishing_is_running",
            new_callable=PropertyMock,
        ) as publishing_running,
        patch.object(
            accounts_page,
            "shutdown",
        ) as accounts_shutdown,
        patch.object(
            posts_page,
            "shutdown",
        ) as posts_shutdown,
    ):
        verification_running.return_value = True
        publishing_running.return_value = True

        # User requests shutdown while both workers are active.
        window.close()

        assert window.isVisible()
        assert window._close_pending

        # Publishing finishes before verification.
        publishing_running.return_value = False
        posts_page.publishing_finished.emit()

        assert window.isVisible()
        assert window._close_pending

        accounts_shutdown.assert_not_called()
        posts_shutdown.assert_not_called()

        # Verification is the final active operation.
        verification_running.return_value = False
        accounts_page.verification_finished.emit()

        qtbot.waitUntil(
            lambda: not window.isVisible(),
            timeout=3000,
        )

        assert not window._close_pending

        accounts_shutdown.assert_called_once_with()
        posts_shutdown.assert_called_once_with()



def test_main_window_waits_for_two_real_workers(
    qtbot,
    real_background_workers,
) -> None:
    """Wait for both actual Qt workers before closing."""
    workers = real_background_workers

    window = workers["window"]
    accounts_page = workers["accounts_page"]
    posts_page = workers["posts_page"]

    verification_controller = workers["verification_controller"]
    publishing_controller = workers["publishing_controller"]

    verification_started = workers["verification_started"]
    publishing_started = workers["publishing_started"]
    release_verification = workers["release_verification"]
    release_publishing = workers["release_publishing"]

    verifier = workers["verifier"]
    publisher = workers["publisher"]
    account = workers["account"]
    request = workers["request"]

    verification_controller.start(account)
    publishing_controller.start(request)

    qtbot.waitUntil(
        lambda: (
            verification_started.is_set()
            and publishing_started.is_set()
        ),
        timeout=3000,
    )

    assert accounts_page.verification_is_running
    assert posts_page.publishing_is_running

    window.close()

    assert window.isVisible()
    assert window._close_pending

    # Publishing completes first; verification remains active.
    release_publishing.set()

    qtbot.waitUntil(
        lambda: not posts_page.publishing_is_running,
        timeout=5000,
    )

    assert window.isVisible()
    assert window._close_pending
    assert accounts_page.verification_is_running

    # Verification completes; the window may now close.
    release_verification.set()

    qtbot.waitUntil(
        lambda: not window.isVisible(),
        timeout=5000,
    )

    assert not window._close_pending
    assert not accounts_page.verification_is_running
    assert not posts_page.publishing_is_running

    verifier.verify.assert_called_once_with(account)
    publisher.execute.assert_called_once()





def test_main_window_waits_for_two_real_workers_verification_first(
    qtbot,
    real_background_workers,
) -> None:
    """Wait for both real Qt workers when verification finishes first."""
    workers = real_background_workers

    window = workers["window"]
    accounts_page = workers["accounts_page"]
    posts_page = workers["posts_page"]

    verification_controller = workers["verification_controller"]
    publishing_controller = workers["publishing_controller"]

    verification_started = workers["verification_started"]
    publishing_started = workers["publishing_started"]
    release_verification = workers["release_verification"]
    release_publishing = workers["release_publishing"]

    verifier = workers["verifier"]
    publisher = workers["publisher"]
    account = workers["account"]
    request = workers["request"]

    verification_controller.start(account)
    publishing_controller.start(request)

    qtbot.waitUntil(
        lambda: (
            verification_started.is_set()
            and publishing_started.is_set()
        ),
        timeout=3000,
    )

    assert accounts_page.verification_is_running
    assert posts_page.publishing_is_running

    window.close()

    assert window.isVisible()
    assert window._close_pending

    # Verification finishes first.
    release_verification.set()

    qtbot.waitUntil(
        lambda: not accounts_page.verification_is_running,
        timeout=5000,
    )

    assert window.isVisible()
    assert window._close_pending
    assert posts_page.publishing_is_running

    # Publishing finishes last.
    release_publishing.set()

    qtbot.waitUntil(
        lambda: not window.isVisible(),
        timeout=5000,
    )

    assert not window._close_pending
    assert not accounts_page.verification_is_running
    assert not posts_page.publishing_is_running

    verifier.verify.assert_called_once_with(account)
    publisher.execute.assert_called_once()




def test_main_window_repeated_close_with_two_real_workers(
    qtbot,
    real_background_workers,
) -> None:
    """Repeated close requests wait for both real Qt workers."""
    workers = real_background_workers

    window = workers["window"]
    accounts_page = workers["accounts_page"]
    posts_page = workers["posts_page"]

    verification_controller = workers["verification_controller"]
    publishing_controller = workers["publishing_controller"]

    verification_started = workers["verification_started"]
    publishing_started = workers["publishing_started"]
    release_verification = workers["release_verification"]
    release_publishing = workers["release_publishing"]

    verifier = workers["verifier"]
    publisher = workers["publisher"]
    account = workers["account"]
    request = workers["request"]

    verification_controller.start(account)
    publishing_controller.start(request)

    qtbot.waitUntil(
        lambda: (
            verification_started.is_set()
            and publishing_started.is_set()
        ),
        timeout=3000,
    )

    assert accounts_page.verification_is_running
    assert posts_page.publishing_is_running

    # Repeated close requests while both workers are active.
    for _ in range(3):
        window.close()

    assert window.isVisible()
    assert window._close_pending

    # Verification finishes first.
    release_verification.set()

    qtbot.waitUntil(
        lambda: not accounts_page.verification_is_running,
        timeout=5000,
    )

    # Another close request while publishing is still active.
    window.close()

    assert window.isVisible()
    assert window._close_pending
    assert posts_page.publishing_is_running

    # Publishing finishes last.
    release_publishing.set()

    qtbot.waitUntil(
        lambda: not window.isVisible(),
        timeout=5000,
    )

    assert not window._close_pending
    assert not accounts_page.verification_is_running
    assert not posts_page.publishing_is_running

    verifier.verify.assert_called_once_with(account)
    publisher.execute.assert_called_once()




def test_main_window_waits_for_publishing_after_real_verification_failure(
    qtbot,
    real_background_workers,
) -> None:
    """Verification failure must not close an active publishing worker."""
    workers = real_background_workers

    window = workers["window"]
    accounts_page = workers["accounts_page"]
    posts_page = workers["posts_page"]

    verification_controller = workers["verification_controller"]
    publishing_controller = workers["publishing_controller"]

    verification_started = workers["verification_started"]
    publishing_started = workers["publishing_started"]
    release_verification = workers["release_verification"]
    release_publishing = workers["release_publishing"]

    verifier = workers["verifier"]
    publisher = workers["publisher"]
    account = workers["account"]
    request = workers["request"]

    def fail_verification(_account):
        verification_started.set()

        if not release_verification.wait(timeout=5):
            raise TimeoutError("Verification worker timed out.")

        raise RuntimeError("Simulated verification failure.")

    verifier.verify.side_effect = fail_verification

    errors = []
    verification_controller.error_occurred.connect(errors.append)

    verification_controller.start(account)
    publishing_controller.start(request)

    qtbot.waitUntil(
        lambda: (
            verification_started.is_set()
            and publishing_started.is_set()
        ),
        timeout=3000,
    )

    assert accounts_page.verification_is_running
    assert posts_page.publishing_is_running

    window.close()

    assert window.isVisible()
    assert window._close_pending

    # Verification fails while publishing remains active.
    release_verification.set()

    qtbot.waitUntil(
        lambda: not accounts_page.verification_is_running,
        timeout=5000,
    )

    assert errors == [
        "WordPress connection verification failed unexpectedly."
    ]

    assert window.isVisible()
    assert window._close_pending
    assert posts_page.publishing_is_running

    # Publishing completes successfully.
    release_publishing.set()

    qtbot.waitUntil(
        lambda: not window.isVisible(),
        timeout=5000,
    )

    assert not window._close_pending
    assert not accounts_page.verification_is_running
    assert not posts_page.publishing_is_running

    verifier.verify.assert_called_once_with(account)
    publisher.execute.assert_called_once()





def test_main_window_waits_for_verification_after_real_publishing_failure(
    qtbot,
    real_background_workers,
) -> None:
    """Publishing failure must not close an active verification worker."""
    workers = real_background_workers

    window = workers["window"]
    accounts_page = workers["accounts_page"]
    posts_page = workers["posts_page"]

    verification_controller = workers["verification_controller"]
    publishing_controller = workers["publishing_controller"]

    verification_started = workers["verification_started"]
    publishing_started = workers["publishing_started"]
    release_verification = workers["release_verification"]
    release_publishing = workers["release_publishing"]

    verifier = workers["verifier"]
    publisher = workers["publisher"]
    account = workers["account"]
    request = workers["request"]

    def fail_publishing(_request, *, on_progress=None):
        assert on_progress is None or callable(on_progress)
        publishing_started.set()

        if not release_publishing.wait(timeout=5):
            raise TimeoutError("Publishing worker timed out.")

        raise RuntimeError("Simulated publishing failure.")

    publisher.execute.side_effect = fail_publishing

    errors = []
    publishing_controller.error_occurred.connect(errors.append)

    verification_controller.start(account)
    publishing_controller.start(request)

    qtbot.waitUntil(
        lambda: (
            verification_started.is_set()
            and publishing_started.is_set()
        ),
        timeout=3000,
    )

    assert accounts_page.verification_is_running
    assert posts_page.publishing_is_running

    window.close()

    assert window.isVisible()
    assert window._close_pending

    # Publishing fails while verification remains active.
    release_publishing.set()

    qtbot.waitUntil(
        lambda: not posts_page.publishing_is_running,
        timeout=5000,
    )

    assert errors
    assert window.isVisible()
    assert window._close_pending
    assert accounts_page.verification_is_running

    # Verification completes successfully.
    release_verification.set()

    qtbot.waitUntil(
        lambda: not window.isVisible(),
        timeout=5000,
    )

    assert not window._close_pending
    assert not accounts_page.verification_is_running
    assert not posts_page.publishing_is_running

    verifier.verify.assert_called_once_with(account)
    publisher.execute.assert_called_once()

