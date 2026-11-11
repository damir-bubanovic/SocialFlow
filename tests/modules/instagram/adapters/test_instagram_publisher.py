from unittest.mock import Mock

import pytest
from pathlib import Path

from socialflow.core.destination import PublishingDestination
from socialflow.modules.accounts.models.account import Account
from socialflow.modules.accounts.models.instagram_account_config import (
    InstagramAccountConfig,
)
from socialflow.modules.accounts.services.instagram_credential_keys import (
    InstagramCredentialKeys,
)
from socialflow.modules.posts.services.errors import (
    PublisherNotConfiguredError,
)
from socialflow.modules.instagram.adapters.instagram_publisher import (
    InstagramPublisher,
)


def make_instagram_account() -> Account:
    return Account(
        name="Test Instagram",
        destination=PublishingDestination.INSTAGRAM,
        instagram_config=InstagramAccountConfig(
            instagram_user_id="17841400000000000",
            username="test_account",
        ),
    )


def test_instagram_publisher_accepts_instagram_account() -> None:
    account = make_instagram_account()
    credentials = Mock()
    publishing_service = Mock()

    publisher = InstagramPublisher(
        account=account,
        credential_store=credentials,
        publishing_service=publishing_service,
    )

    assert publisher._account is account
    assert publisher._credential_store is credentials
    assert publisher._publishing_service is publishing_service


@pytest.mark.parametrize(
    "destination",
    [
        PublishingDestination.FACEBOOK,
        PublishingDestination.WORDPRESS,
    ],
)
def test_instagram_publisher_rejects_other_destinations(
    destination: PublishingDestination,
) -> None:
    account = Account(
        name="Wrong destination",
        destination=destination,
    )

    credentials = Mock()
    publishing_service = Mock()

    with pytest.raises(
        ValueError,
        match="Instagram account is required",
    ):
        InstagramPublisher(
            account=account,
            credential_store=credentials,
            publishing_service=publishing_service,
        )

    credentials.get.assert_not_called()
    publishing_service.publish_image.assert_not_called()


def test_instagram_publisher_rejects_missing_configuration() -> None:
    account = Account(
        name="Instagram without configuration",
        destination=PublishingDestination.INSTAGRAM,
    )
    credentials = Mock()
    publishing_service = Mock()

    publisher = InstagramPublisher(
        account=account,
        credential_store=credentials,
        publishing_service=publishing_service,
    )

    with pytest.raises(
        PublisherNotConfiguredError,
        match="Instagram",
    ):
        publisher.publish(Mock())

    credentials.get.assert_not_called()
    publishing_service.publish_image.assert_not_called()


@pytest.mark.parametrize(
    "instagram_user_id",
    ["", " ", "\t\n"],
)
def test_instagram_publisher_rejects_incomplete_configuration(
    instagram_user_id: str,
) -> None:
    account = Account(
        name="Incomplete Instagram",
        destination=PublishingDestination.INSTAGRAM,
        instagram_config=InstagramAccountConfig(
            instagram_user_id=instagram_user_id,
            username="test_account",
        ),
    )
    credentials = Mock()
    publishing_service = Mock()

    publisher = InstagramPublisher(
        account=account,
        credential_store=credentials,
        publishing_service=publishing_service,
    )

    with pytest.raises(
        PublisherNotConfiguredError,
        match="Instagram",
    ):
        publisher.publish(Mock())

    credentials.get.assert_not_called()
    publishing_service.publish_image.assert_not_called()


@pytest.mark.parametrize(
    "token",
    [None, "", " ", "\t\n"],
)
def test_instagram_publisher_rejects_missing_access_token(
    token: str | None,
) -> None:
    account = make_instagram_account()
    credentials = Mock()
    credentials.get.return_value = token
    publishing_service = Mock()

    publisher = InstagramPublisher(
        account=account,
        credential_store=credentials,
        publishing_service=publishing_service,
    )

    post = Mock()
    post.source.tags = ()
    post.source.images = (Mock(),)
    post.images = ()

    with pytest.raises(ValueError, match="access token"):
        publisher.publish(post)

    credentials.get.assert_called_once_with(
        InstagramCredentialKeys.access_token(account)
    )
    publishing_service.publish_image.assert_not_called()


