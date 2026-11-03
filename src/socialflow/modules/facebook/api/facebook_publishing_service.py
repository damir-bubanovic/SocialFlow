from socialflow.modules.facebook.api.facebook_graph_client import (
    FacebookGraphClient,
)


class FacebookPublishingService:
    """Publish text posts to a Facebook Page."""

    def __init__(
        self,
        client: FacebookGraphClient,
    ) -> None:
        if not isinstance(client, FacebookGraphClient):
            raise ValueError(
                "A Facebook Graph API client is required."
            )

        self._client = client

    def publish_text(
        self,
        page_id: str,
        access_token: str,
        message: str,
    ) -> str:
        """Publish a text post and return its Facebook post ID."""
        if not isinstance(page_id, str) or not page_id.strip():
            raise ValueError("A Facebook Page ID is required.")

        page_id = page_id.strip()

        if not page_id.isascii() or not page_id.isdecimal():
            raise ValueError("Invalid Facebook Page ID.")

        if not isinstance(access_token, str) or not access_token.strip():
            raise ValueError("A Facebook Page access token is required.")

        if not isinstance(message, str) or not message.strip():
            raise ValueError("A non-empty post message is required.")

        response = self._client.post(
            path=f"{page_id}/feed",
            access_token=access_token,
            params={"message": message},
        )

        post_id = response.get("id")

        if not isinstance(post_id, str) or not post_id.strip():
            raise ValueError(
                "Facebook did not return a valid post ID."
            )

        return post_id.strip()