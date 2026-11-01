from socialflow.modules.accounts.models.account import Account
from socialflow.modules.posts.models.language import Language
from socialflow.modules.posts.models.post import Post
from socialflow.modules.posts.models.destination import PublishingDestination
from socialflow.modules.posts.models.publish_request import PublishRequest


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