def test_instagram_publisher_retrieves_account_access_token() -> None:
    account = make_instagram_account()
    credentials = Mock()
    credentials.get.return_value = "test-access-token"
    publishing_service = Mock()

    publisher = InstagramPublisher(
        account=account,
        credential_store=credentials,
        publishing_service=publishing_service,
    )

    post = Mock()
    post.source.tags = ()
    post.source.images = (Mock(),)
    post.images = ()

    with pytest.raises(
            PublisherNotConfiguredError,
            match="image URL provider",
    ):
        publisher.publish(post)

    credentials.get.assert_called_once_with(
        InstagramCredentialKeys.access_token(account)
    )
    publishing_service.publish_image.assert_not_called()


def test_instagram_publisher_rejects_text_only_post_before_credentials() -> None:
    account = make_instagram_account()
    credentials = Mock()
    publishing_service = Mock()

    publisher = InstagramPublisher(
        account=account,
        credential_store=credentials,
        publishing_service=publishing_service,
    )

    post = Mock()
    post.source.tags = ()
    post.source.images = ()
    post.images = ()

    with pytest.raises(ValueError, match="image"):
        publisher.publish(post)

    credentials.get.assert_not_called()
    publishing_service.publish_image.assert_not_called()


def test_instagram_publisher_rejects_multiple_images_before_credentials() -> None:
    account = make_instagram_account()
    credentials = Mock()
    publishing_service = Mock()

    publisher = InstagramPublisher(
        account=account,
        credential_store=credentials,
        publishing_service=publishing_service,
    )

    post = Mock()
    post.source.tags = ()
    post.source.images = (Mock(), Mock())
    post.images = ()

    with pytest.raises(ValueError, match="exactly one image"):
        publisher.publish(post)

    credentials.get.assert_not_called()
    publishing_service.publish_image.assert_not_called()


def test_instagram_publisher_rejects_tags_before_credentials() -> None:
    account = make_instagram_account()
    credentials = Mock()
    publishing_service = Mock()

    publisher = InstagramPublisher(
        account=account,
        credential_store=credentials,
        publishing_service=publishing_service,
    )

    post = Mock()
    post.source.images = (Mock(),)
    post.source.tags = (Mock(),)
    post.images = ()

    with pytest.raises(ValueError, match="tag"):
        publisher.publish(post)

    credentials.get.assert_not_called()
    publishing_service.publish_image.assert_not_called()


def test_instagram_publisher_rejects_prepared_image_count_mismatch() -> None:
    account = make_instagram_account()
    credentials = Mock()
    publishing_service = Mock()

    publisher = InstagramPublisher(
        account=account,
        credential_store=credentials,
        publishing_service=publishing_service,
    )

    source_image = Mock()

    post = Mock()
    post.source.tags = ()
    post.source.images = (source_image,)
    post.images = (Mock(), Mock())

    with pytest.raises(ValueError, match="prepared image count"):
        publisher.publish(post)

    credentials.get.assert_not_called()
    publishing_service.publish_image.assert_not_called()


def test_instagram_publisher_rejects_inconsistent_prepared_image() -> None:
    account = make_instagram_account()
    credentials = Mock()
    publishing_service = Mock()

    publisher = InstagramPublisher(
        account=account,
        credential_store=credentials,
        publishing_service=publishing_service,
    )

    source_image = Mock()
    prepared_image = Mock()
    prepared_image.source = Mock()
    prepared_image.destination = PublishingDestination.INSTAGRAM

    post = Mock()
    post.source.tags = ()
    post.source.images = (source_image,)
    post.images = (prepared_image,)

    with pytest.raises(ValueError, match="inconsistent"):
        publisher.publish(post)

    credentials.get.assert_not_called()
    publishing_service.publish_image.assert_not_called()


