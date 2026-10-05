import pytest

from pathlib import Path

from PIL import Image

from socialflow.application.images.image_preparation_service import (
    ImagePreparationService,
)
from socialflow.application.images.image_processor import ImageDimensions
from socialflow.application.images.image_profile import ImageProfile
from socialflow.application.images.image_profile_provider import (
    ImageProfileProvider,
)
from socialflow.domain.post.image_attachment import ImageAttachment
from socialflow.application.publishing.errors import (
    EmptyPostError,
    ImagePreparationNotConfiguredError,
)
from socialflow.application.publishing.prepared_post import PreparedPost
from socialflow.application.publishing.publish_post import PublishPost
from socialflow.application.publishing.publisher import Publisher
from socialflow.application.publishing.publisher_router import PublisherRouter
from socialflow.domain.account.account import Account
from socialflow.domain.language.language import Language
from socialflow.domain.post.post import Post
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.domain.publishing.publish_request import PublishRequest


class RecordingPublisher(Publisher):
    """Test publisher that records published posts."""

    def __init__(self) -> None:
        self.published_posts: list[PreparedPost] = []

    def publish(self, post: PreparedPost) -> None:
        self.published_posts.append(post)


def test_publish_post_publishes_to_requested_accounts() -> None:
    facebook_publisher = RecordingPublisher()
    wordpress_publisher = RecordingPublisher()

    router = PublisherRouter(
        {
            PublishingDestination.FACEBOOK: facebook_publisher,
            PublishingDestination.WORDPRESS: wordpress_publisher,
        }
    )
    service = PublishPost(router)

    post = Post(
        text="Hello from SocialFlow",
        language=Language.ENGLISH,
    )
    facebook_account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )
    wordpress_account = Account(
        name="Main Website",
        destination=PublishingDestination.WORDPRESS,
    )

    request = PublishRequest(
        post=post,
        accounts=(
            facebook_account,
            wordpress_account,
        ),
    )

    service.execute(request)

    assert len(facebook_publisher.published_posts) == 1
    assert facebook_publisher.published_posts[0].source is post
    assert facebook_publisher.published_posts[0].images == ()

    assert len(wordpress_publisher.published_posts) == 1
    assert wordpress_publisher.published_posts[0].source is post
    assert wordpress_publisher.published_posts[0].images == ()


def test_publish_post_rejects_empty_post() -> None:
    publisher = RecordingPublisher()
    router = PublisherRouter(
        {
            PublishingDestination.FACEBOOK: publisher,
        }
    )
    service = PublishPost(router)

    post = Post(
        text="   ",
        language=Language.CROATIAN,
    )
    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    request = PublishRequest(
        post=post,
        accounts=(account,),
    )

    with pytest.raises(
        EmptyPostError,
        match="Cannot publish a post without content.",
    ):
        service.execute(request)

    assert publisher.published_posts == []

