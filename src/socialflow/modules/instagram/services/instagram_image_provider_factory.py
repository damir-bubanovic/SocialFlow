
from collections.abc import Mapping

from socialflow.modules.instagram.services.instagram_image_provider_config import (
    InstagramImageProviderConfig,
    InstagramImageProviderType,
)
from socialflow.modules.instagram.services.instagram_image_url_provider import (
    InstagramImageUrlProvider,
)


class InstagramImageProviderFactory:
    """Resolve registered Instagram image URL providers."""

    def __init__(
        self,
        providers: Mapping[
            InstagramImageProviderType,
            InstagramImageUrlProvider,
        ] | None = None,
    ) -> None:
        self._providers = dict(providers or {})

        for provider_type, provider in self._providers.items():
            if not isinstance(
                provider_type,
                InstagramImageProviderType,
            ):
                raise ValueError(
                    "Invalid Instagram image provider type."
                )

            if provider_type is InstagramImageProviderType.UNCONFIGURED:
                raise ValueError(
                    "Cannot register an unconfigured Instagram image provider."
                )

            if not callable(
                getattr(provider, "get_public_url", None)
            ):
                raise ValueError(
                    "invalid Instagram image URL provider."
                )


    def create(
        self,
        config: InstagramImageProviderConfig,
    ) -> InstagramImageUrlProvider:
        """Return the provider selected by the configuration.

        Raises:
            ValueError: If no provider is configured or its backend
                has not been registered.
        """
        provider_type = config.provider_type

        if provider_type is InstagramImageProviderType.UNCONFIGURED:
            raise ValueError(
                "Instagram image URL provider is not configured."
            )

        provider = self._providers.get(provider_type)

        if provider is None:
            raise ValueError(
                "Instagram image URL provider backend is not available."
            )

        return provider
