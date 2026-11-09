from types import SimpleNamespace
from unittest.mock import Mock
import pytest

from socialflow.core.destination import PublishingDestination
from socialflow.modules.accounts.services.facebook_credential_keys import (
    FacebookCredentialKeys,
)
from socialflow.modules.facebook.adapters.facebook_publisher import (
    FacebookPublisher,
)
from socialflow.modules.posts.models.language import Language
from socialflow.modules.posts.models.post import Post
from socialflow.modules.posts.services.prepared_post import PreparedPost
from socialflow.modules.posts.services.errors import (
    PublisherNotConfiguredError,
)
from pathlib import Path

from socialflow.modules.posts.models.image_attachment import (
    ImageAttachment,
)
from socialflow.modules.posts.services.prepared_image import (
    PreparedImage,
)


def make_account():
    config = Mock()
    config.is_complete.return_value = True
    config.normalized.return_value = SimpleNamespace(
        page_id="123456789",
        page_name="Test Facebook Page",
    )

    return SimpleNamespace(
        id="test-facebook-account",
        destination=PublishingDestination.FACEBOOK,
        facebook_config=config,
    )


def make_post(text: str = "Hello Facebook!") -> PreparedPost:
    return PreparedPost(
        source=Post(
            text=text,
            language=Language.ENGLISH,
        )
    )


def make_publisher(
    account=None,
    token: str | None = "page-secret-token",
):
    account = account if account is not None else make_account()

    credentials = Mock()
    credentials.get.return_value = token

    publishing_service = Mock()

    publisher = FacebookPublisher(
        account=account,
        credential_store=credentials,
        publishing_service=publishing_service,
    )

    return publisher, credentials, publishing_service


def test_successful_facebook_publication() -> None:
    publisher, credentials, service = make_publisher()

    publisher.publish(make_post())

    credentials.get.assert_called_once_with(
        FacebookCredentialKeys.page_access_token(
            publisher._account
        )
    )

    service.publish_text.assert_called_once_with(
        page_id="123456789",
        access_token="page-secret-token",
        message="Hello Facebook!",
    )

def test_rejects_missing_facebook_configuration() -> None:
    account = make_account()
    account.facebook_config = None

    publisher, credentials, service = make_publisher(
        account=account,
    )

    with pytest.raises(
            PublisherNotConfiguredError,
            match="Facebook Page connection settings are incomplete",
    ):
        publisher.publish(make_post())

    credentials.get.assert_not_called()
    service.publish_text.assert_not_called()


def test_rejects_incomplete_facebook_configuration() -> None:
    account = make_account()
    account.facebook_config.is_complete.return_value = False

    publisher, credentials, service = make_publisher(
        account=account,
    )

    with pytest.raises(
            PublisherNotConfiguredError,
            match="Facebook Page connection settings are incomplete",
    ):
        publisher.publish(make_post())

    credentials.get.assert_not_called()
    service.publish_text.assert_not_called()


@pytest.mark.parametrize("token", [None, "", "   "])
def test_rejects_missing_facebook_access_token(token) -> None:
    publisher, credentials, service = make_publisher(
        token=token,
    )

    with pytest.raises(
        ValueError,
        match="Facebook Page access token is missing",
    ):
        publisher.publish(make_post())

    credentials.get.assert_called_once()
    service.publish_text.assert_not_called()


def make_image_attachment(tmp_path: Path) -> ImageAttachment:
    path = tmp_path / "photo.jpg"
    path.write_bytes(b"\xff\xd8test-image")
    return ImageAttachment(path=path)


def test_publishes_single_source_image(tmp_path: Path) -> None:
    publisher, credentials, service = make_publisher()
    attachment = make_image_attachment(tmp_path)

    post = PreparedPost(
        source=Post(
            text="Photo caption",
            language=Language.ENGLISH,
            images=(attachment,),
        )
    )

    publisher.publish(post)

    service.publish_photo.assert_called_once_with(
        page_id="123456789",
        access_token="page-secret-token",
        attachment=attachment,
        caption="Photo caption",
    )
    service.publish_text.assert_not_called()


def test_publishes_photo_without_caption(tmp_path: Path) -> None:
    publisher, credentials, service = make_publisher()
    attachment = make_image_attachment(tmp_path)

    post = PreparedPost(
        source=Post(
            text="",
            language=Language.ENGLISH,
            images=(attachment,),
        )
    )

    publisher.publish(post)

    assert service.publish_photo.call_args.kwargs["caption"] == ""
    service.publish_text.assert_not_called()


