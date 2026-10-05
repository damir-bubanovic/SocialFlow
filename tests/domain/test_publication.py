from datetime import datetime

from socialflow.domain.account.account import Account
from socialflow.domain.language.language import Language
from socialflow.domain.post.post import Post
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.domain.publishing.publication import Publication


def test_publication_stores_published_post_information() -> None:
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
        account=account,
        post=post,
        published_at=published_at,
    )

    assert publication.account is account
    assert publication.post is post
    assert publication.published_at == published_at