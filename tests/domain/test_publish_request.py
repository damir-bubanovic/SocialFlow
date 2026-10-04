from socialflow.domain.account.account import Account
from socialflow.domain.language.language import Language
from socialflow.domain.post.post import Post
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.domain.publishing.publish_request import PublishRequest


def test_publish_request_contains_post_and_accounts() -> None:
    post = Post(
        text="Hello from SocialFlow",
        language=Language.ENGLISH,
    )
    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    request = PublishRequest(
        post=post,
        accounts=(account,),
    )

    assert request.post == post
    assert request.accounts == (account,)