def test_publish_post_prepares_images_for_destination(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "source.png"

    image = Image.new(
        "RGB",
        (1600, 900),
    )
    image.save(source_path)

    attachment = ImageAttachment(
        path=source_path,
    )

    publisher = RecordingPublisher()

    router = PublisherRouter(
        {
            PublishingDestination.INSTAGRAM: publisher,
        }
    )

    profile_provider = ImageProfileProvider(
        profiles={
            PublishingDestination.INSTAGRAM: ImageProfile(
                maximum_dimensions=ImageDimensions(
                    width=800,
                    height=800,
                ),
                output_format="JPEG",
            ),
        }
    )

    service = PublishPost(
        publisher_router=router,
        image_preparation_service=ImagePreparationService(
            profile_provider=profile_provider,
        ),
        image_output_directory=tmp_path / "prepared",
    )

    post = Post(
        text="Post with image",
        language=Language.ENGLISH,
        images=(attachment,),
    )

    account = Account(
        name="Main Instagram",
        destination=PublishingDestination.INSTAGRAM,
    )

    request = PublishRequest(
        post=post,
        accounts=(account,),
    )

    service.execute(request)

    assert len(publisher.published_posts) == 1

    prepared_post = publisher.published_posts[0]

    assert prepared_post.source is post
    assert len(prepared_post.images) == 1

    prepared_image = prepared_post.images[0]

    assert prepared_image.source is attachment
    assert (
        prepared_image.destination
        == PublishingDestination.INSTAGRAM
    )

    assert prepared_image.path == (
        tmp_path
        / "prepared"
        / "instagram"
        / "source-instagram-1.jpg"
    )

    assert prepared_image.path.is_file()

    with Image.open(prepared_image.path) as result:
        assert result.size == (800, 450)
        assert result.format == "JPEG"

    with Image.open(source_path) as original:
        assert original.size == (1600, 900)
        assert original.format == "PNG"

def test_publish_post_prepares_image_separately_for_each_destination(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "source.png"

    image = Image.new(
        "RGB",
        (1600, 900),
    )
    image.save(source_path)

    attachment = ImageAttachment(
        path=source_path,
    )

    facebook_publisher = RecordingPublisher()
    instagram_publisher = RecordingPublisher()

    router = PublisherRouter(
        {
            PublishingDestination.FACEBOOK: facebook_publisher,
            PublishingDestination.INSTAGRAM: instagram_publisher,
        }
    )

    profile_provider = ImageProfileProvider(
        profiles={
            PublishingDestination.FACEBOOK: ImageProfile(
                maximum_dimensions=ImageDimensions(
                    width=1200,
                    height=1200,
                ),
                output_format="JPEG",
            ),
            PublishingDestination.INSTAGRAM: ImageProfile(
                maximum_dimensions=ImageDimensions(
                    width=800,
                    height=800,
                ),
                output_format="JPEG",
            ),
        }
    )

    service = PublishPost(
        publisher_router=router,
        image_preparation_service=ImagePreparationService(
            profile_provider=profile_provider,
        ),
        image_output_directory=tmp_path / "prepared",
    )

    post = Post(
        text="Post for multiple destinations",
        language=Language.ENGLISH,
        images=(attachment,),
    )

    request = PublishRequest(
        post=post,
        accounts=(
            Account(
                name="Main Facebook",
                destination=PublishingDestination.FACEBOOK,
            ),
            Account(
                name="Main Instagram",
                destination=PublishingDestination.INSTAGRAM,
            ),
        ),
    )

    service.execute(request)

    assert len(facebook_publisher.published_posts) == 1
    assert len(instagram_publisher.published_posts) == 1

    facebook_post = facebook_publisher.published_posts[0]
    instagram_post = instagram_publisher.published_posts[0]

    assert facebook_post.source is post
    assert instagram_post.source is post

    assert len(facebook_post.images) == 1
    assert len(instagram_post.images) == 1

    facebook_image = facebook_post.images[0]
    instagram_image = instagram_post.images[0]

    assert facebook_image.destination == PublishingDestination.FACEBOOK
    assert instagram_image.destination == PublishingDestination.INSTAGRAM

    assert facebook_image.path == (
        tmp_path
        / "prepared"
        / "facebook"
        / "source-facebook-1.jpg"
    )

    assert instagram_image.path == (
        tmp_path
        / "prepared"
        / "instagram"
        / "source-instagram-1.jpg"
    )

    with Image.open(facebook_image.path) as result:
        assert result.size == (1200, 675)
        assert result.format == "JPEG"

    with Image.open(instagram_image.path) as result:
        assert result.size == (800, 450)
        assert result.format == "JPEG"

    with Image.open(source_path) as original:
        assert original.size == (1600, 900)
        assert original.format == "PNG"

def test_publish_post_rejects_images_without_preparation_configuration(
    tmp_path: Path,
) -> None:
    image_path = tmp_path / "source.jpg"

    image = Image.new(
        "RGB",
        (800, 600),
    )
    image.save(image_path)

    attachment = ImageAttachment(
        path=image_path,
    )

    publisher = RecordingPublisher()

    router = PublisherRouter(
        {
            PublishingDestination.FACEBOOK: publisher,
        }
    )

    service = PublishPost(
        publisher_router=router,
    )

    post = Post(
        text="Post with image",
        language=Language.ENGLISH,
        images=(attachment,),
    )

    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    request = PublishRequest(
        post=post,
        accounts=(account,),
    )

    with pytest.raises(
        ImagePreparationNotConfiguredError,
        match=(
            "Image preparation must be configured "
            "before publishing images."
        ),
    ):
        service.execute(request)

    assert publisher.published_posts == []