def test_instagram_publisher_rejects_prepared_image_for_other_destination() -> None:
    account = make_instagram_account()
    credentials = Mock()
    publishing_service = Mock()

    publisher = InstagramPublisher(
        account=account,
        credential_store=credentials,
        publishing_service=publishing_service,
    )

    source_image = Mock()
    prepared_image = Mock()
    prepared_image.source = source_image
    prepared_image.destination = PublishingDestination.FACEBOOK

    post = Mock()
    post.source.tags = ()
    post.source.images = (source_image,)
    post.images = (prepared_image,)

    with pytest.raises(ValueError, match="Instagram"):
        publisher.publish(post)

    credentials.get.assert_not_called()
    publishing_service.publish_image.assert_not_called()


def test_instagram_publisher_accepts_image_url_provider() -> None:
    account = make_instagram_account()
    credentials = Mock()
    publishing_service = Mock()
    image_url_provider = Mock()

    publisher = InstagramPublisher(
        account=account,
        credential_store=credentials,
        publishing_service=publishing_service,
        image_url_provider=image_url_provider,
    )

    assert publisher._image_url_provider is image_url_provider


def test_instagram_publisher_constructor_does_not_access_credentials_or_host_images() -> None:
    account = make_instagram_account()
    credentials = Mock()
    publishing_service = Mock()
    image_url_provider = Mock()

    InstagramPublisher(
        account=account,
        credential_store=credentials,
        publishing_service=publishing_service,
        image_url_provider=image_url_provider,
    )

    credentials.get.assert_not_called()
    image_url_provider.get_public_url.assert_not_called()
    publishing_service.publish_image.assert_not_called()


def test_instagram_publisher_rejects_other_destination_with_image_url_provider() -> None:
    account = Account(
        name="Test Facebook",
        destination=PublishingDestination.FACEBOOK,
    )
    credentials = Mock()
    publishing_service = Mock()
    image_url_provider = Mock()

    with pytest.raises(ValueError, match="Instagram account"):
        InstagramPublisher(
            account=account,
            credential_store=credentials,
            publishing_service=publishing_service,
            image_url_provider=image_url_provider,
        )

    credentials.get.assert_not_called()
    image_url_provider.get_public_url.assert_not_called()
    publishing_service.publish_image.assert_not_called()


def test_instagram_publisher_rejects_missing_image_url_provider() -> None:
    account = make_instagram_account()
    credentials = Mock()
    credentials.get.return_value = "valid-access-token"
    publishing_service = Mock()

    publisher = InstagramPublisher(
        account=account,
        credential_store=credentials,
        publishing_service=publishing_service,
    )

    source_image = Mock()
    post = Mock()
    post.source.tags = ()
    post.source.images = (source_image,)
    post.images = ()

    with pytest.raises(
        PublisherNotConfiguredError,
        match="image URL provider",
    ):
        publisher.publish(post)

    publishing_service.publish_image.assert_not_called()


def test_instagram_publisher_resolves_source_image_path() -> None:
    account = make_instagram_account()
    credentials = Mock()
    credentials.get.return_value = "valid-access-token"
    publishing_service = Mock()
    image_url_provider = Mock()
    image_url_provider.get_public_url.return_value = (
        "https://example.com/photo.jpg"
    )

    publisher = InstagramPublisher(
        account=account,
        credential_store=credentials,
        publishing_service=publishing_service,
        image_url_provider=image_url_provider,
    )

    source_image = Mock()
    source_image.path = Path("/tmp/instagram-photo.jpg")

    post = Mock()
    post.source.tags = ()
    post.source.images = (source_image,)
    post.images = ()

    publisher.publish(post)

    image_url_provider.get_public_url.assert_called_once_with(
        source_image.path
    )
    publishing_service.publish_image.assert_called_once()


