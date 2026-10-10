
import base64
import json
import ssl
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import (
    HTTPRedirectHandler,
    HTTPSHandler,
    Request,
    build_opener,
)

from socialflow.infrastructure.wordpress.wordpress_post_client import (
    WordPressPostClient,
)


class _NoRedirectHandler(HTTPRedirectHandler):
    """Prevent redirects from forwarding credentials."""

    def redirect_request(
        self, req, fp, code, msg, headers, newurl
    ):
        return None


class UrllibWordPressPostClient(WordPressPostClient):
    """Create WordPress posts using HTTPS and the REST API."""

    def __init__(self, timeout: float = 10.0) -> None:
        if timeout <= 0:
            raise ValueError("HTTP timeout must be positive.")

        self._timeout = timeout

    def create_post(
        self,
        site_url: str,
        username: str,
        application_password: str,
        content: str,
    ) -> int:
        parsed = urlsplit(site_url)

        if (
            parsed.scheme.lower() != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("A valid HTTPS WordPress URL is required.")

        endpoint = (
            site_url.rstrip("/")
            + "/wp-json/wp/v2/posts"
        )

        credentials = f"{username}:{application_password}"
        encoded = base64.b64encode(
            credentials.encode("utf-8")
        ).decode("ascii")

        payload = json.dumps({
            "content": content,
            "status": "publish",
        }).encode("utf-8")

        request = Request(
            endpoint,
            data=payload,
            headers={
                "Authorization": f"Basic {encoded}",
                "Accept": "application/json",
                "Content-Type": "application/json; charset=utf-8",
            },
            method="POST",
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
                return response.status
        except HTTPError as error:
            return error.code
