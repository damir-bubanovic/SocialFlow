
"""Integration tests for Facebook Page photo publishing."""

from pathlib import Path
from typing import Mapping
from unittest.mock import Mock
from uuid import UUID

from PIL import Image

from socialflow.core.destination import PublishingDestination
from socialflow.modules.accounts.models.account import Account
from socialflow.modules.accounts.models.facebook_page_config import (
    FacebookPageConfig,
)
from socialflow.modules.facebook.adapters.facebook_publisher import (
    FacebookPublisher,
)
from socialflow.modules.facebook.api.facebook_graph_client import (
    FacebookGraphClient,
)
from socialflow.modules.facebook.api.facebook_http_transport import (
    FacebookHttpResponse,
    FacebookHttpTransport,
)
from socialflow.modules.facebook.api.facebook_publishing_service import (
    FacebookPublishingService,
)
from socialflow.modules.posts.models.image_attachment import (
    ImageAttachment,
)
from socialflow.modules.posts.models.language import Language
from socialflow.modules.posts.models.post import Post
from socialflow.modules.posts.models.publish_request import PublishRequest
from socialflow.modules.posts.models.publication_id import PublicationId
from socialflow.modules.posts.services.default_image_profiles import (
    DEFAULT_IMAGE_PROFILES,
)
from socialflow.modules.posts.services.image_preparation_service import (
    ImagePreparationService,
)
from socialflow.modules.posts.services.image_profile_provider import (
    ImageProfileProvider,
)
from socialflow.modules.posts.services.publication_id_generator import (
    PublicationIdGenerator,
)
from socialflow.modules.posts.services.publish_post import PublishPost
from socialflow.modules.posts.services.publisher_router import (
    PublisherRouter,
)


class RecordingTransport(FacebookHttpTransport):
    """Record HTTP requests without contacting Facebook."""

    def __init__(self) -> None:
        self.requests: list[
            tuple[str, dict[str, str], bytes]
        ] = []

    def get(
        self,
        url: str,
        headers: Mapping[str, str],
        timeout: float,
    ) -> FacebookHttpResponse:
        raise AssertionError("Unexpected HTTP GET request.")

    def post(
        self,
        url: str,
        headers: Mapping[str, str],
        body: bytes,
        timeout: float,
    ) -> FacebookHttpResponse:
        self.requests.append(
            (url, dict(headers), body)
        )
        return FacebookHttpResponse(
            status_code=200,
            body=b'{"id":"123456789_987654321"}',
        )


class FixedIdGenerator(PublicationIdGenerator):
    """Provide a deterministic publication identifier."""

    def generate(self) -> PublicationId:
        return PublicationId(
            UUID("12345678-1234-5678-1234-567812345678")
        )


def test_facebook_photo_pipeline_prepares_publishes_and_cleans_up(
    tmp_path: Path,
) -> None:
    # Create a real image with a filename containing spaces.
    source_path = tmp_path / "summer holiday.png"

    Image.new(
        "RGB",
        (2400, 1600),
        color=(100, 150, 200),
    ).save(source_path, format="PNG")

    attachment = ImageAttachment(path=source_path)

    account = Account(
        name="Test Facebook Page",
        destination=PublishingDestination.FACEBOOK,
        facebook_config=FacebookPageConfig(
            page_id="123456789",
            page_name="Test Facebook Page",
        ),
    )

    credentials = Mock()
    credentials.get.return_value = "test-page-token"

    transport = RecordingTransport()

    graph_client = FacebookGraphClient(
        api_version="v24.0",
        transport=transport,
    )

    publishing_service = FacebookPublishingService(
        client=graph_client,
    )

    facebook_publisher = FacebookPublisher(
        account=account,
        credential_store=credentials,
        publishing_service=publishing_service,
    )

    router = PublisherRouter(
        publishers={
            PublishingDestination.FACEBOOK: facebook_publisher,
        }
    )

    image_preparation = ImagePreparationService(
        profile_provider=ImageProfileProvider(
            profiles=DEFAULT_IMAGE_PROFILES,
        )
    )

    output_directory = tmp_path / "prepared"

    publish_post = PublishPost(
        publisher_router=router,
        publication_id_generator=FixedIdGenerator(),
        image_preparation_service=image_preparation,
        image_output_directory=output_directory,
    )

    post = Post(
        text="My Facebook photo caption",
        language=Language.ENGLISH,
        images=(attachment,),
    )

    results = publish_post.execute(
        PublishRequest(
            post=post,
            accounts=(account,),
        )
    )

    # The publishing workflow reports success.
    assert len(results) == 1
    assert results[0].succeeded is True
    assert results[0].error is None

    # Exactly one HTTP request was made.
    assert len(transport.requests) == 1

    url, headers, body = transport.requests[0]

    assert url == (
        "https://graph.facebook.com/"
        "v24.0/123456789/photos"
    )
    assert headers["Authorization"] == (
        "Bearer test-page-token"
    )
    assert headers["Content-Type"].startswith(
        "multipart/form-data;"
    )

    # The caption and safe upload filename are present.
    assert b"My Facebook photo caption" in body
    assert b"facebook-photo.jpg" in body

    # Verify that the uploaded image was prepared as JPEG.
    # The original source is PNG and must remain unchanged.
    assert source_path.is_file()

    with Image.open(source_path) as original:
        assert original.format == "PNG"
        assert original.size == (2400, 1600)

    # Temporary prepared image files must be removed.
    prepared_files = list(output_directory.rglob("*.jpg"))
    assert prepared_files == []
