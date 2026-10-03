from socialflow.application.publishing.composite_publisher import (
    CompositePublisher,
)
from socialflow.application.publishing.publisher import Publisher
from socialflow.domain.language.language import Language
from socialflow.domain.post.post import Post


class RecordingPublisher(Publisher):
    """Test publisher that records published posts."""

    def __init__(self) -> None:
        self.published_posts: list[Post] = []

    def publish(self, post: Post) -> None:
        self.published_posts.append(post)


def test_composite_publisher_publishes_to_all_publishers() -> None:
    first_publisher = RecordingPublisher()
    second_publisher = RecordingPublisher()

    publisher = CompositePublisher(
        [
            first_publisher,
            second_publisher,
        ]
    )

    post = Post(
        text="Hello from SocialFlow",
        language=Language.ENGLISH,
    )

    publisher.publish(post)

    assert first_publisher.published_posts == [post]
    assert second_publisher.published_posts == [post]