def test_publishes_prepared_facebook_image(tmp_path: Path) -> None:
    publisher, credentials, service = make_publisher()
    attachment = make_image_attachment(tmp_path)

    prepared = PreparedImage(
        source=attachment,
        destination=PublishingDestination.FACEBOOK,
        path=attachment.path,
    )

    post = PreparedPost(
        source=Post(
            text="Prepared photo",
            language=Language.ENGLISH,
            images=(attachment,),
        ),
        images=(prepared,),
    )

    publisher.publish(post)

    service.publish_photo.assert_called_once()
    assert (
        service.publish_photo.call_args.kwargs["attachment"].path
        == attachment.path
    )



def test_publishes_multiple_source_images(tmp_path: Path) -> None:
    publisher, credentials, service = make_publisher()
    first = make_image_attachment(tmp_path)

    second_path = tmp_path / "second.png"
    second_path.write_bytes(b"image-data")
    second = ImageAttachment(path=second_path)

    post = PreparedPost(
        source=Post(
            text="Two photos",
            language=Language.ENGLISH,
            images=(first, second),
        )
    )

    publisher.publish(post)

    credentials.get.assert_called_once_with(
        FacebookCredentialKeys.page_access_token(
            publisher._account
        )
    )

    service.publish_multiple_photos.assert_called_once_with(
        page_id="123456789",
        access_token="page-secret-token",
        attachments=(first, second),
        message="Two photos",
    )

    service.publish_photo.assert_not_called()
    service.publish_text.assert_not_called()


def test_rejects_prepared_image_for_other_destination(
    tmp_path: Path,
) -> None:
    publisher, credentials, service = make_publisher()
    attachment = make_image_attachment(tmp_path)

    prepared = PreparedImage(
        source=attachment,
        destination=PublishingDestination.WORDPRESS,
        path=attachment.path,
    )

    post = PreparedPost(
        source=Post(
            text="Photo",
            language=Language.ENGLISH,
            images=(attachment,),
        ),
        images=(prepared,),
    )

    with pytest.raises(ValueError, match="not intended for Facebook"):
        publisher.publish(post)

    credentials.get.assert_not_called()
    service.publish_photo.assert_not_called()


def test_photo_publishing_error_propagates(tmp_path: Path) -> None:
    publisher, credentials, service = make_publisher()
    attachment = make_image_attachment(tmp_path)

    service.publish_photo.side_effect = RuntimeError(
        "Photo publishing failed."
    )

    post = PreparedPost(
        source=Post(
            text="Photo caption",
            language=Language.ENGLISH,
            images=(attachment,),
        )
    )

    with pytest.raises(RuntimeError, match="Photo publishing failed"):
        publisher.publish(post)

    service.publish_photo.assert_called_once()



def test_rejects_facebook_tags() -> None:
    publisher, credentials, service = make_publisher()

    post = PreparedPost(
        source=Post(
            text="Hello Facebook!",
            language=Language.ENGLISH,
            tags=(Mock(),),
        )
    )

    with pytest.raises(
        ValueError,
        match="Facebook tag publishing is not supported yet",
    ):
        publisher.publish(post)

    credentials.get.assert_not_called()
    service.publish_text.assert_not_called()

@pytest.mark.parametrize("text", ["", " ", "   \t\n"])
def test_rejects_empty_facebook_post_text(text: str) -> None:
    publisher, credentials, service = make_publisher()

    with pytest.raises(
        ValueError,
        match="Facebook post text is required",
    ):
        publisher.publish(make_post(text=text))

    credentials.get.assert_not_called()
    service.publish_text.assert_not_called()


def test_propagates_facebook_publishing_error() -> None:
    publisher, credentials, service = make_publisher()

    service.publish_text.side_effect = RuntimeError(
        "Facebook publishing failed."
    )

    with pytest.raises(
        RuntimeError,
        match="Facebook publishing failed",
    ):
        publisher.publish(make_post())

    credentials.get.assert_called_once()
    service.publish_text.assert_called_once_with(
        page_id="123456789",
        access_token="page-secret-token",
        message="Hello Facebook!",
    )

def test_rejects_non_facebook_account() -> None:
    account = make_account()
    account.destination = PublishingDestination.WORDPRESS

    with pytest.raises(
        ValueError,
        match="A Facebook account is required",
    ):
        make_publisher(account=account)


