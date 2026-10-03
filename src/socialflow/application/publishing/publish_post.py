from socialflow.application.publishing.errors import EmptyPostError
from socialflow.application.publishing.publisher_router import PublisherRouter
from socialflow.domain.publishing.publish_request import PublishRequest


class PublishPost:
    """Application service for publishing a post."""

    def __init__(self, publisher_router: PublisherRouter) -> None:
        self._publisher_router = publisher_router

    def execute(self, request: PublishRequest) -> None:
        """Publish the post to every requested destination."""
        if not request.post.has_content():
            raise EmptyPostError("Cannot publish a post without content.")

        for destination in request.destinations:
            publisher = self._publisher_router.publisher_for(destination)
            publisher.publish(request.post)