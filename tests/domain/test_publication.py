from datetime import datetime
from uuid import UUID

from socialflow.domain.account.account import Account
from socialflow.domain.language.language import Language
from socialflow.domain.post.post import Post
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.domain.publishing.publication import Publication
from socialflow.domain.publishing.publication_id import PublicationId


def test_publication_stores_published_post_information() -> None:
    publication_id = PublicationId(
        UUID("12345678-1234-5678-1234-567812345678")
    )

    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    post = Post(
        text="Hello from SocialFlow",
        language=Language.ENGLISH,
    )

    published_at = datetime(
        2026,
        10,
        5,
        20,
        30,
    )

    publication = Publication(
        id=publication_id,
        account=account,
        post=post,
        published_at=published_at,
    )

    assert publication.id == publication_id
    assert publication.account is account
    assert publication.post is post
    assert publication.published_at == published_at