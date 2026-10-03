import pytest

from socialflow.application.publishing.publisher import Publisher
from socialflow.application.publishing.publisher_router import PublisherRouter
from socialflow.domain.post.post import Post
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.application.publishing.errors import (
    PublisherNotConfiguredError,
)


class RecordingPublisher(Publisher):
    """Test publisher used for routing assertions."""

    def publish(self, post: Post) -> None:
        pass


def test_publisher_router_returns_publisher_for_destination() -> None:
    facebook_publisher = RecordingPublisher()

    router = PublisherRouter(
        {
            PublishingDestination.FACEBOOK: facebook_publisher,
        }
    )

    publisher = router.publisher_for(
        PublishingDestination.FACEBOOK
    )

    assert publisher is facebook_publisher

def test_publisher_router_rejects_unconfigured_destination() -> None:
    router = PublisherRouter({})

    with pytest.raises(
        PublisherNotConfiguredError,
        match="No publisher configured for instagram.",
    ):
        router.publisher_for(PublishingDestination.INSTAGRAM)