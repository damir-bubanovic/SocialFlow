from datetime import datetime
from uuid import UUID

from socialflow.domain.account.account import Account
from socialflow.domain.language.language import Language
from socialflow.domain.post.post import Post
from socialflow.domain.post.tag import Tag
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.domain.publishing.publication import Publication
from socialflow.domain.publishing.publication_id import PublicationId
from socialflow.infrastructure.publishing.publication_serializer import (
    PublicationSerializer,
)
from socialflow.domain.post.image_attachment import ImageAttachment


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
            "id": str(publication.account.id),
            "name": "Main Facebook",
            "destination": "facebook",
        },
        "post": {
            "text": "Hello from SocialFlow",
            "language": "EN",
            "tags": [],
            "images": []
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
    assert publication.account.name == "Main Facebook"
    assert publication.account.destination == PublishingDestination.FACEBOOK
    assert publication.account.id.value.int == 0
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

def test_publication_serializer_preserves_tags() -> None:
    original = create_publication()

    original = Publication(
        id=original.id,
        account=original.account,
        post=Post(
            text=original.post.text,
            language=original.post.language,
            tags=(
                Tag(name="Python"),
                Tag(name="SocialFlow"),
            ),
        ),
        published_at=original.published_at,
    )

    data = PublicationSerializer.to_dict(original)
    restored = PublicationSerializer.from_dict(data)

    assert data["post"]["tags"] == [
        "Python",
        "SocialFlow",
    ]
    assert restored == original


def test_publication_serializer_supports_legacy_posts_without_tags() -> None:
    original = create_publication()
    data = PublicationSerializer.to_dict(original)

    del data["post"]["tags"]

    restored = PublicationSerializer.from_dict(data)

    assert restored.post.tags == ()

def test_publication_serializer_preserves_images(tmp_path) -> None:
    image_path = tmp_path / "example.png"
    image_path.write_bytes(b"test image")

    original = create_publication()

    original = Publication(
        id=original.id,
        account=original.account,
        post=Post(
            text=original.post.text,
            language=original.post.language,
            images=(ImageAttachment(path=image_path),),
        ),
        published_at=original.published_at,
    )

    data = PublicationSerializer.to_dict(original)
    restored = PublicationSerializer.from_dict(data)

    assert data["post"]["images"] == [str(image_path)]
    assert restored == original


def test_publication_serializer_supports_legacy_posts_without_images() -> None:
    original = create_publication()
    data = PublicationSerializer.to_dict(original)

    del data["post"]["images"]

    restored = PublicationSerializer.from_dict(data)

    assert restored.post.images == ()

def test_publication_serializer_skips_missing_images(
    tmp_path,
) -> None:
    original = create_publication()
    data = PublicationSerializer.to_dict(original)

    missing_path = tmp_path / "deleted.png"

    data["post"]["images"] = [str(missing_path)]

    restored = PublicationSerializer.from_dict(data)

    assert restored.post.images == ()
    assert restored.post.text == original.post.text
    assert restored.post.language == original.post.language
    assert restored.id == original.id

def test_publication_serializer_preserves_account_id() -> None:
    original = create_publication()

    serialized = PublicationSerializer.to_dict(original)
    restored = PublicationSerializer.from_dict(serialized)

    assert serialized["account"]["id"] == str(original.account.id)
    assert restored.account.id == original.account.id
    assert restored == original