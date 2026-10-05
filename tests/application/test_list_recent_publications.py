from datetime import datetime, timedelta

from socialflow.application.publishing.list_recent_publications import (
    ListRecentPublications,
)
from socialflow.domain.account.account import Account
from socialflow.domain.language.language import Language
from socialflow.domain.post.post import Post
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.domain.publishing.publication import Publication
from socialflow.infrastructure.publishing.in_memory_publication_repository import (
    InMemoryPublicationRepository,
)


def test_list_recent_publications_returns_recent_account_history() -> None:
    repository = InMemoryPublicationRepository()

    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    start = datetime(2026, 10, 5, 20, 0)

    publications = [
        Publication(
            account=account,
            post=Post(
                text=f"Post {index}",
                language=Language.ENGLISH,
            ),
            published_at=start + timedelta(minutes=index),
        )
        for index in range(6)
    ]

    for publication in publications:
        repository.add(publication)

    service = ListRecentPublications(repository)

    assert service.execute(account) == tuple(
        reversed(publications[1:])
    )


def test_list_recent_publications_supports_custom_limit() -> None:
    repository = InMemoryPublicationRepository()

    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    start = datetime(2026, 10, 5, 20, 0)

    publications = [
        Publication(
            account=account,
            post=Post(
                text=f"Post {index}",
                language=Language.ENGLISH,
            ),
            published_at=start + timedelta(minutes=index),
        )
        for index in range(3)
    ]

    for publication in publications:
        repository.add(publication)

    service = ListRecentPublications(repository)

    assert service.execute(
        account,
        limit=2,
    ) == (
        publications[2],
        publications[1],
    )