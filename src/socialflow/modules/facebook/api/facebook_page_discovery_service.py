
from socialflow.modules.facebook.api.facebook_api_error import (
    FacebookApiError,
)
from socialflow.modules.facebook.api.facebook_graph_client import (
    FacebookGraphClient,
)
from socialflow.modules.facebook.api.facebook_page_parser import (
    parse_discovered_pages,
)
from socialflow.modules.facebook.models.discovered_facebook_page import (
    DiscoveredFacebookPage,
)


class FacebookPageDiscoveryService:
    """Discover a bounded set of Facebook Pages."""

    DEFAULT_LIMIT = 25
    MAX_LIMIT = 100

    def __init__(
        self,
        client: FacebookGraphClient,
        limit: int = DEFAULT_LIMIT,
    ) -> None:
        if not isinstance(client, FacebookGraphClient):
            raise ValueError("A Facebook Graph API client is required.")

        if (
            type(limit) is not int
            or not 1 <= limit <= self.MAX_LIMIT
        ):
            raise ValueError("Invalid Facebook Page discovery limit.")

        self._client = client
        self._limit = limit

    def discover(
        self,
        user_access_token: str,
    ) -> list[DiscoveredFacebookPage]:
        """Discover Pages accessible through a user access token."""

        if (
            not isinstance(user_access_token, str)
            or not user_access_token.strip()
        ):
            raise ValueError("A Facebook user access token is required.")

        payload = self._client.get(
            path="me/accounts",
            access_token=user_access_token.strip(),
            params={
                "fields": "id,name,access_token",
                "limit": str(self._limit),
            },
        )

        pages = parse_discovered_pages(payload)

        if len(pages) > self._limit:
            raise FacebookApiError(
                message="Facebook returned too many Pages.",
            )

        return pages
