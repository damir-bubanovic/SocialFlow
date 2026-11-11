
from dataclasses import dataclass
from enum import Enum


class InstagramImageProviderType(str, Enum):
    """Supported Instagram image-hosting provider categories."""

    UNCONFIGURED = "unconfigured"
    EXTERNAL_HOSTING = "external_hosting"
    SELF_HOSTED = "self_hosted"


@dataclass(frozen=True, slots=True)
class InstagramImageProviderConfig:
    """Configuration for selecting an Instagram image URL provider."""

    provider_type: InstagramImageProviderType = (
        InstagramImageProviderType.UNCONFIGURED
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.provider_type,
            InstagramImageProviderType,
        ):
            raise ValueError(
                "Invalid Instagram image provider type."
            )

    def is_configured(self) -> bool:
        """Return whether a hosting provider category is selected."""
        return (
            self.provider_type
            is not InstagramImageProviderType.UNCONFIGURED
        )
