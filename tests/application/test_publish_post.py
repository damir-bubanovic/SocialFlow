import pytest

from socialflow.application.publishing.errors import EmptyPostError
from socialflow.application.publishing.publish_post import PublishPost
from socialflow.application.publishing.publisher import Publisher
from socialflow.application.publishing.publisher_router import PublisherRouter
from socialflow.domain.language.language import Language
from socialflow.domain.post.post import Post
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.domain.publishing.publish_request import PublishRequest


class RecordingPublisher(Publisher):
    """Test publisher that records published posts."""

    def __init__(self) -> None:
        self.published_posts: list[Post] = []

    def publish(self, post: Post) -> None:
        self.published_posts.append(post)


def test_publish_post_publishes_to_requested_destinations() -> None:
    facebook_publisher = RecordingPublisher()
    wordpress_publisher = RecordingPublisher()

    router = PublisherRouter(
        {
            PublishingDestination.FACEBOOK: facebook_publisher,
            PublishingDestination.WORDPRESS: wordpress_publisher,
        }
    )
    service = PublishPost(router)

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

    service.execute(request)

    assert facebook_publisher.published_posts == [post]
    assert wordpress_publisher.published_posts == [post]


def test_publish_post_rejects_empty_post() -> None:
    publisher = RecordingPublisher()
    router = PublisherRouter(
        {
            PublishingDestination.FACEBOOK: publisher,
        }
    )
    service = PublishPost(router)

    post = Post(
        text="   ",
        language=Language.CROATIAN,
    )
    request = PublishRequest(
        post=post,
        destinations=(PublishingDestination.FACEBOOK,),
    )

    with pytest.raises(
        EmptyPostError,
        match="Cannot publish a post without content.",
    ):
        service.execute(request)

    assert publisher.published_posts == []