import logging
from pathlib import Path
from collections.abc import Callable

from socialflow.modules.posts.services.image_preparation_service import (
    ImagePreparationService,
)
from socialflow.modules.posts.services.errors import (
    EmptyPostError,
    ImagePreparationNotConfiguredError,
)
from socialflow.modules.posts.services.prepared_post import PreparedPost
from socialflow.modules.posts.services.publish_result import PublishResult
from socialflow.modules.posts.services.publisher_router import PublisherRouter
from socialflow.modules.posts.models.publish_request import PublishRequest
from socialflow.modules.posts.repositories.publication_repository import (
    PublicationRepository,
)
from socialflow.application.time.clock import Clock
from socialflow.modules.posts.models.publication import Publication
from socialflow.modules.posts.services.publication_id_generator import (
    PublicationIdGenerator,
)


logger = logging.getLogger(__name__)


class PublishPost:
    """Application service for publishing a post."""

    def __init__(
        self,
        publisher_router: PublisherRouter,
        publication_id_generator: PublicationIdGenerator,
        image_preparation_service: ImagePreparationService | None = None,
        image_output_directory: Path | None = None,
        publication_repository: PublicationRepository | None = None,
        clock: Clock | None = None,
    ) -> None:
        self._publisher_router = publisher_router
        self._publication_id_generator = publication_id_generator
        self._image_preparation_service = image_preparation_service
        self._image_output_directory = image_output_directory
        self._publication_repository = publication_repository
        self._clock = clock

    def execute(
        self,
        request: PublishRequest,
        on_progress: Callable[[PublishResult], None] | None = None,
    ) -> tuple[PublishResult, ...]:
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
            prepared_images = ()

            try:
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

                publisher = self._publisher_router.publisher_for_account(
                    account
                )
                publisher.publish(prepared_post)

                persistence_error: Exception | None = None

                if (
                    self._publication_repository is not None
                    and self._clock is not None
                ):
                    try:
                        self._publication_repository.add(
                            Publication(
                                id=self._publication_id_generator.generate(),
                                account=account,
                                post=request.post,
                                published_at=self._clock.now(),
                            )
                        )
                    except Exception as error:
                        persistence_error = error

                        logger.error(
                            "Publication history persistence failed "
                            "for account %s (%s): %s",
                            account.name,
                            account.destination,
                            type(error).__name__,
                        )

                results.append(
                    PublishResult(
                        account=account,
                        succeeded=True,
                        persistence_error=persistence_error,
                    )
                )

            except Exception as error:
                logger.error(
                    "Publishing failed for account %s (%s): %s",
                    account.name,
                    account.destination,
                    type(error).__name__,
                )
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
                    try:
                        self._image_preparation_service.cleanup(
                            prepared_images
                        )
                    # noinspection PyBroadException
                    except Exception as cleanup_error:
                        logger.exception(
                            "Failed to clean up prepared images for account %s",
                            account.name,
                        )

                        previous_result = results[-1]

                        results[-1] = PublishResult(
                            account=previous_result.account,
                            succeeded=previous_result.succeeded,
                            error=previous_result.error,
                            cleanup_error=cleanup_error,
                            persistence_error=previous_result.persistence_error,
                        )

            if on_progress is not None:
                on_progress(results[-1])

        return tuple(results)