
from unittest.mock import Mock

from socialflow.domain.account.account import Account
from socialflow.domain.post.tag import Tag
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.ui.workers.tag_loading_worker import TagLoadingWorker


def make_account() -> Account:
    return Account(
        name="WordPress",
        destination=PublishingDestination.WORDPRESS,
    )


def test_worker_emits_loaded_tags() -> None:
    account = make_account()
    expected_tags = (Tag(name="Python"),)

    list_tags = Mock()
    list_tags.execute.return_value = expected_tags

    worker = TagLoadingWorker(
        list_tags=list_tags,
        account=account,
    )

    received = []
    worker.finished.connect(received.append)

    worker.run()

    assert received == [expected_tags]
    list_tags.execute.assert_called_once_with(account)


def test_worker_emits_error_on_failure() -> None:
    account = make_account()

    list_tags = Mock()
    list_tags.execute.side_effect = ValueError(
        "WordPress application password is missing."
    )

    worker = TagLoadingWorker(
        list_tags=list_tags,
        account=account,
    )

    errors = []
    worker.failed.connect(errors.append)

    worker.run()

    assert errors == [
        "WordPress application password is missing."
    ]
