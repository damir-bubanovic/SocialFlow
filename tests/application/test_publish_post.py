import pytest

from socialflow.application.publishing.publish_post import PublishPost
from socialflow.application.publishing.publisher import Publisher
from socialflow.domain.language.language import Language
from socialflow.domain.post.post import Post
from socialflow.application.publishing.errors import EmptyPostError


class RecordingPublisher(Publisher):
    """Test publisher that records published posts."""

    def __init__(self) -> None:
        self.published_post: Post | None = None

    def publish(self, post: Post) -> None:
        self.published_post = post


def test_publish_post_delegates_to_publisher() -> None:
    publisher = RecordingPublisher()
    service = PublishPost(publisher)

    post = Post(
        text="Hello from SocialFlow",
        language=Language.ENGLISH,
    )

    service.execute(post)

    assert publisher.published_post == post

def test_publish_post_rejects_empty_post() -> None:
    publisher = RecordingPublisher()
    service = PublishPost(publisher)

    post = Post(
        text="   ",
        language=Language.CROATIAN,
    )

    with pytest.raises(
        EmptyPostError,
        match="Cannot publish a post without content.",
    ):
        service.execute(post)

    assert publisher.published_post is None