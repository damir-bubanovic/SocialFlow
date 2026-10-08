import pytest

from socialflow.application.publishing.errors import (
    PublisherNotConfiguredError,
)
from socialflow.application.publishing.prepared_post import PreparedPost
from socialflow.application.publishing.unconfigured_publisher import (
    UnconfiguredPublisher,
)
from socialflow.domain.language.language import Language
from socialflow.domain.post.post import Post


def test_unconfigured_publisher_rejects_external_publishing() -> None:
    publisher = UnconfiguredPublisher()

    post = PreparedPost(
        source=Post(
            text="Test publishing.",
            language=Language.ENGLISH,
        )
    )

    with pytest.raises(
        PublisherNotConfiguredError,
        match="External publishing is not configured",
    ):
        publisher.publish(post)