from socialflow.application.publishing.publisher import Publisher
from socialflow.domain.language.language import Language
from socialflow.domain.post.post import Post


class RecordingPublisher(Publisher):
    """Test publisher that records the received post."""

    def __init__(self) -> None:
        self.published_post: Post | None = None

    def publish(self, post: Post) -> None:
        self.published_post = post


def test_publisher_contract_accepts_post() -> None:
    publisher = RecordingPublisher()
    post = Post(
        text="Hello from SocialFlow",
        language=Language.ENGLISH,
    )

    publisher.publish(post)

    assert publisher.published_post == post