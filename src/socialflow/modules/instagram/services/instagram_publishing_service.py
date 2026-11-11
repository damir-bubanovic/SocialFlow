import ipaddress
import math
import re
import time
from collections.abc import Callable
from urllib.parse import urlsplit

from socialflow.modules.instagram.api.instagram_graph_client import (
    InstagramGraphClient,
)


class InstagramPublishingService:
    """Create Instagram media containers using the Graph API."""

    def __init__(self, graph_client: InstagramGraphClient) -> None:
        self._graph_client = graph_client

    def create_image_container(
        self,
        instagram_user_id: str,
        access_token: str,
        image_url: str,
        caption: str = "",
    ) -> str:
        """Create an Instagram image container and return its ID."""
        if (
                not isinstance(instagram_user_id, str)
                or not re.fullmatch(r"[0-9]+", instagram_user_id.strip())
        ):
            raise ValueError(
                "Instagram user ID must contain ASCII digits only."
            )

        if (
            not isinstance(access_token, str)
            or not access_token.strip()
        ):
            raise ValueError("Instagram access token is required.")

        if not isinstance(image_url, str) or not image_url.strip():
            raise ValueError("Instagram image URL is required.")

        normalized_url = image_url.strip()

        if (
                "\\" in normalized_url
                or any(ord(character) < 33 for character in normalized_url)
        ):
            raise ValueError("Invalid Instagram image URL.")

        try:
            parsed_url = urlsplit(normalized_url)
            hostname = parsed_url.hostname
            port = parsed_url.port
        except ValueError:
            raise ValueError("Invalid Instagram image URL.") from None

        if (
                parsed_url.scheme != "https"
                or not hostname
                or parsed_url.username is not None
                or parsed_url.password is not None
                or parsed_url.query
                or parsed_url.fragment
                or port not in (None, 443)
        ):
            raise ValueError(
                "Instagram image URL must be a valid public HTTPS URL."
            )

        hostname = hostname.lower().rstrip(".")

        if (
                hostname == "localhost"
                or hostname.endswith(".localhost")
                or hostname.endswith(".local")
                or "." not in hostname
        ):
            raise ValueError(
                "Instagram image URL must use a public hostname."
            )

        try:
            ipaddress.ip_address(hostname)
        except ValueError:
            # Domain names require additional DNS-level validation
            # when an image-hosting or retrieval component is added.
            pass
        else:
            # Reject literal IP addresses. Public DNS hostnames are
            # required by this initial publishing contract.
            raise ValueError(
                "Instagram image URL must use a public hostname."
            )

        if not isinstance(caption, str):
            raise ValueError("Instagram caption must be a string.")

        response = self._graph_client.post(
            path=f"{instagram_user_id.strip()}/media",
            access_token=access_token.strip(),
            params={
                "image_url": image_url.strip(),
                "caption": caption,
            },
        )

        container_id = response.get("id")

        if not isinstance(container_id, str) or not container_id.strip():
            raise ValueError(
                "Instagram API response is missing a valid container ID."
            )

        return container_id.strip()


    def get_container_status(
        self,
        container_id: str,
        access_token: str,
    ) -> str:
        """Retrieve the processing status of an Instagram media container."""
        if (
            not isinstance(container_id, str)
            or not re.fullmatch(r"[0-9]+", container_id.strip())
        ):
            raise ValueError(
                "Instagram container ID must contain ASCII digits only."
            )

        if (
            not isinstance(access_token, str)
            or not access_token.strip()
        ):
            raise ValueError("Instagram access token is required.")

        response = self._graph_client.get(
            path=container_id.strip(),
            access_token=access_token.strip(),
            params={"fields": "status_code"},
        )

        status = response.get("status_code")

        valid_statuses = {
            "IN_PROGRESS",
            "FINISHED",
            "ERROR",
            "EXPIRED",
        }

        if not isinstance(status, str) or status not in valid_statuses:
            raise ValueError(
                "Instagram API response contains an invalid container status."
            )

        return status


    def publish_media_container(
        self,
        instagram_user_id: str,
        container_id: str,
        access_token: str,
    ) -> str:
        """Publish a finished Instagram media container and return its media ID."""
        if (
            not isinstance(instagram_user_id, str)
            or not re.fullmatch(r"[0-9]+", instagram_user_id.strip())
        ):
            raise ValueError(
                "Instagram user ID must contain ASCII digits only."
            )

        if (
            not isinstance(container_id, str)
            or not re.fullmatch(r"[0-9]+", container_id.strip())
        ):
            raise ValueError(
                "Instagram container ID must contain ASCII digits only."
            )

        if (
            not isinstance(access_token, str)
            or not access_token.strip()
        ):
            raise ValueError("Instagram access token is required.")

        normalized_user_id = instagram_user_id.strip()
        normalized_container_id = container_id.strip()
        normalized_access_token = access_token.strip()

        status = self.get_container_status(
            container_id=normalized_container_id,
            access_token=normalized_access_token,
        )

        if status != "FINISHED":
            raise ValueError(
                "Instagram media container must have FINISHED status "
                "before publishing."
            )

        response = self._graph_client.post(
            path=f"{normalized_user_id}/media_publish",
            access_token=normalized_access_token,
            params={
                "creation_id": normalized_container_id,
            },
        )

        media_id = response.get("id")

        if (
            not isinstance(media_id, str)
            or not re.fullmatch(r"[0-9]+", media_id.strip())
        ):
            raise ValueError(
                "Instagram API response is missing a valid media ID."
            )

        return media_id.strip()



    def wait_for_container_ready(
        self,
        container_id: str,
        access_token: str,
        max_attempts: int = 3,
        poll_interval_seconds: float = 0.0,
        sleep: Callable[[float], None] = time.sleep,
    ) -> str:
        """Poll container status with bounded attempts and optional delays."""
        if type(max_attempts) is not int or max_attempts < 1:
            raise ValueError(
                "Instagram max_attempts must be a positive integer."
            )

        if (
            type(poll_interval_seconds) not in (int, float)
            or not math.isfinite(poll_interval_seconds)
            or poll_interval_seconds < 0
        ):
            raise ValueError(
                "Instagram poll_interval_seconds must be a finite "
                "non-negative number."
            )

        if not callable(sleep):
            raise ValueError(
                "Instagram sleep must be callable."
            )

        for attempt in range(max_attempts):
            status = self.get_container_status(
                container_id=container_id,
                access_token=access_token,
            )

            if status == "FINISHED":
                return status

            if status in {"ERROR", "EXPIRED"}:
                raise ValueError(
                    f"Instagram media container processing failed: {status}."
                )

            if (
                attempt < max_attempts - 1
                and poll_interval_seconds > 0
            ):
                sleep(float(poll_interval_seconds))

        raise ValueError(
            "Instagram media container remains IN_PROGRESS "
            f"after {max_attempts} status checks."
        )


    def publish_image(
        self,
        instagram_user_id: str,
        access_token: str,
        image_url: str,
        caption: str = "",
        *,
        max_attempts: int = 3,
        poll_interval_seconds: float = 2.0,
        sleep: Callable[[float], None] = time.sleep,
    ) -> str:
        """Create, wait for readiness, and publish an Instagram image."""
        if type(max_attempts) is not int or max_attempts < 1:
            raise ValueError(
                "Instagram max_attempts must be a positive integer."
            )

        if (
            type(poll_interval_seconds) not in (int, float)
            or not math.isfinite(poll_interval_seconds)
            or poll_interval_seconds < 0
        ):
            raise ValueError(
                "Instagram poll_interval_seconds must be a finite "
                "non-negative number."
            )

        if not callable(sleep):
            raise ValueError(
                "Instagram sleep must be callable."
            )

        container_id = self.create_image_container(
            instagram_user_id=instagram_user_id,
            access_token=access_token,
            image_url=image_url,
            caption=caption,
        )

        try:
            self.wait_for_container_ready(
                container_id=container_id,
                access_token=access_token,
                max_attempts=max_attempts,
                poll_interval_seconds=poll_interval_seconds,
                sleep=sleep,
            )
        except ValueError as exc:
            raise ValueError(
                "Instagram media container must have FINISHED status "
                f"before publishing. {exc}"
            ) from exc

        return self.publish_media_container(
            instagram_user_id=instagram_user_id,
            container_id=container_id,
            access_token=access_token,
        )