def test_publishes_multiple_prepared_facebook_images(
    tmp_path: Path,
) -> None:
    publisher, credentials, service = make_publisher()

    first = make_image_attachment(tmp_path)
    second_path = tmp_path / "second.jpg"
    second_path.write_bytes(b"source-image")
    second = ImageAttachment(path=second_path)

    prepared_first_path = tmp_path / "prepared-first.jpg"
    prepared_second_path = tmp_path / "prepared-second.jpg"

    prepared_first_path.write_bytes(b"prepared-first-image")
    prepared_second_path.write_bytes(b"prepared-second-image")

    prepared_first = PreparedImage(
        source=first,
        destination=PublishingDestination.FACEBOOK,
        path=prepared_first_path,
    )
    prepared_second = PreparedImage(
        source=second,
        destination=PublishingDestination.FACEBOOK,
        path=prepared_second_path,
    )

    post = PreparedPost(
        source=Post(
            text="Prepared album",
            language=Language.ENGLISH,
            images=(first, second),
        ),
        images=(prepared_first, prepared_second),
    )

    publisher.publish(post)

    service.publish_multiple_photos.assert_called_once_with(
        page_id="123456789",
        access_token="page-secret-token",
        attachments=(
            ImageAttachment(path=prepared_first_path),
            ImageAttachment(path=prepared_second_path),
        ),
        message="Prepared album",
    )
    service.publish_photo.assert_not_called()
    service.publish_text.assert_not_called()
    credentials.get.assert_called_once()


def test_rejects_mismatched_prepared_image_count(
    tmp_path: Path,
) -> None:
    publisher, credentials, service = make_publisher()

    first = make_image_attachment(tmp_path)

    second_path = tmp_path / "second.jpg"
    second_path.write_bytes(b"source-second-image")
    second = ImageAttachment(path=second_path)

    prepared = PreparedImage(
        source=first,
        destination=PublishingDestination.FACEBOOK,
        path=first.path,
    )

    post = PreparedPost(
        source=Post(
            text="Album",
            language=Language.ENGLISH,
            images=(first, second),
        ),
        images=(prepared,),
    )

    with pytest.raises(ValueError, match="count does not match"):
        publisher.publish(post)

    credentials.get.assert_not_called()
    service.publish_multiple_photos.assert_not_called()


def test_rejects_prepared_images_in_wrong_order(
    tmp_path: Path,
) -> None:
    publisher, credentials, service = make_publisher()

    first = make_image_attachment(tmp_path)

    second_path = tmp_path / "second.jpg"
    second_path.write_bytes(b"source-second-image")
    second = ImageAttachment(path=second_path)

    prepared_first = PreparedImage(
        source=second,
        destination=PublishingDestination.FACEBOOK,
        path=second.path,
    )
    prepared_second = PreparedImage(
        source=first,
        destination=PublishingDestination.FACEBOOK,
        path=first.path,
    )

    post = PreparedPost(
        source=Post(
            text="Album",
            language=Language.ENGLISH,
            images=(first, second),
        ),
        images=(prepared_first, prepared_second),
    )

    with pytest.raises(ValueError, match="inconsistent"):
        publisher.publish(post)

    credentials.get.assert_not_called()
    service.publish_multiple_photos.assert_not_called()


def test_rejects_missing_prepared_image_before_credentials(
    tmp_path: Path,
) -> None:
    publisher, credentials, service = make_publisher()
    source = make_image_attachment(tmp_path)

    missing_path = tmp_path / "missing-prepared.jpg"

    prepared = PreparedImage(
        source=source,
        destination=PublishingDestination.FACEBOOK,
        path=missing_path,
    )

    post = PreparedPost(
        source=Post(
            text="Missing prepared image",
            language=Language.ENGLISH,
            images=(source,),
        ),
        images=(prepared,),
    )

    with pytest.raises(ValueError, match="Image file does not exist"):
        publisher.publish(post)

    credentials.get.assert_not_called()
    service.publish_photo.assert_not_called()
    service.publish_multiple_photos.assert_not_called()
    service.publish_text.assert_not_called()


