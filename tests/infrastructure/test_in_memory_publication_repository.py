from datetime import datetime, timedelta
from uuid import UUID

from socialflow.domain.account.account import Account
from socialflow.domain.language.language import Language
from socialflow.domain.post.image_attachment import ImageAttachment
from socialflow.domain.post.post import Post
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.domain.publishing.publication import Publication
from socialflow.domain.publishing.publication_id import PublicationId
from socialflow.infrastructure.publishing.in_memory_publication_repository import (
    InMemoryPublicationRepository,
)


def create_publication(
    account: Account,
    text: str,
    published_at: datetime,
    publication_id: UUID,
) -> Publication:
    return Publication(
        id=PublicationId(publication_id),
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
        UUID("11111111-1111-1111-1111-111111111111"),
    )
    wordpress_publication = create_publication(
        wordpress,
        "WordPress post",
        now,
        UUID("22222222-2222-2222-2222-222222222222"),
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
        UUID("11111111-1111-1111-1111-111111111111"),
    )
    newer = create_publication(
        account,
        "Newer post",
        now + timedelta(minutes=1),
        UUID("22222222-2222-2222-2222-222222222222"),
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

    publication_ids = (
        UUID("00000000-0000-0000-0000-000000000001"),
        UUID("00000000-0000-0000-0000-000000000002"),
        UUID("00000000-0000-0000-0000-000000000003"),
        UUID("00000000-0000-0000-0000-000000000004"),
        UUID("00000000-0000-0000-0000-000000000005"),
        UUID("00000000-0000-0000-0000-000000000006"),
    )

    publications = [
        create_publication(
            account,
            f"Post {index}",
            start + timedelta(minutes=index),
            publication_ids[index],
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

    publication_ids = (
        UUID("00000000-0000-0000-0000-000000000001"),
        UUID("00000000-0000-0000-0000-000000000002"),
        UUID("00000000-0000-0000-0000-000000000003"),
    )

    publications = [
        create_publication(
            account,
            f"Post {index}",
            start + timedelta(minutes=index),
            publication_ids[index],
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

def test_repository_detects_missing_publication_images(tmp_path) -> None:
    image_path = tmp_path / "deleted.png"
    image_path.write_bytes(b"image content")

    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    original = create_publication(
        account,
        "Post with missing image",
        datetime(2026, 10, 8, 16, 0),
        UUID("11111111-1111-1111-1111-111111111111"),
    )

    publication = Publication(
        id=original.id,
        account=original.account,
        post=Post(
            text=original.post.text,
            language=original.post.language,
            images=(ImageAttachment(path=image_path),),
        ),
        published_at=original.published_at,
    )

    repository = InMemoryPublicationRepository()
    repository.add(publication)

    image_path.unlink()

    assert repository.missing_images_for_publication(
        publication.id
    ) == (image_path,)


def test_repository_returns_no_missing_images_when_files_exist(
    tmp_path,
) -> None:
    image_path = tmp_path / "existing.png"
    image_path.write_bytes(b"image content")

    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    original = create_publication(
        account,
        "Post with existing image",
        datetime(2026, 10, 8, 16, 0),
        UUID("22222222-2222-2222-2222-222222222222"),
    )

    publication = Publication(
        id=original.id,
        account=original.account,
        post=Post(
            text=original.post.text,
            language=original.post.language,
            images=(ImageAttachment(path=image_path),),
        ),
        published_at=original.published_at,
    )

    repository = InMemoryPublicationRepository()
    repository.add(publication)

    assert repository.missing_images_for_publication(
        publication.id
    ) == ()


def test_repository_returns_no_missing_images_for_unknown_id() -> None:
    repository = InMemoryPublicationRepository()

    unknown_id = PublicationId(
        UUID("99999999-9999-9999-9999-999999999999")
    )

    assert repository.missing_images_for_publication(
        unknown_id
    ) == ()