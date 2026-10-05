from datetime import datetime

from socialflow.domain.account.account import Account
from socialflow.domain.language.language import Language
from socialflow.domain.post.post import Post
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.domain.publishing.publication import Publication


class PublicationSerializer:
    """Convert publications to and from JSON-compatible data."""

    @staticmethod
    def to_dict(publication: Publication) -> dict:
        """Convert a publication to JSON-compatible data."""
        return {
            "account": {
                "name": publication.account.name,
                "destination": publication.account.destination.value,
            },
            "post": {
                "text": publication.post.text,
                "language": publication.post.language.value,
            },
            "published_at": publication.published_at.isoformat(),
        }

    @staticmethod
    def from_dict(data: dict) -> Publication:
        """Create a publication from serialized data."""
        return Publication(
            account=Account(
                name=data["account"]["name"],
                destination=PublishingDestination(
                    data["account"]["destination"]
                ),
            ),
            post=Post(
                text=data["post"]["text"],
                language=Language(data["post"]["language"]),
            ),
            published_at=datetime.fromisoformat(
                data["published_at"]
            ),
        )