def test_instagram_publisher_propagates_image_url_provider_failure() -> None:
    account = make_instagram_account()
    credentials = Mock()
    credentials.get.return_value = "valid-access-token"
    publishing_service = Mock()
    image_url_provider = Mock()
    image_url_provider.get_public_url.side_effect = RuntimeError(
        "Image hosting failed."
    )

    publisher = InstagramPublisher(
        account=account,
        credential_store=credentials,
        publishing_service=publishing_service,
        image_url_provider=image_url_provider,
    )

    source_image = Mock()
    source_image.path = Path("/tmp/instagram-photo.jpg")

    post = Mock()
    post.source.tags = ()
    post.source.images = (source_image,)
    post.images = ()

    with pytest.raises(RuntimeError, match="Image hosting failed"):
        publisher.publish(post)

    image_url_provider.get_public_url.assert_called_once_with(
        source_image.path
    )
    publishing_service.publish_image.assert_not_called()


@pytest.mark.parametrize(
    "public_url",
    [
        "",
        "   ",
        "http://example.com/photo.jpg",
        "not-a-url",
        "https://",
        "https://example.com@localhost/photo.jpg",
        "https://localhost/photo.jpg",
    ],
)
def test_instagram_publisher_rejects_invalid_public_image_url(
    public_url: str,
) -> None:
    account = make_instagram_account()

    credentials = Mock()
    credentials.get.return_value = "valid-access-token"

    publishing_service = Mock()

    image_url_provider = Mock()
    image_url_provider.get_public_url.return_value = public_url

    publisher = InstagramPublisher(
        account=account,
        credential_store=credentials,
        publishing_service=publishing_service,
        image_url_provider=image_url_provider,
    )

    source_image = Mock()
    source_image.path = Path("/tmp/instagram-photo.jpg")

    post = Mock()
    post.source.tags = ()
    post.source.images = (source_image,)
    post.images = ()

    with pytest.raises(ValueError, match="public HTTPS"):
        publisher.publish(post)

    image_url_provider.get_public_url.assert_called_once_with(
        source_image.path
    )

    publishing_service.publish_image.assert_not_called()


def test_instagram_publisher_accepts_valid_public_https_url() -> None:
    account = make_instagram_account()

    credentials = Mock()
    credentials.get.return_value = "valid-access-token"

    publishing_service = Mock()

    image_url_provider = Mock()
    image_url_provider.get_public_url.return_value = (
        "https://images.example.com/photo.jpg"
    )

    publisher = InstagramPublisher(
        account=account,
        credential_store=credentials,
        publishing_service=publishing_service,
        image_url_provider=image_url_provider,
    )

    source_image = Mock()
    source_image.path = Path("/tmp/instagram-photo.jpg")

    post = Mock()
    post.source.tags = ()
    post.source.images = (source_image,)
    post.images = ()

    publisher.publish(post)

    image_url_provider.get_public_url.assert_called_once_with(
        source_image.path
    )

    publishing_service.publish_image.assert_called_once()


def test_instagram_publisher_delegates_image_to_publishing_service() -> None:
    account = make_instagram_account()

    credentials = Mock()
    credentials.get.return_value = "valid-access-token"

    publishing_service = Mock()

    image_url_provider = Mock()
    image_url_provider.get_public_url.return_value = (
        "https://images.example.com/photo.jpg"
    )

    publisher = InstagramPublisher(
        account=account,
        credential_store=credentials,
        publishing_service=publishing_service,
        image_url_provider=image_url_provider,
    )

    source_image = Mock()
    source_image.path = Path("/tmp/instagram-photo.jpg")

    post = Mock()
    post.source.text = "Instagram test caption"
    post.source.tags = ()
    post.source.images = (source_image,)
    post.images = ()

    publisher.publish(post)

    credentials.get.assert_called_once_with(
        InstagramCredentialKeys.access_token(account)
    )

    image_url_provider.get_public_url.assert_called_once_with(
        source_image.path
    )

    publishing_service.publish_image.assert_called_once_with(
        instagram_user_id=account.instagram_config.instagram_user_id,
        access_token="valid-access-token",
        image_url="https://images.example.com/photo.jpg",
        caption="Instagram test caption",
    )


