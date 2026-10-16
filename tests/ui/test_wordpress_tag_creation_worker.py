from unittest.mock import Mock
import pytest

from socialflow.domain.account.account import Account
from socialflow.domain.connections.wordpress_connection_config import (
    WordPressConnectionConfig,
)
from socialflow.domain.post.tag import Tag
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.infrastructure.wordpress.wordpress_tag import WordPressTag
from socialflow.infrastructure.wordpress.wordpress_tag_creation_plan import (
    WordPressTagCreationPlan,
)
from socialflow.ui.workers.wordpress_tag_creation_worker import (
    WordPressTagCreationWorker,
)


def make_worker(tag_names: tuple[str, ...]):
    account = Account(
        name="WordPress",
        destination=PublishingDestination.WORDPRESS,
        wordpress_config=WordPressConnectionConfig(
            site_url="https://example.com",
            username="admin",
        ),
    )

    credentials = Mock()
    credentials.get.return_value = "secret"

    client = Mock()
    client.create_tag.side_effect = [
        WordPressTag(id=index + 1, name=name)
        for index, name in enumerate(tag_names)
    ]

    plan = WordPressTagCreationPlan(
        missing_tags=tuple(Tag(name) for name in tag_names),
    )

    worker = WordPressTagCreationWorker(
        account=account,
        plan=plan,
        credential_store=credentials,
        tag_client=client,
    )

    return worker, client


def test_worker_creates_only_approved_tags():
    worker, client = make_worker(("Python", "SocialFlow"))

    results = []
    worker.finished.connect(results.append)

    worker.run()

    assert len(results) == 1
    assert tuple(tag.name for tag in results[0]) == (
        "Python",
        "SocialFlow",
    )
    assert client.create_tag.call_count == 2
    assert [
        call.kwargs["name"]
        for call in client.create_tag.call_args_list
    ] == ["Python", "SocialFlow"]


def test_worker_skips_creation_for_empty_plan():
    worker, client = make_worker(())

    results = []
    worker.finished.connect(results.append)

    worker.run()

    assert results == [()]
    client.create_tag.assert_not_called()


def test_worker_reports_creation_failure():
    worker, client = make_worker(("Python",))
    client.create_tag.side_effect = RuntimeError(
        "WordPress tag creation failed."
    )

    errors = []
    worker.failed.connect(errors.append)

    worker.run()

    assert errors == ["WordPress tag creation failed."]


def test_worker_stops_after_first_failure():
    worker, client = make_worker(("Python", "SocialFlow"))
    client.create_tag.side_effect = RuntimeError(
        "Creation failed."
    )

    errors = []
    worker.failed.connect(errors.append)

    worker.run()

    assert errors == ["Creation failed."]
    client.create_tag.assert_called_once()

def test_retry_only_requires_tags_missing_after_partial_failure():
    from socialflow.infrastructure.wordpress.wordpress_tag_resolver import (
        WordPressTagResolver,
    )

    selected_tags = (
        Tag("Python"),
        Tag("SocialFlow"),
        Tag("Linux"),
    )

    worker, client = make_worker(
        ("Python", "SocialFlow", "Linux")
    )

    # WordPress successfully creates the first two tags,
    # but the third creation fails.
    client.create_tag.side_effect = [
        WordPressTag(id=101, name="Python"),
        WordPressTag(id=102, name="SocialFlow"),
        RuntimeError("WordPress API unavailable."),
    ]

    errors = []
    completed = []

    worker.failed.connect(errors.append)
    worker.finished.connect(completed.append)

    worker.run()

    assert errors == ["WordPress API unavailable."]
    assert completed == []
    assert client.create_tag.call_count == 3

    # Simulate a fresh WordPress tag retrieval on retry.
    remote_tags_after_failure = (
        WordPressTag(id=101, name="Python"),
        WordPressTag(id=102, name="SocialFlow"),
    )

    retry_plan = WordPressTagResolver.prepare_creation_plan(
        selected_tags=selected_tags,
        remote_tags=remote_tags_after_failure,
    )

    # Only the tag that failed should require confirmation.
    assert retry_plan.requires_confirmation is True
    assert retry_plan.tag_names == ("Linux",)

def test_network_failure_recovery_uses_fresh_remote_tag_state():
    from socialflow.infrastructure.wordpress.wordpress_tag_resolver import (
        WordPressTagResolver,
    )

    selected_tags = (
        Tag("Python"),
        Tag("SocialFlow"),
    )

    worker, client = make_worker(("Python", "SocialFlow"))

    # The first tag may have been created remotely, but its
    # HTTP response was lost before SocialFlow received it.
    client.create_tag.side_effect = ConnectionError(
        "Connection closed before receiving the response."
    )

    errors = []
    results = []

    worker.failed.connect(errors.append)
    worker.finished.connect(results.append)

    worker.run()

    assert errors == [
        "Connection closed before receiving the response."
    ]
    assert results == []

    # The worker must not blindly retry the POST.
    assert client.create_tag.call_count == 1

    # A fresh WordPress GET shows that Python now exists.
    remote_tags = (
        WordPressTag(id=101, name="Python"),
    )

    recovery_plan = WordPressTagResolver.prepare_creation_plan(
        selected_tags=selected_tags,
        remote_tags=remote_tags,
    )

    # Only SocialFlow still requires creation and approval.
    assert recovery_plan.requires_confirmation is True
    assert recovery_plan.tag_names == ("SocialFlow",)

