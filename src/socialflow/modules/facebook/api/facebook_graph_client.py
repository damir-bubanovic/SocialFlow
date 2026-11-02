
import json
import re
from typing import Any
from urllib.error import URLError
from urllib.parse import urlencode

from socialflow.modules.facebook.api.facebook_api_error import (
    FacebookApiError,
)
from socialflow.modules.facebook.api.facebook_http_transport import (
    FacebookHttpResponse,
    FacebookHttpTransport,
)
from socialflow.modules.facebook.api.urllib_facebook_http_transport import (
    UrllibFacebookHttpTransport,
)


_GRAPH_VERSION_PATTERN = re.compile(r"v[1-9][0-9]*\.[0-9]+")
_TRANSIENT_HTTP_STATUSES = {429, 500, 502, 503, 504}
_TRANSIENT_GRAPH_CODES = {4, 17, 32, 613}


class FacebookGraphClient:
    """Versioned Facebook Graph API client."""

    BASE_URL = "https://graph.facebook.com"

    def __init__(
        self,
        api_version: str,
        transport: FacebookHttpTransport | None = None,
        timeout: float = 10.0,
    ) -> None:
        if (
            not isinstance(api_version, str)
            or not _GRAPH_VERSION_PATTERN.fullmatch(api_version)
        ):
            raise ValueError("Invalid Facebook Graph API version.")

        if (
            isinstance(timeout, bool)
            or not isinstance(timeout, (int, float))
            or not 0 < timeout < float("inf")
        ):
            raise ValueError("HTTP timeout must be positive and finite.")

        self._api_version = api_version
        self._transport = (
            transport
            if transport is not None
            else UrllibFacebookHttpTransport()
        )
        self._timeout = timeout

    def get(
        self,
        path: str,
        access_token: str,
        params: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Request a JSON object from the Graph API."""

        if (
            not isinstance(path, str)
            or not path
            or path.startswith("/")
            or "?" in path
            or "#" in path
            or "\\" in path
        ):
            raise ValueError("Invalid Graph API resource path.")

        segments = path.split("/")

        if any(
            not segment
            or segment in (".", "..")
            or not re.fullmatch(r"[A-Za-z0-9_.-]+", segment)
            for segment in segments
        ):
            raise ValueError("Invalid Graph API resource path.")

        if not isinstance(access_token, str) or not access_token.strip():
            raise ValueError("Facebook access token is required.")

        if params is not None:
            if not isinstance(params, dict):
                raise ValueError(
                    "Graph API parameters must be a dictionary."
                )

            if any(
                    not isinstance(key, str)
                    or not key
                    or not isinstance(value, str)
                    for key, value in params.items()
            ):
                raise ValueError(
                    "Graph API parameters must contain "
                    "non-empty string keys and string values."
                )

            if any(
                    key.lower() == "access_token"
                    for key in params
            ):
                raise ValueError(
                    "Access tokens must be sent in the "
                    "Authorization header."
                )

        query = urlencode(params or {})
        url = f"{self.BASE_URL}/{self._api_version}/{path}"

        if query:
            url = f"{url}?{query}"

        try:
            response = self._transport.get(
                url=url,
                headers={
                    "Authorization": (
                        f"Bearer {access_token.strip()}"
                    ),
                    "Accept": "application/json",
                },
                timeout=self._timeout,
            )
        except (TimeoutError, URLError, OSError):
            raise FacebookApiError(
                message="Facebook network request failed.",
                is_transient=True,
            ) from None

        return self._parse_response(response)

    @staticmethod
    def _optional_int(value: Any) -> int | None:
        if type(value) is int:
            return value
        return None

    @staticmethod
    def _optional_string(value: Any) -> str | None:
        if isinstance(value, str):
            return value
        return None

    @classmethod
    def _parse_response(
        cls,
        response: FacebookHttpResponse,
    ) -> dict[str, Any]:
        status = response.status_code

        if (
                type(status) is not int
                or not 100 <= status <= 599
        ):
            raise FacebookApiError(
                message="Invalid Facebook HTTP response status.",
            )

        if not isinstance(response.body, bytes):
            raise FacebookApiError(
                message="Invalid Facebook HTTP response body.",
                status_code=status,
            )

        try:
            payload = json.loads(response.body)
        except (ValueError, UnicodeDecodeError, TypeError):
            raise FacebookApiError(
                message="Invalid Facebook API JSON response.",
                status_code=status,
                is_transient=status in _TRANSIENT_HTTP_STATUSES,
            ) from None

        if not isinstance(payload, dict):
            raise FacebookApiError(
                message="Unexpected Facebook API response format.",
                status_code=status,
                is_transient=status in _TRANSIENT_HTTP_STATUSES,
            )

        error_payload = payload.get("error")

        if isinstance(error_payload, dict):
            code = cls._optional_int(error_payload.get("code"))
            subcode = cls._optional_int(
                error_payload.get("error_subcode")
            )

            transient_flag = error_payload.get("is_transient")
            explicitly_transient = transient_flag is True

            raise FacebookApiError(
                message="Facebook Graph API returned an error.",
                status_code=status,
                code=code,
                subcode=subcode,
                is_transient=(
                    explicitly_transient
                    or status in _TRANSIENT_HTTP_STATUSES
                    or code in _TRANSIENT_GRAPH_CODES
                ),
                error_type=cls._optional_string(
                    error_payload.get("type")
                ),
            )

        if status != 200:
            raise FacebookApiError(
                message="Unexpected Facebook HTTP response status.",
                status_code=status,
                is_transient=status in _TRANSIENT_HTTP_STATUSES,
            )

        return payload
