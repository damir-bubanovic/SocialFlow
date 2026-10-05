from datetime import datetime, timedelta

from socialflow.domain.account.account import Account
from socialflow.domain.language.language import Language
from socialflow.domain.post.post import Post
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.domain.publishing.publication import Publication
from socialflow.infrastructure.publishing.json_publication_repository import (
    JsonPublicationRepository,
)


def create_publication(
    account: Account,
    text: str,
    published_at: datetime,
) -> Publication:
    return Publication(
        account=account,
        post=Post(
            text=text,
            language=Language.ENGLISH,
        ),
        published_at=published_at,
    )


def test_repository_returns_empty_history_when_file_does_not_exist(
    tmp_path,
) -> None:
    repository = JsonPublicationRepository(
        tmp_path / "publications.json"
    )

    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    assert repository.recent_for_account(account) == ()


def test_repository_persists_publication(tmp_path) -> None:
    file_path = tmp_path / "publications.json"

    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    publication = create_publication(
        account,
        "Hello from SocialFlow",
        datetime(2026, 10, 5, 21, 30),
    )

    repository = JsonPublicationRepository(file_path)
    repository.add(publication)

    reloaded_repository = JsonPublicationRepository(file_path)

    assert reloaded_repository.recent_for_account(account) == (
        publication,
    )


def test_repository_returns_requested_account_only(tmp_path) -> None:
    repository = JsonPublicationRepository(
        tmp_path / "publications.json"
    )

    facebook = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )
    wordpress = Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    published_at = datetime(2026, 10, 5, 21, 30)

    facebook_publication = create_publication(
        facebook,
        "Facebook post",
        published_at,
    )
    wordpress_publication = create_publication(
        wordpress,
        "WordPress post",
        published_at,
    )

    repository.add(facebook_publication)
    repository.add(wordpress_publication)

    assert repository.recent_for_account(facebook) == (
        facebook_publication,
    )


def test_repository_returns_newest_publications_first(tmp_path) -> None:
    repository = JsonPublicationRepository(
        tmp_path / "publications.json"
    )

    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    start = datetime(2026, 10, 5, 21, 0)

    older = create_publication(
        account,
        "Older post",
        start,
    )
    newer = create_publication(
        account,
        "Newer post",
        start + timedelta(minutes=1),
    )

    repository.add(older)
    repository.add(newer)

    assert repository.recent_for_account(account) == (
        newer,
        older,
    )


def test_repository_returns_five_publications_by_default(
    tmp_path,
) -> None:
    repository = JsonPublicationRepository(
        tmp_path / "publications.json"
    )

    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    start = datetime(2026, 10, 5, 21, 0)

    publications = [
        create_publication(
            account,
            f"Post {index}",
            start + timedelta(minutes=index),
        )
        for index in range(6)
    ]

    for publication in publications:
        repository.add(publication)

    assert repository.recent_for_account(account) == tuple(
        reversed(publications[1:])
    )


def test_repository_respects_custom_limit(tmp_path) -> None:
    repository = JsonPublicationRepository(
        tmp_path / "publications.json"
    )

    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    start = datetime(2026, 10, 5, 21, 0)

    publications = [
        create_publication(
            account,
            f"Post {index}",
            start + timedelta(minutes=index),
        )
        for index in range(3)
    ]

    for publication in publications:
        repository.add(publication)

    assert repository.recent_for_account(
        account,
        limit=2,
    ) == (
        publications[2],
        publications[1],
    )