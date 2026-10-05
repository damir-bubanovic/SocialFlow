import pytest

from pathlib import Path

from PIL import Image

from datetime import datetime

from socialflow.application.time.clock import Clock
from socialflow.infrastructure.publishing.in_memory_publication_repository import (
    InMemoryPublicationRepository,
)

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

class FailingPublisher(Publisher):
    """Test publisher that fails while publishing."""

    def publish(self, post: PreparedPost) -> None:
        raise RuntimeError("Publishing failed.")

class InspectingPublisher(Publisher):
    """Test publisher that inspects prepared images while publishing."""

    def __init__(self) -> None:
        self.image_existed_during_publish = False
        self.image_size: tuple[int, int] | None = None
        self.image_format: str | None = None

    def publish(self, post: PreparedPost) -> None:
        prepared_image = post.images[0]

        self.image_existed_during_publish = (
            prepared_image.path.is_file()
        )

        with Image.open(prepared_image.path) as image:
            self.image_size = image.size
            self.image_format = image.format

class FixedClock(Clock):
    """Test clock returning a fixed date and time."""

    def __init__(self, current: datetime) -> None:
        self._current = current

    def now(self) -> datetime:
        return self._current

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

    assert not prepared_image.path.exists()

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

    assert not facebook_image.path.exists()
    assert not instagram_image.path.exists()

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

def test_publish_post_cleans_prepared_images_when_publisher_fails(
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

    router = PublisherRouter(
        {
            PublishingDestination.INSTAGRAM: FailingPublisher(),
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

    request = PublishRequest(
        post=post,
        accounts=(
            Account(
                name="Main Instagram",
                destination=PublishingDestination.INSTAGRAM,
            ),
        ),
    )

    prepared_path = (
        tmp_path
        / "prepared"
        / "instagram"
        / "source-instagram-1.jpg"
    )

    results = service.execute(request)

    assert len(results) == 1
    assert results[0].account is request.accounts[0]
    assert not results[0].succeeded
    assert isinstance(results[0].error, RuntimeError)
    assert str(results[0].error) == "Publishing failed."

    assert not prepared_path.exists()
    assert source_path.exists()

def test_prepared_image_exists_during_publish_and_is_cleaned_afterward(
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

    publisher = InspectingPublisher()

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

    request = PublishRequest(
        post=post,
        accounts=(
            Account(
                name="Main Instagram",
                destination=PublishingDestination.INSTAGRAM,
            ),
        ),
    )

    prepared_path = (
        tmp_path
        / "prepared"
        / "instagram"
        / "source-instagram-1.jpg"
    )

    service.execute(request)

    assert publisher.image_existed_during_publish
    assert publisher.image_size == (800, 450)
    assert publisher.image_format == "JPEG"

    assert not prepared_path.exists()
    assert source_path.exists()

def test_publish_post_continues_after_one_destination_fails() -> None:
    failing_publisher = FailingPublisher()
    successful_publisher = RecordingPublisher()

    router = PublisherRouter(
        {
            PublishingDestination.FACEBOOK: failing_publisher,
            PublishingDestination.WORDPRESS: successful_publisher,
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

    results = service.execute(request)

    assert len(results) == 2

    assert results[0].account is facebook_account
    assert not results[0].succeeded
    assert isinstance(results[0].error, RuntimeError)

    assert results[1].account is wordpress_account
    assert results[1].succeeded
    assert results[1].error is None

    assert len(successful_publisher.published_posts) == 1
    assert successful_publisher.published_posts[0].source is post

def test_publish_post_records_successful_publication() -> None:
    publisher = RecordingPublisher()

    router = PublisherRouter(
        {
            PublishingDestination.FACEBOOK: publisher,
        }
    )

    repository = InMemoryPublicationRepository()
    published_at = datetime(2026, 10, 5, 21, 0)

    service = PublishPost(
        publisher_router=router,
        publication_repository=repository,
        clock=FixedClock(published_at),
    )

    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    post = Post(
        text="Hello from SocialFlow",
        language=Language.ENGLISH,
    )

    request = PublishRequest(
        post=post,
        accounts=(account,),
    )

    service.execute(request)

    publications = repository.recent_for_account(account)

    assert len(publications) == 1
    assert publications[0].account is account
    assert publications[0].post is post
    assert publications[0].published_at == published_at

def test_publish_post_does_not_record_failed_publication() -> None:
    publisher = FailingPublisher()

    router = PublisherRouter(
        {
            PublishingDestination.FACEBOOK: publisher,
        }
    )

    repository = InMemoryPublicationRepository()
    published_at = datetime(2026, 10, 5, 21, 0)

    service = PublishPost(
        publisher_router=router,
        publication_repository=repository,
        clock=FixedClock(published_at),
    )

    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    post = Post(
        text="Hello from SocialFlow",
        language=Language.ENGLISH,
    )

    request = PublishRequest(
        post=post,
        accounts=(account,),
    )

    results = service.execute(request)

    assert len(results) == 1
    assert not results[0].succeeded
    assert repository.recent_for_account(account) == ()

def test_publish_post_records_only_successful_destinations() -> None:
    facebook_publisher = FailingPublisher()
    wordpress_publisher = RecordingPublisher()

    router = PublisherRouter(
        {
            PublishingDestination.FACEBOOK: facebook_publisher,
            PublishingDestination.WORDPRESS: wordpress_publisher,
        }
    )

    repository = InMemoryPublicationRepository()
    published_at = datetime(2026, 10, 5, 21, 0)

    service = PublishPost(
        publisher_router=router,
        publication_repository=repository,
        clock=FixedClock(published_at),
    )

    facebook_account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )
    wordpress_account = Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    post = Post(
        text="Hello from SocialFlow",
        language=Language.ENGLISH,
    )

    request = PublishRequest(
        post=post,
        accounts=(
            facebook_account,
            wordpress_account,
        ),
    )

    results = service.execute(request)

    assert len(results) == 2

    assert not results[0].succeeded
    assert results[1].succeeded

    assert repository.recent_for_account(
        facebook_account
    ) == ()

    wordpress_publications = repository.recent_for_account(
        wordpress_account
    )

    assert len(wordpress_publications) == 1
    assert wordpress_publications[0].account is wordpress_account
    assert wordpress_publications[0].post is post
    assert wordpress_publications[0].published_at == published_at