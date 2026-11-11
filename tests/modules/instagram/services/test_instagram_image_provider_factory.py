from typing import cast
from unittest.mock import Mock

import pytest

from socialflow.modules.instagram.services.instagram_image_provider_config import (
    InstagramImageProviderConfig,
    InstagramImageProviderType,
)
from socialflow.modules.instagram.services.instagram_image_provider_factory import (
    InstagramImageProviderFactory,
)
from socialflow.modules.instagram.services.instagram_image_url_provider import (
    InstagramImageUrlProvider,
)


def test_factory_rejects_unconfigured_provider() -> None:
    factory = InstagramImageProviderFactory()

    config = InstagramImageProviderConfig()

    with pytest.raises(
        ValueError,
        match="not configured",
    ):
        factory.create(config)


@pytest.mark.parametrize(
    "provider_type",
    [
        InstagramImageProviderType.EXTERNAL_HOSTING,
        InstagramImageProviderType.SELF_HOSTED,
    ],
)
def test_factory_rejects_unavailable_backend(
    provider_type: InstagramImageProviderType,
) -> None:
    factory = InstagramImageProviderFactory()

    config = InstagramImageProviderConfig(
        provider_type=provider_type,
    )

    with pytest.raises(
        ValueError,
        match="not available",
    ):
        factory.create(config)


def test_factory_returns_registered_external_provider() -> None:
    provider = Mock()

    factory = InstagramImageProviderFactory(
        providers={
            InstagramImageProviderType.EXTERNAL_HOSTING: provider,
        },
    )

    config = InstagramImageProviderConfig(
        provider_type=InstagramImageProviderType.EXTERNAL_HOSTING,
    )

    assert factory.create(config) is provider


def test_factory_returns_registered_self_hosted_provider() -> None:
    provider = Mock()

    factory = InstagramImageProviderFactory(
        providers={
            InstagramImageProviderType.SELF_HOSTED: provider,
        },
    )

    config = InstagramImageProviderConfig(
        provider_type=InstagramImageProviderType.SELF_HOSTED,
    )

    assert factory.create(config) is provider


def test_factory_rejects_unconfigured_provider_before_lookup() -> None:
    factory = InstagramImageProviderFactory()

    with pytest.raises(
        ValueError,
        match="not configured",
    ):
        factory.create(InstagramImageProviderConfig())


def test_factory_rejects_invalid_provider_object() -> None:
    with pytest.raises(
        ValueError,
        match="invalid",
    ):
        InstagramImageProviderFactory(
            providers={
                InstagramImageProviderType.EXTERNAL_HOSTING: cast(
                    InstagramImageUrlProvider,
                    object(),
                ),
            },
        )


def test_factory_copies_provider_registrations() -> None:
    original_provider = Mock()
    replacement_provider = Mock()

    providers = {
        InstagramImageProviderType.EXTERNAL_HOSTING: original_provider,
    }

    factory = InstagramImageProviderFactory(
        providers=providers,
    )

    providers[
        InstagramImageProviderType.EXTERNAL_HOSTING
    ] = replacement_provider

    config = InstagramImageProviderConfig(
        provider_type=InstagramImageProviderType.EXTERNAL_HOSTING,
    )

    assert factory.create(config) is original_provider


def test_factory_rejects_invalid_registration_key() -> None:
    provider = Mock()

    with pytest.raises(
        ValueError,
        match="provider type",
    ):
        InstagramImageProviderFactory(
            providers={
                cast(
                    InstagramImageProviderType,
                    "unknown",
                ): provider,
            },
        )


def test_factory_rejects_unconfigured_registration() -> None:
    provider = Mock()

    with pytest.raises(
        ValueError,
        match="unconfigured",
    ):
        InstagramImageProviderFactory(
            providers={
                InstagramImageProviderType.UNCONFIGURED: provider,
            },
        )
