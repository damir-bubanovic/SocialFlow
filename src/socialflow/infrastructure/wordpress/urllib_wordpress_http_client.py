import base64
import ssl
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import (
    HTTPSHandler,
    HTTPRedirectHandler,
    Request,
    build_opener,
)

from socialflow.infrastructure.wordpress.wordpress_http_client import (
    WordPressHttpClient,
    WordPressHttpResponse,
)


class _NoRedirectHandler(HTTPRedirectHandler):
    """Prevent redirects from forwarding authentication headers."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class UrllibWordPressHttpClient(WordPressHttpClient):
    """Communicate with WordPress using HTTPS."""

    def __init__(self, timeout: float = 10.0) -> None:
        if timeout <= 0:
            raise ValueError("HTTP timeout must be positive.")

        self._timeout = timeout

    def get_authenticated_user(
        self,
        site_url: str,
        username: str,
        application_password: str,
    ) -> WordPressHttpResponse:
        """Verify WordPress credentials through the REST API."""
        parsed = urlsplit(site_url)

        if (
            parsed.scheme.lower() != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("A valid HTTPS site URL is required.")

        endpoint = (
            site_url.rstrip("/")
            + "/wp-json/wp/v2/users/me"
        )

        credentials = f"{username}:{application_password}"
        encoded = base64.b64encode(
            credentials.encode("utf-8")
        ).decode("ascii")

        request = Request(
            endpoint,
            headers={
                "Authorization": f"Basic {encoded}",
                "Accept": "application/json",
            },
            method="GET",
        )

        opener = build_opener(
            HTTPSHandler(context=ssl.create_default_context()),
            _NoRedirectHandler(),
        )

        try:
            with opener.open(
                request,
                timeout=self._timeout,
            ) as response:
                return WordPressHttpResponse(
                    status_code=response.status,
                )
        except HTTPError as error:
            return WordPressHttpResponse(
                status_code=error.code,
            )