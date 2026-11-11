
from dataclasses import FrozenInstanceError

import pytest

from socialflow.modules.instagram.services.instagram_image_provider_config import (
    InstagramImageProviderConfig,
    InstagramImageProviderType,
)


def test_provider_config_defaults_to_unconfigured() -> None:
    config = InstagramImageProviderConfig()

    assert config.provider_type is InstagramImageProviderType.UNCONFIGURED
    assert not config.is_configured()


def test_provider_config_accepts_external_hosting() -> None:
    config = InstagramImageProviderConfig(
        provider_type=InstagramImageProviderType.EXTERNAL_HOSTING,
    )

    assert config.is_configured()


def test_provider_config_accepts_self_hosted_storage() -> None:
    config = InstagramImageProviderConfig(
        provider_type=InstagramImageProviderType.SELF_HOSTED,
    )

    assert config.is_configured()


def test_provider_config_is_immutable() -> None:
    config = InstagramImageProviderConfig()

    with pytest.raises(FrozenInstanceError):
        setattr(
            config,
            "provider_type",
            InstagramImageProviderType.EXTERNAL_HOSTING,
        )


def test_provider_config_rejects_unknown_provider_type() -> None:
    with pytest.raises(ValueError, match="provider type"):
        InstagramImageProviderConfig(
            provider_type="unknown",
        )