def test_instagram_publisher_propagates_publishing_service_failure() -> None:
    account = make_instagram_account()

    credentials = Mock()
    credentials.get.return_value = "valid-access-token"

    publishing_service = Mock()
    publishing_service.publish_image.side_effect = RuntimeError(
        "Instagram publishing failed."
    )

    image_url_provider = Mock()
    image_url_provider.get_public_url.return_value = (
        "https://images.example.com/photo.jpg"
    )

    publisher = InstagramPublisher(
        account=account,
        credential_store=credentials,
        publishing_service=publishing_service,
        image_url_provider=image_url_provider,
    )

    source_image = Mock()
    source_image.path = Path("/tmp/instagram-photo.jpg")

    post = Mock()
    post.source.text = "Instagram test caption"
    post.source.tags = ()
    post.source.images = (source_image,)
    post.images = ()

    with pytest.raises(
        RuntimeError,
        match="Instagram publishing failed",
    ):
        publisher.publish(post)

    image_url_provider.get_public_url.assert_called_once_with(
        source_image.path
    )

    publishing_service.publish_image.assert_called_once_with(
        instagram_user_id=account.instagram_config.instagram_user_id,
        access_token="valid-access-token",
        image_url="https://images.example.com/photo.jpg",
        caption="Instagram test caption",
    )


def test_instagram_publisher_uses_prepared_image_path() -> None:
    account = make_instagram_account()

    credentials = Mock()
    credentials.get.return_value = "valid-access-token"

    publishing_service = Mock()

    image_url_provider = Mock()
    image_url_provider.get_public_url.return_value = (
        "https://images.example.com/prepared-photo.jpg"
    )

    publisher = InstagramPublisher(
        account=account,
        credential_store=credentials,
        publishing_service=publishing_service,
        image_url_provider=image_url_provider,
    )

    source_image = Mock()
    source_image.path = Path("/tmp/original-photo.png")

    prepared_image = Mock()
    prepared_image.source = source_image
    prepared_image.destination = PublishingDestination.INSTAGRAM
    prepared_image.path = Path("/tmp/prepared-photo.jpg")

    post = Mock()
    post.source.text = "Prepared Instagram photo"
    post.source.tags = ()
    post.source.images = (source_image,)
    post.images = (prepared_image,)

    publisher.publish(post)

    image_url_provider.get_public_url.assert_called_once_with(
        prepared_image.path
    )

    publishing_service.publish_image.assert_called_once_with(
        instagram_user_id=account.instagram_config.instagram_user_id,
        access_token="valid-access-token",
        image_url="https://images.example.com/prepared-photo.jpg",
        caption="Prepared Instagram photo",
    )


def test_instagram_publisher_does_not_fallback_after_prepared_image_failure() -> None:
    account = make_instagram_account()

    credentials = Mock()
    credentials.get.return_value = "valid-access-token"

    publishing_service = Mock()

    image_url_provider = Mock()
    image_url_provider.get_public_url.side_effect = RuntimeError(
        "Prepared image hosting failed."
    )

    publisher = InstagramPublisher(
        account=account,
        credential_store=credentials,
        publishing_service=publishing_service,
        image_url_provider=image_url_provider,
    )

    source_image = Mock()
    source_image.path = Path("/tmp/original-photo.png")

    prepared_image = Mock()
    prepared_image.source = source_image
    prepared_image.destination = PublishingDestination.INSTAGRAM
    prepared_image.path = Path("/tmp/prepared-photo.jpg")

    post = Mock()
    post.source.text = "Prepared Instagram photo"
    post.source.tags = ()
    post.source.images = (source_image,)
    post.images = (prepared_image,)

    with pytest.raises(
        RuntimeError,
        match="Prepared image hosting failed",
    ):
        publisher.publish(post)

    image_url_provider.get_public_url.assert_called_once_with(
        prepared_image.path
    )

    publishing_service.publish_image.assert_not_called()
