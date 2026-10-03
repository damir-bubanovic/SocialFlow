from socialflow.domain.language.language import Language
from socialflow.domain.post.post import Post
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.domain.publishing.publish_request import PublishRequest


def test_publish_request_contains_post_and_destinations() -> None:
    post = Post(
        text="Hello from SocialFlow",
        language=Language.ENGLISH,
    )

    request = PublishRequest(
        post=post,
        destinations=(
            PublishingDestination.FACEBOOK,
            PublishingDestination.WORDPRESS,
        ),
    )

    assert request.post == post
    assert request.destinations == (
        PublishingDestination.FACEBOOK,
        PublishingDestination.WORDPRESS,
    )