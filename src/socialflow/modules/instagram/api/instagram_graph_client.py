import json
import re
from typing import Any
from urllib.error import URLError
from urllib.parse import urlencode

from socialflow.modules.instagram.api.instagram_api_error import (
    InstagramApiError,
)
from socialflow.modules.instagram.api.instagram_http_transport import (
    InstagramHttpResponse,
    InstagramHttpTransport,
)
from socialflow.modules.instagram.api.urllib_instagram_http_transport import (
    UrllibInstagramHttpTransport,
)


_GRAPH_VERSION_PATTERN = re.compile(r"v[1-9][0-9]*\.[0-9]+")
_TRANSIENT_HTTP_STATUSES = {429, 500, 502, 503, 504}
_TRANSIENT_GRAPH_CODES = {4, 17, 32, 613}


class InstagramGraphClient:
    """Versioned Instagram Graph API client."""

    BASE_URL = "https://graph.instagram.com"

    def __init__(
        self,
        api_version: str,
        transport: InstagramHttpTransport | None = None,
        timeout: float = 10.0,
    ) -> None:
        if (
            not isinstance(api_version, str)
            or not _GRAPH_VERSION_PATTERN.fullmatch(api_version)
        ):
            raise ValueError("Invalid Instagram Graph API version.")

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
            else UrllibInstagramHttpTransport()
        )
        self._timeout = timeout

    def get(
        self,
        path: str,
        access_token: str,
        params: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Request a JSON object from the Instagram Graph API."""
        self._validate_request_inputs(path, access_token, params)

        query = urlencode(params or {})
        url = f"{self.BASE_URL}/{self._api_version}/{path}"

        if query:
            url = f"{url}?{query}"

        try:
            response = self._transport.get(
                url=url,
                headers={
                    "Authorization": f"Bearer {access_token.strip()}",
                    "Accept": "application/json",
                },
                timeout=self._timeout,
            )
        except (TimeoutError, URLError, OSError):
            raise InstagramApiError(
                message="Instagram network request failed.",
                is_transient=True,
            ) from None

        return self._parse_response(response)

    def post(
        self,
        path: str,
        access_token: str,
        params: dict[str, str],
    ) -> dict[str, Any]:
        """POST form-encoded data to the Instagram Graph API."""
        if not isinstance(params, dict):
            raise ValueError(
                "Graph API parameters must be a dictionary."
            )

        self._validate_request_inputs(path, access_token, params)

        url = f"{self.BASE_URL}/{self._api_version}/{path}"
        body = urlencode(params).encode("utf-8")

        try:
            response = self._transport.post(
                url=url,
                headers={
                    "Authorization": f"Bearer {access_token.strip()}",
                    "Accept": "application/json",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                body=body,
                timeout=self._timeout,
            )
        except (TimeoutError, URLError, OSError):
            raise InstagramApiError(
                message="Instagram network request failed.",
                is_transient=True,
            ) from None

        return self._parse_response(response)

    @staticmethod
    def _validate_request_inputs(
        path: str,
        access_token: str,
        params: dict[str, str] | None,
    ) -> None:
        """Validate Graph API paths, tokens, and parameters."""
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
            raise ValueError("Instagram access token is required.")

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
        response: InstagramHttpResponse,
    ) -> dict[str, Any]:
        status = response.status_code

        if type(status) is not int or not 100 <= status <= 599:
            raise InstagramApiError(
                message="Invalid Instagram HTTP response status.",
            )

        if not isinstance(response.body, bytes):
            raise InstagramApiError(
                message="Invalid Instagram HTTP response body.",
                status_code=status,
            )

        try:
            payload = json.loads(response.body)
        except (ValueError, UnicodeDecodeError, TypeError):
            raise InstagramApiError(
                message="Invalid Instagram API JSON response.",
                status_code=status,
                is_transient=status in _TRANSIENT_HTTP_STATUSES,
            ) from None

        if not isinstance(payload, dict):
            raise InstagramApiError(
                message="Unexpected Instagram API response format.",
                status_code=status,
                is_transient=status in _TRANSIENT_HTTP_STATUSES,
            )

        error_payload = payload.get("error")

        if isinstance(error_payload, dict):
            code = cls._optional_int(error_payload.get("code"))
            subcode = cls._optional_int(
                error_payload.get("error_subcode")
            )

            raise InstagramApiError(
                message="Instagram Graph API returned an error.",
                status_code=status,
                code=code,
                subcode=subcode,
                is_transient=(
                    error_payload.get("is_transient") is True
                    or status in _TRANSIENT_HTTP_STATUSES
                    or code in _TRANSIENT_GRAPH_CODES
                ),
                error_type=cls._optional_string(
                    error_payload.get("type")
                ),
            )

        if status != 200:
            raise InstagramApiError(
                message="Unexpected Instagram HTTP response status.",
                status_code=status,
                is_transient=status in _TRANSIENT_HTTP_STATUSES,
            )

        return payload