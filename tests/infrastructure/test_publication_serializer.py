from datetime import datetime
from uuid import UUID

from socialflow.domain.account.account import Account
from socialflow.domain.language.language import Language
from socialflow.domain.post.post import Post
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.domain.publishing.publication import Publication
from socialflow.domain.publishing.publication_id import PublicationId
from socialflow.infrastructure.publishing.publication_serializer import (
    PublicationSerializer,
)


PUBLICATION_ID = PublicationId(
    UUID("12345678-1234-5678-1234-567812345678")
)


def create_publication() -> Publication:
    return Publication(
        id=PUBLICATION_ID,
        account=Account(
            name="Main Facebook",
            destination=PublishingDestination.FACEBOOK,
        ),
        post=Post(
            text="Hello from SocialFlow",
            language=Language.ENGLISH,
        ),
        published_at=datetime(2026, 10, 5, 21, 30),
    )


def test_publication_serializer_converts_publication_to_dict() -> None:
    publication = create_publication()

    data = PublicationSerializer.to_dict(publication)

    assert data == {
        "id": "12345678-1234-5678-1234-567812345678",
        "account": {
            "name": "Main Facebook",
            "destination": "facebook",
        },
        "post": {
            "text": "Hello from SocialFlow",
            "language": "EN",
        },
        "published_at": "2026-10-05T21:30:00",
    }


def test_publication_serializer_creates_publication_from_dict() -> None:
    data = {
        "id": "12345678-1234-5678-1234-567812345678",
        "account": {
            "name": "Main Facebook",
            "destination": "facebook",
        },
        "post": {
            "text": "Hello from SocialFlow",
            "language": "EN",
        },
        "published_at": "2026-10-05T21:30:00",
    }

    publication = PublicationSerializer.from_dict(data)

    assert publication.id == PUBLICATION_ID
    assert publication.account == Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )
    assert publication.post == Post(
        text="Hello from SocialFlow",
        language=Language.ENGLISH,
    )
    assert publication.published_at == datetime(
        2026,
        10,
        5,
        21,
        30,
    )


def test_publication_serializer_round_trip() -> None:
    original = create_publication()

    serialized = PublicationSerializer.to_dict(original)
    restored = PublicationSerializer.from_dict(serialized)

    assert restored == original
    assert restored.id == original.id