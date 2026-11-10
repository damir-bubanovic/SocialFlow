import math
import ssl
from typing import Mapping
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import (
    HTTPRedirectHandler,
    HTTPSHandler,
    Request,
    build_opener,
)

from socialflow.modules.instagram.api.instagram_http_transport import (
    InstagramHttpResponse,
    InstagramHttpTransport,
)


class _NoRedirectHandler(HTTPRedirectHandler):
    """Do not forward authorization headers through redirects."""

    def redirect_request(
        self,
        req,
        fp,
        code,
        msg,
        headers,
        newurl,
    ):
        return None


class UrllibInstagramHttpTransport(InstagramHttpTransport):
    """HTTPS-only transport for Instagram API requests."""

    def get(
        self,
        url: str,
        headers: Mapping[str, str],
        timeout: float,
    ) -> InstagramHttpResponse:
        return self._request(
            url=url,
            headers=headers,
            timeout=timeout,
            method="GET",
        )

    def post(
        self,
        url: str,
        headers: Mapping[str, str],
        body: bytes,
        timeout: float,
    ) -> InstagramHttpResponse:
        if not isinstance(body, bytes):
            raise ValueError("HTTP request body must be bytes.")

        return self._request(
            url=url,
            headers=headers,
            timeout=timeout,
            method="POST",
            body=body,
        )

    @staticmethod
    def _request(
        *,
        url: str,
        headers: Mapping[str, str],
        timeout: float,
        method: str,
        body: bytes | None = None,
    ) -> InstagramHttpResponse:
        parsed = urlsplit(url)

        if (
            parsed.scheme.lower() != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.fragment
        ):
            raise ValueError("A valid HTTPS URL is required.")

        if (
            isinstance(timeout, bool)
            or not isinstance(timeout, (int, float))
            or not math.isfinite(timeout)
            or timeout <= 0
        ):
            raise ValueError(
                "HTTP timeout must be positive and finite."
            )

        try:
            port = parsed.port
        except ValueError:
            raise ValueError(
                "Invalid HTTPS URL port."
            ) from None

        if port is not None and not 1 <= port <= 65535:
            raise ValueError(
                "Invalid HTTPS URL port."
            )

        request = Request(
            url,
            data=body,
            headers=dict(headers),
            method=method,
        )

        opener = build_opener(
            HTTPSHandler(context=ssl.create_default_context()),
            _NoRedirectHandler(),
        )

        try:
            with opener.open(request, timeout=timeout) as response:
                return InstagramHttpResponse(
                    status_code=response.status,
                    body=response.read(),
                )
        except HTTPError as error:
            try:
                response_body = error.read()
            finally:
                error.close()

            return InstagramHttpResponse(
                status_code=error.code,
                body=response_body,
            )