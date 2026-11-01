from datetime import datetime
from uuid import UUID
from pathlib import Path

from socialflow.modules.posts.models.image_attachment import ImageAttachment
from socialflow.domain.language.language import Language
from socialflow.modules.posts.models.post import Post
from socialflow.modules.posts.models.tag import Tag
from socialflow.modules.posts.models.publication import Publication
from socialflow.modules.posts.models.publication_id import PublicationId
from socialflow.infrastructure.accounts.account_serializer import AccountSerializer


class PublicationSerializer:
    """Convert publications to and from JSON-compatible data."""

    @staticmethod
    def to_dict(publication: Publication) -> dict:
        """Convert a publication to JSON-compatible data."""
        return {
            "id": str(publication.id),
            "account": AccountSerializer.to_dict(publication.account),
            "post": {
                "text": publication.post.text,
                "language": publication.post.language.value,
                "tags": [tag.name for tag in publication.post.tags],
                "images": [
                    str(image.path)
                    for image in publication.post.images
                ],
            },
            "published_at": publication.published_at.isoformat(),
        }

    @staticmethod
    def from_dict(data: dict) -> Publication:
        """Create a publication from serialized data."""
        return Publication(
            id=PublicationId(
                UUID(data["id"])
            ),
            account=AccountSerializer.from_dict(data["account"]),
            post=Post(
                text=data["post"]["text"],
                language=Language(data["post"]["language"]),
                tags=tuple(
                    Tag(name=name)
                    for name in data["post"].get("tags", [])
                ),
                images=tuple(
                    ImageAttachment(path=image_path)
                    for path in data["post"].get("images", [])
                    if (image_path := Path(path)).is_file()
                ),
            ),
            published_at=datetime.fromisoformat(
                data["published_at"]
            ),
        )