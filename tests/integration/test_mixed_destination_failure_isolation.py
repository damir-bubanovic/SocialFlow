
"""Integration tests for mixed-destination publishing failures."""

from pathlib import Path
from unittest.mock import Mock

import pytest
from PIL import Image

from socialflow.core.destination import PublishingDestination
from socialflow.modules.accounts.models.account import Account
from socialflow.modules.posts.models.image_attachment import ImageAttachment
from socialflow.modules.posts.models.language import Language
from socialflow.modules.posts.models.post import Post
from socialflow.modules.posts.models.publish_request import PublishRequest
from socialflow.modules.posts.services.default_image_profiles import (
    DEFAULT_IMAGE_PROFILES,
)
from socialflow.modules.posts.services.image_preparation_service import (
    ImagePreparationService,
)
from socialflow.modules.posts.services.image_profile_provider import (
    ImageProfileProvider,
)
from socialflow.modules.posts.services.publish_post import PublishPost
from socialflow.modules.posts.services.publisher_router import PublisherRouter


@pytest.mark.parametrize(
    "failing_destination",
    [
        PublishingDestination.FACEBOOK,
        PublishingDestination.WORDPRESS,
    ],
)
def test_failure_does_not_block_other_destination(
    tmp_path: Path,
    failing_destination: PublishingDestination,
) -> None:
    source_path = tmp_path / "holiday photo.png"
    Image.new("RGB", (2400, 1600)).save(source_path)

    facebook_account = Account(
        name="Facebook Page",
        destination=PublishingDestination.FACEBOOK,
    )
    wordpress_account = Account(
        name="WordPress Site",
        destination=PublishingDestination.WORDPRESS,
    )

    publishers = {
        PublishingDestination.FACEBOOK: Mock(),
        PublishingDestination.WORDPRESS: Mock(),
    }

    publishers[failing_destination].publish.side_effect = RuntimeError(
        "Simulated publishing failure"
    )

    preparation = ImagePreparationService(
        profile_provider=ImageProfileProvider(
            profiles=DEFAULT_IMAGE_PROFILES,
        )
    )

    output_directory = tmp_path / "prepared"

    service = PublishPost(
        publisher_router=PublisherRouter(publishers=publishers),
        publication_id_generator=Mock(),
        image_preparation_service=preparation,
        image_output_directory=output_directory,
    )

    post = Post(
        title="Holiday photos",
        text="Publishing to Facebook and WordPress",
        language=Language.ENGLISH,
        images=(ImageAttachment(path=source_path),),
    )

    results = service.execute(
        PublishRequest(
            post=post,
            accounts=(facebook_account, wordpress_account),
        )
    )

    assert len(results) == 2

    for result in results:
        if result.account.destination is failing_destination:
            assert result.succeeded is False
            assert isinstance(result.error, RuntimeError)
        else:
            assert result.succeeded is True
            assert result.error is None

    # Both publishers must have been called.
    for publisher in publishers.values():
        publisher.publish.assert_called_once()

    # Each publisher receives an image prepared for its destination.
    for destination, publisher in publishers.items():
        prepared_post = publisher.publish.call_args.args[0]

        assert len(prepared_post.images) == 1
        assert prepared_post.images[0].destination is destination

    # Neither destination may leave temporary prepared images behind.
    assert not list(output_directory.rglob("*.jpg"))
    assert not list(output_directory.rglob("*.png"))
    assert not list(output_directory.rglob("*.webp"))

    # Original source image must remain intact.
    assert source_path.is_file()
