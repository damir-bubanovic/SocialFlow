
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FacebookPage:
    """A Facebook Page returned by the Meta Graph API."""

    id: str
    name: str

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError(
                "Facebook Page ID must be a non-empty string."
            )

        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError(
                "Facebook Page name must be a non-empty string."
            )

        object.__setattr__(self, "id", self.id.strip())
        object.__setattr__(self, "name", self.name.strip())
