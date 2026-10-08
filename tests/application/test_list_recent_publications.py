from datetime import datetime, timedelta
from uuid import UUID

from socialflow.application.publishing.list_recent_publications import (
    ListRecentPublications,
)
from socialflow.domain.account.account import Account
from socialflow.domain.language.language import Language
from socialflow.domain.post.post import Post
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.domain.publishing.publication import Publication
from socialflow.domain.publishing.publication_id import PublicationId
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

    publication_ids = (
        UUID("00000000-0000-0000-0000-000000000001"),
        UUID("00000000-0000-0000-0000-000000000002"),
        UUID("00000000-0000-0000-0000-000000000003"),
        UUID("00000000-0000-0000-0000-000000000004"),
        UUID("00000000-0000-0000-0000-000000000005"),
        UUID("00000000-0000-0000-0000-000000000006"),
    )

    publications = [
        Publication(
            id=PublicationId(publication_ids[index]),
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

    publication_ids = (
        UUID("00000000-0000-0000-0000-000000000001"),
        UUID("00000000-0000-0000-0000-000000000002"),
        UUID("00000000-0000-0000-0000-000000000003"),
    )

    publications = [
        Publication(
            id=PublicationId(publication_ids[index]),
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