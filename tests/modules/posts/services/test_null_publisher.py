from socialflow.modules.posts.services.null_publisher import NullPublisher
from socialflow.domain.language.language import Language
from socialflow.modules.posts.models.post import Post


def test_null_publisher_accepts_post() -> None:
    publisher = NullPublisher()
    post = Post(
        text="Hello from SocialFlow",
        language=Language.ENGLISH,
    )

    publisher.publish(post)