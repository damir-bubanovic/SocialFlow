from pathlib import Path

from socialflow.application.images.image_preparation_service import (
    ImagePreparationService,
)
from socialflow.application.publishing.errors import (
    EmptyPostError,
    ImagePreparationNotConfiguredError,
)
from socialflow.application.publishing.prepared_post import PreparedPost
from socialflow.application.publishing.publish_result import PublishResult
from socialflow.application.publishing.publisher_router import PublisherRouter
from socialflow.domain.publishing.publish_request import PublishRequest


class PublishPost:
    """Application service for publishing a post."""

    def __init__(
        self,
        publisher_router: PublisherRouter,
        image_preparation_service: ImagePreparationService | None = None,
        image_output_directory: Path | None = None,
    ) -> None:
        self._publisher_router = publisher_router
        self._image_preparation_service = image_preparation_service
        self._image_output_directory = image_output_directory

    def execute(self, request: PublishRequest) -> tuple[PublishResult, ...]:
        """Publish the post and return one result for every account."""
        if not request.post.has_content():
            raise EmptyPostError("Cannot publish a post without content.")

        if request.post.images and (
                self._image_preparation_service is None
                or self._image_output_directory is None
        ):
            raise ImagePreparationNotConfiguredError(
                "Image preparation must be configured before publishing images."
            )

        results: list[PublishResult] = []

        for account in request.accounts:
            publisher = self._publisher_router.publisher_for(
                account.destination
            )

            prepared_images = ()

            if request.post.images:
                destination_directory = (
                        self._image_output_directory
                        / str(account.destination)
                )

                prepared_images = (
                    self._image_preparation_service.prepare_all(
                        attachments=request.post.images,
                        destination=account.destination,
                        output_directory=destination_directory,
                    )
                )

            prepared_post = PreparedPost(
                source=request.post,
                images=prepared_images,
            )

            try:
                publisher.publish(prepared_post)

                results.append(
                    PublishResult(
                        account=account,
                        succeeded=True,
                    )
                )
            except Exception as error:
                results.append(
                    PublishResult(
                        account=account,
                        succeeded=False,
                        error=error,
                    )
                )
            finally:
                if (
                        prepared_images
                        and self._image_preparation_service is not None
                ):
                    self._image_preparation_service.cleanup(
                        prepared_images
                    )

        return tuple(results)