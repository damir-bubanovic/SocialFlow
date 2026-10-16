from unittest.mock import Mock

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