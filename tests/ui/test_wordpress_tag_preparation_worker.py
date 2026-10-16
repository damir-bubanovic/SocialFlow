from unittest.mock import Mock

from socialflow.domain.account.account import Account
from socialflow.domain.connections.wordpress_connection_config import (
    WordPressConnectionConfig,
)
from socialflow.domain.post.tag import Tag
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.infrastructure.wordpress.wordpress_tag import WordPressTag
from socialflow.ui.workers.wordpress_tag_preparation_worker import (
    WordPressTagPreparationWorker,
)


def make_worker(
    selected_tags: tuple[Tag, ...],
    remote_tags: tuple[WordPressTag, ...] = (),
):
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
    client.list_tags.return_value = remote_tags

    worker = WordPressTagPreparationWorker(
        account=account,
        selected_tags=selected_tags,
        credential_store=credentials,
        tag_client=client,
    )

    return worker, client


def test_worker_detects_missing_tags():
    worker, client = make_worker(
        selected_tags=(
            Tag("Python"),
            Tag("SocialFlow"),
        ),
        remote_tags=(
            WordPressTag(id=12, name="Python"),
        ),
    )

    plans = []
    worker.finished.connect(plans.append)

    worker.run()

    assert len(plans) == 1
    assert plans[0].tag_names == ("SocialFlow",)
    assert plans[0].requires_confirmation is True

    client.list_tags.assert_called_once_with(
        site_url="https://example.com",
        username="admin",
        application_password="secret",
    )
    client.create_tag.assert_not_called()


def test_worker_does_not_require_confirmation_for_existing_tags():
    worker, client = make_worker(
        selected_tags=(Tag("Python"),),
        remote_tags=(
            WordPressTag(id=12, name="Python"),
        ),
    )

    plans = []
    worker.finished.connect(plans.append)

    worker.run()

    assert len(plans) == 1
    assert plans[0].requires_confirmation is False
    client.create_tag.assert_not_called()


def test_worker_reports_tag_lookup_failure():
    worker, client = make_worker(
        selected_tags=(Tag("Python"),),
    )

    client.list_tags.side_effect = RuntimeError(
        "WordPress tag lookup failed."
    )

    errors = []
    worker.failed.connect(errors.append)

    worker.run()

    assert errors == ["WordPress tag lookup failed."]
    client.create_tag.assert_not_called()

def test_new_preparation_fetches_updated_tags_after_failure():
    selected_tags = (
        Tag("Python"),
        Tag("SocialFlow"),
    )

    # First preparation: neither tag exists remotely.
    first_worker, client = make_worker(
        selected_tags=selected_tags,
    )

    first_plans = []
    first_worker.finished.connect(first_plans.append)

    first_worker.run()

    assert len(first_plans) == 1
    assert first_plans[0].tag_names == (
        "Python",
        "SocialFlow",
    )

    # Simulate a previous creation attempt:
    # Python was created, but its HTTP response was lost.
    client.list_tags.return_value = (
        WordPressTag(id=101, name="Python"),
    )

    # A new preparation worker uses the same client,
    # which now returns the updated remote tag collection.
    second_worker = WordPressTagPreparationWorker(
        account=first_worker._account,
        selected_tags=selected_tags,
        credential_store=first_worker._credential_store,
        tag_client=client,
    )

    second_plans = []
    second_worker.finished.connect(second_plans.append)

    second_worker.run()

    assert len(second_plans) == 1
    assert second_plans[0].tag_names == ("SocialFlow",)
    assert second_plans[0].requires_confirmation is True

    # Each preparation performs its own remote lookup.
    assert client.list_tags.call_count == 2

    # Preparation never creates tags automatically.
    client.create_tag.assert_not_called()