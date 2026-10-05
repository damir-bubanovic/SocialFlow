from datetime import datetime, timedelta

from socialflow.domain.account.account import Account
from socialflow.domain.language.language import Language
from socialflow.domain.post.post import Post
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.domain.publishing.publication import Publication
from socialflow.infrastructure.publishing.in_memory_publication_repository import (
    InMemoryPublicationRepository,
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


def test_repository_returns_publications_for_requested_account_only() -> None:
    repository = InMemoryPublicationRepository()

    facebook = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )
    wordpress = Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    now = datetime(2026, 10, 5, 20, 0)

    facebook_publication = create_publication(
        facebook,
        "Facebook post",
        now,
    )
    wordpress_publication = create_publication(
        wordpress,
        "WordPress post",
        now,
    )

    repository.add(facebook_publication)
    repository.add(wordpress_publication)

    assert repository.recent_for_account(facebook) == (
        facebook_publication,
    )


def test_repository_returns_newest_publications_first() -> None:
    repository = InMemoryPublicationRepository()

    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    now = datetime(2026, 10, 5, 20, 0)

    older = create_publication(
        account,
        "Older post",
        now,
    )
    newer = create_publication(
        account,
        "Newer post",
        now + timedelta(minutes=1),
    )

    repository.add(older)
    repository.add(newer)

    assert repository.recent_for_account(account) == (
        newer,
        older,
    )


def test_repository_returns_five_publications_by_default() -> None:
    repository = InMemoryPublicationRepository()

    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    start = datetime(2026, 10, 5, 20, 0)

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


def test_repository_respects_custom_limit() -> None:
    repository = InMemoryPublicationRepository()

    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    start = datetime(2026, 10, 5, 20, 0)

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