def test_rejects_wrong_destination_in_multiple_prepared_images(
    tmp_path: Path,
) -> None:
    publisher, credentials, service = make_publisher()

    first = make_image_attachment(tmp_path)

    second_path = tmp_path / "second.jpg"
    second_path.write_bytes(b"second-image")
    second = ImageAttachment(path=second_path)

    prepared_first = PreparedImage(
        source=first,
        destination=PublishingDestination.FACEBOOK,
        path=first.path,
    )
    prepared_second = PreparedImage(
        source=second,
        destination=PublishingDestination.WORDPRESS,
        path=second.path,
    )

    post = PreparedPost(
        source=Post(
            text="Mixed destinations",
            language=Language.ENGLISH,
            images=(first, second),
        ),
        images=(prepared_first, prepared_second),
    )

    with pytest.raises(ValueError, match="not intended for Facebook"):
        publisher.publish(post)

    credentials.get.assert_not_called()
    service.publish_photo.assert_not_called()
    service.publish_multiple_photos.assert_not_called()
    service.publish_text.assert_not_called()


def test_rejects_missing_second_prepared_image_without_publishing(
    tmp_path: Path,
) -> None:
    publisher, credentials, service = make_publisher()

    first = make_image_attachment(tmp_path)

    second_path = tmp_path / "second.jpg"
    second_path.write_bytes(b"second-source")
    second = ImageAttachment(path=second_path)

    prepared_first = PreparedImage(
        source=first,
        destination=PublishingDestination.FACEBOOK,
        path=first.path,
    )
    prepared_second = PreparedImage(
        source=second,
        destination=PublishingDestination.FACEBOOK,
        path=tmp_path / "missing-second-prepared.jpg",
    )

    post = PreparedPost(
        source=Post(
            text="Two prepared images",
            language=Language.ENGLISH,
            images=(first, second),
        ),
        images=(prepared_first, prepared_second),
    )

    with pytest.raises(ValueError, match="Image file does not exist"):
        publisher.publish(post)

    credentials.get.assert_not_called()
    service.publish_photo.assert_not_called()
    service.publish_multiple_photos.assert_not_called()
    service.publish_text.assert_not_called()


@pytest.mark.parametrize("image_count", [2, 10])
def test_publishes_album_at_supported_boundaries(
    tmp_path: Path,
    image_count: int,
) -> None:
    publisher, credentials, service = make_publisher()

    attachments = []

    for index in range(image_count):
        path = tmp_path / f"photo-{index}.jpg"
        path.write_bytes(b"test-image")
        attachments.append(ImageAttachment(path=path))

    post = PreparedPost(
        source=Post(
            text="Album boundary",
            language=Language.ENGLISH,
            images=tuple(attachments),
        )
    )

    publisher.publish(post)

    service.publish_multiple_photos.assert_called_once_with(
        page_id="123456789",
        access_token="page-secret-token",
        attachments=tuple(attachments),
        message="Album boundary",
    )

    credentials.get.assert_called_once()
    service.publish_photo.assert_not_called()
    service.publish_text.assert_not_called()


@pytest.mark.parametrize("image_count", [11, 12])
def test_rejects_oversized_album_without_publishing(
    tmp_path: Path,
    image_count: int,
) -> None:
    publisher, credentials, service = make_publisher()

    attachments = []

    for index in range(image_count):
        path = tmp_path / f"photo-{index}.jpg"
        path.write_bytes(b"test-image")
        attachments.append(ImageAttachment(path=path))

    post = PreparedPost(
        source=Post(
            text="Oversized album",
            language=Language.ENGLISH,
            images=tuple(attachments),
        )
    )

    with pytest.raises(ValueError, match="2 to 10"):
        publisher.publish(post)

    credentials.get.assert_not_called()
    service.publish_multiple_photos.assert_not_called()
    service.publish_photo.assert_not_called()
    service.publish_text.assert_not_called()


def test_multiple_photo_publishing_error_propagates(
    tmp_path: Path,
) -> None:
    publisher, credentials, service = make_publisher()

    first_path = tmp_path / "first.jpg"
    second_path = tmp_path / "second.jpg"

    first_path.write_bytes(b"first-image")
    second_path.write_bytes(b"second-image")

    first = ImageAttachment(path=first_path)
    second = ImageAttachment(path=second_path)

    service.publish_multiple_photos.side_effect = RuntimeError(
        "Album publishing failed."
    )

    post = PreparedPost(
        source=Post(
            text="Failed album",
            language=Language.ENGLISH,
            images=(first, second),
        )
    )

    with pytest.raises(
        RuntimeError,
        match="Album publishing failed",
    ):
        publisher.publish(post)

    credentials.get.assert_called_once()
    service.publish_multiple_photos.assert_called_once_with(
        page_id="123456789",
        access_token="page-secret-token",
        attachments=(first, second),
        message="Failed album",
    )
    service.publish_photo.assert_not_called()
    service.publish_text.assert_not_called()
