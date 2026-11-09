
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FacebookPageConfig:
    """Non-secret configuration for a Facebook Page."""

    page_id: str
    page_name: str

    def normalized(self) -> "FacebookPageConfig":
        """Return configuration with trimmed values."""
        return FacebookPageConfig(
            page_id=self.page_id.strip(),
            page_name=self.page_name.strip(),
        )

    def is_complete(self) -> bool:
        """Return whether the required Page ID is present."""
        return bool(self.page_id.strip())
