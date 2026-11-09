
from typing import Any

from socialflow.modules.facebook.api.facebook_api_error import (
    FacebookApiError,
)
from socialflow.modules.facebook.models.discovered_facebook_page import (
    DiscoveredFacebookPage,
)
from socialflow.modules.facebook.models.facebook_page import (
    FacebookPage,
)


def parse_discovered_pages(
    payload: dict[str, Any],
) -> list[DiscoveredFacebookPage]:
    """Parse one Graph API Page discovery response."""

    if not isinstance(payload, dict):
        raise FacebookApiError(
            message="Invalid Facebook Page discovery response.",
        )

    data = payload.get("data")

    if not isinstance(data, list):
        raise FacebookApiError(
            message="Facebook Page discovery data is missing.",
        )

    pages: list[DiscoveredFacebookPage] = []
    seen_ids: set[str] = set()

    for item in data:
        if not isinstance(item, dict):
            raise FacebookApiError(
                message="Invalid Facebook Page discovery entry.",
            )

        page_id = item.get("id")
        page_name = item.get("name")
        page_token = item.get("access_token")

        if (
            not isinstance(page_id, str)
            or not page_id.strip()
            or not isinstance(page_name, str)
            or not page_name.strip()
            or not isinstance(page_token, str)
            or not page_token.strip()
        ):
            raise FacebookApiError(
                message="Incomplete Facebook Page discovery entry.",
            )

        normalized_id = page_id.strip()

        if normalized_id in seen_ids:
            raise FacebookApiError(
                message="Duplicate Facebook Page ID in discovery response.",
            )

        seen_ids.add(normalized_id)

        pages.append(
            DiscoveredFacebookPage(
                page=FacebookPage(
                    id=normalized_id,
                    name=page_name.strip(),
                ),
                access_token=page_token,
            )
        )

    return pages
