
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class FacebookPost:
    """A post retrieved from a Facebook Page."""

    id: str
    page_id: str
    message: str
    created_at: datetime
    permalink_url: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError(
                "Facebook post ID must be a non-empty string."
            )

        if not isinstance(self.page_id, str) or not self.page_id.strip():
            raise ValueError(
                "Facebook Page ID must be a non-empty string."
            )

        if not isinstance(self.message, str):
            raise ValueError(
                "Facebook post message must be a string."
            )

        if not isinstance(self.created_at, datetime):
            raise ValueError(
                "Facebook post creation date must be a datetime."
            )

        if (
            self.permalink_url is not None
            and not isinstance(self.permalink_url, str)
        ):
            raise ValueError(
                "Facebook post permalink must be a string or None."
            )

        object.__setattr__(self, "id", self.id.strip())
        object.__setattr__(self, "page_id", self.page_id.strip())
