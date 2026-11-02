
from dataclasses import dataclass, field

from socialflow.modules.facebook.models.facebook_page import (
    FacebookPage,
)


@dataclass(frozen=True, slots=True)
class DiscoveredFacebookPage:
    """A discovered Facebook Page and its temporary credential."""

    page: FacebookPage
    access_token: str = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        if not isinstance(self.page, FacebookPage):
            raise ValueError("A valid Facebook Page is required.")

        if (
            not isinstance(self.access_token, str)
            or not self.access_token.strip()
        ):
            raise ValueError("A Facebook Page access token is required.")

        object.__setattr__(
            self,
            "access_token",
            self.access_token.strip(),
        )