def test_unexpected_creation_error_stops_remaining_tags():
    worker, client = make_worker(
        ("Python", "SocialFlow", "Linux")
    )

    client.create_tag.side_effect = [
        WordPressTag(id=101, name="Python"),
        RuntimeError("Unexpected WordPress response."),
    ]

    errors = []
    results = []

    worker.failed.connect(errors.append)
    worker.finished.connect(results.append)

    worker.run()

    assert errors == ["Unexpected WordPress response."]
    assert results == []

    # The first tag succeeded, the second failed,
    # and the third must never be attempted.
    assert client.create_tag.call_count == 2

    attempted_names = [
        call.kwargs["name"]
        for call in client.create_tag.call_args_list
    ]

    assert attempted_names == [
        "Python",
        "SocialFlow",
    ]

def test_invalid_creation_result_stops_remaining_tags():
    worker, client = make_worker(
        ("Python", "SocialFlow", "Linux")
    )

    client.create_tag.side_effect = [
        WordPressTag(id=101, name="Python"),
        None,
        WordPressTag(id=103, name="Linux"),
    ]

    errors = []
    results = []

    worker.failed.connect(errors.append)
    worker.finished.connect(results.append)

    worker.run()

    assert len(errors) == 1
    assert "invalid" in errors[0].lower()
    assert results == []

    # Python succeeds, SocialFlow returns an invalid result.
    # Linux must not be attempted.
    assert client.create_tag.call_count == 2

    attempted_names = [
        call.kwargs["name"]
        for call in client.create_tag.call_args_list
    ]

    assert attempted_names == [
        "Python",
        "SocialFlow",
    ]

def test_mismatched_created_tag_name_stops_remaining_tags():
    worker, client = make_worker(
        ("Python", "SocialFlow", "Linux")
    )

    client.create_tag.side_effect = [
        WordPressTag(id=101, name="Python"),
        WordPressTag(id=102, name="WrongTag"),
        WordPressTag(id=103, name="Linux"),
    ]

    errors = []
    results = []

    worker.failed.connect(errors.append)
    worker.finished.connect(results.append)

    worker.run()

    assert len(errors) == 1
    assert "SocialFlow" in errors[0]
    assert results == []

    assert client.create_tag.call_count == 2

    attempted_names = [
        call.kwargs["name"]
        for call in client.create_tag.call_args_list
    ]

    assert attempted_names == [
        "Python",
        "SocialFlow",
    ]

def test_worker_accepts_unicode_equivalent_created_tag_name() -> None:
    worker, client = make_worker(("Čakovec",))

    client.create_tag.side_effect = None
    client.create_tag.return_value = WordPressTag(
        id=101,
        name="C\u030Cakovec",
    )

    results = []
    errors = []

    worker.finished.connect(results.append)
    worker.failed.connect(errors.append)

    worker.run()

    assert errors == []
    assert results == [
        (WordPressTag(id=101, name="C\u030Cakovec"),)
    ]

    client.create_tag.assert_called_once()

def test_worker_rejects_different_unicode_created_tag_name() -> None:
    worker, client = make_worker(("Čakovec",))

    client.create_tag.side_effect = None
    client.create_tag.return_value = WordPressTag(
        id=101,
        name="Ćakovec",
    )

    results = []
    errors = []

    worker.finished.connect(results.append)
    worker.failed.connect(errors.append)

    worker.run()

    assert results == []
    assert errors == [
        "Invalid WordPress tag creation result for "
        "'Čakovec': received 'Ćakovec'."
    ]

    client.create_tag.assert_called_once()

def test_worker_accepts_case_insensitive_created_tag_name() -> None:
    worker, client = make_worker(("SocialFlow",))

    client.create_tag.side_effect = None
    client.create_tag.return_value = WordPressTag(
        id=101,
        name="socialflow",
    )

    results = []
    errors = []

    worker.finished.connect(results.append)
    worker.failed.connect(errors.append)

    worker.run()

    assert errors == []
    assert results == [
        (WordPressTag(id=101, name="socialflow"),)
    ]

    client.create_tag.assert_called_once()

def test_interruption_prevents_remaining_tag_creation_requests(qtbot):
    from threading import Event

    from PySide6.QtCore import QThread

    worker, client = make_worker(
        ("Python", "SocialFlow", "Linux")
    )

    first_request_started = Event()
    allow_first_request_to_finish = Event()

    errors = []
    results = []

    def create_tag(**kwargs):
        first_request_started.set()

        if not allow_first_request_to_finish.wait(timeout=3):
            raise TimeoutError("Test synchronization timed out.")

        return WordPressTag(
            id=101,
            name=kwargs["name"],
        )

    client.create_tag.side_effect = create_tag

    worker.failed.connect(errors.append)
    worker.finished.connect(results.append)

    thread = QThread()
    worker.moveToThread(thread)

    thread.started.connect(worker.run)
    worker.finished.connect(thread.quit)
    worker.failed.connect(thread.quit)
    thread.finished.connect(worker.deleteLater)

    try:
        thread.start()

        qtbot.waitUntil(
            first_request_started.is_set,
            timeout=3000,
        )

        thread.requestInterruption()
        allow_first_request_to_finish.set()

        qtbot.waitUntil(
            lambda: not thread.isRunning(),
            timeout=5000,
        )

        thread.wait()

        assert client.create_tag.call_count == 1
        assert [
            call.kwargs["name"]
            for call in client.create_tag.call_args_list
        ] == ["Python"]

        assert errors == [
            "WordPress tag creation was interrupted."
        ]
        assert results == []

    finally:
        allow_first_request_to_finish.set()
        thread.requestInterruption()
        thread.quit()

        if not thread.wait(5000):
            pytest.fail(
                "WordPress tag creation test thread did not stop."
            )